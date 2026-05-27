const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api/${import.meta.env.VITE_API_PREFIX ?? 'v1_7b82'}`
  : `/api/${import.meta.env.VITE_API_PREFIX ?? 'v1_7b82'}`;
// FIX: Read Telegram SDK at CALL TIME, not at module load time.
// On mobile, the SDK may not be injected yet when the JS module first evaluates.
const getTg = () => window.Telegram?.WebApp;

// FIX: Use sessionStorage instead of localStorage.
// Telegram re-provides initData on every app open, so persistence across sessions
// is unnecessary. sessionStorage limits the exposure window significantly.
let sessionToken = sessionStorage.getItem('auth_token');

export const setSessionToken = (token: string | null) => {
  sessionToken = token;
  if (token) {
    sessionStorage.setItem('auth_token', token);
  } else {
    sessionStorage.removeItem('auth_token');
  }
};

/**
 * Universal fetch wrapper for the Seal-bot FastAPI backend.
 * Handles authentication headers and standard error reporting.
 */

interface RefreshSubscriber {
  resolve: (value: any) => void;
  reject: (reason?: any) => void;
  endpoint: string;
  options: RequestInit;
  retries: number;
}

// FIX: Replace boolean isRefreshing with a proper refresh queue.
// When a 401 is received while a refresh is already in progress,
// queue the caller's Promise so it retries after the new token is ready,
// instead of silently failing.
let isRefreshing = false;
let refreshSubscribers: RefreshSubscriber[] = []; // Array of { resolve, reject, endpoint, options, retries }

function subscribeToRefresh(endpoint: string, options: RequestInit, retries: number) {
  return new Promise((resolve, reject) => {
    refreshSubscribers.push({ resolve, reject, endpoint, options, retries });
  });
}

function flushRefreshSubscribers() {
  refreshSubscribers.forEach(({ resolve, endpoint, options, retries }) => {
    resolve(apiFetch(endpoint, options, retries));
  });
  refreshSubscribers = [];
}

function rejectRefreshSubscribers(err: Error) {
  refreshSubscribers.forEach(({ reject }) => reject(err));
  refreshSubscribers = [];
}

export async function apiFetch(endpoint: string, options: RequestInit = {}, retries = 2): Promise<any> {
  const url = `${API_BASE}${endpoint}`;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (sessionToken) {
    headers['Authorization'] = `Bearer ${sessionToken}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 12000);

  if (options.signal) {
    options.signal.addEventListener('abort', () => {
      controller.abort();
    });
  }

  try {
    const response = await fetch(url, { ...options, headers, signal: controller.signal });
    clearTimeout(timeoutId);
    
    // Automatic Handshake Recovery: If 401, re-init session once.
    // All concurrent requests that also 401 are queued and retried after recovery.
    if (response.status === 401) {
      if (isRefreshing) {
        // Another request is already refreshing — queue this one
        return subscribeToRefresh(endpoint, options, retries);
      }

      isRefreshing = true;
      try {
        const newToken = await secureInit();
        if (newToken) {
          isRefreshing = false;
          flushRefreshSubscribers();
          return apiFetch(endpoint, options, retries);
        }
        // Re-auth failed — reject all queued requests
        setSessionToken(null);
        const authErr = new Error('Session expired. Please reopen the app.');
        rejectRefreshSubscribers(authErr);
        isRefreshing = false;
        throw authErr;
      } catch (err: any) {
        isRefreshing = false;
        rejectRefreshSubscribers(err);
        console.error(`[API ERROR] ${options.method || 'GET'} ${endpoint}:`, err);
        throw err;
      }
    }

    if (!response.ok) {
      const contentType = response.headers.get("content-type");
      const errorData = contentType && contentType.includes("application/json") 
        ? await response.json().catch(() => ({})) 
        : { detail: await response.text() };
      throw new Error(errorData.detail || `API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (timeoutId) clearTimeout(timeoutId);
    if (retries > 0 && (!options.method || options.method === 'GET')) {
      console.warn(`Retrying [${endpoint}]... (${retries} left)`);
      return apiFetch(endpoint, options, retries - 1);
    }
    console.error(`Fetch error [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * Perform initial handshake with the backend using Telegram initData.
 */
export async function secureInit(avatarUrl: string | null = null): Promise<string | null> {
  const tg = getTg(); // Read at call time, not module load time
  const initData = tg?.initData;
  // Check sessionStorage for an existing token to avoid redundant re-auths
  const storedToken = sessionStorage.getItem('auth_token');

  const payload = {
    initData: initData || null,
    token: storedToken || null,
    avatar: avatarUrl,
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 12000);

  try {
    const response = await fetch(`${API_BASE}/secure_init`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);

    if (!response.ok) throw new Error('Init failed');

    const data = await response.json();
    if (data.token) {
      setSessionToken(data.token);
      return data.token;
    }
    return null;
  } catch (error) {
    if (timeoutId) clearTimeout(timeoutId);
    console.error('Secure Init Error:', error);
    return null;
  }
}
