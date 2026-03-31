const API_BASE = '/api/v1_7b82';
// FIX: Read Telegram SDK at CALL TIME, not at module load time.
// On mobile, the SDK may not be injected yet when the JS module first evaluates.
const getTg = () => window.Telegram?.WebApp;

let sessionToken = localStorage.getItem('auth_token');

export const getSessionToken = () => sessionToken;

export const setSessionToken = (token) => {
  sessionToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
};

/**
 * Universal fetch wrapper for the Seal-bot FastAPI backend.
 * Handles authentication headers and standard error reporting.
 */
let isRefreshing = false;

export async function apiFetch(endpoint, options = {}, retries = 2) {
  const url = `${API_BASE}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (sessionToken) {
    headers['Authorization'] = `Bearer ${sessionToken}`;
  }

  try {
    const response = await fetch(url, { ...options, headers });
    
    // Automatic Handshake Recovery: If 401, session might be dead. Try to re-init once.
    if (response.status === 401 && !isRefreshing) {
      isRefreshing = true;
      try {
        const newToken = await secureInit();
        if (newToken) {
          isRefreshing = false;
          return apiFetch(endpoint, options, retries); // Retry with new token
        }
      } catch (err) {
        console.error("Auth Recovery Failed:", err);
      }
      isRefreshing = false;
      setSessionToken(null);
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
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
export async function secureInit(avatarUrl = null) {
  const tg = getTg(); // Read at call time, not module load time
  const initData = tg?.initData;
  const storedToken = localStorage.getItem('auth_token');

  const payload = {
    initData: initData || null,
    token: storedToken || null,
    avatar: avatarUrl,
  };

  try {
    const response = await fetch(`${API_BASE}/secure_init`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) throw new Error('Init failed');

    const data = await response.json();
    if (data.token) {
      setSessionToken(data.token);
      return data.token;
    }
    return null;
  } catch (error) {
    console.error('Secure Init Error:', error);
    return null;
  }
}
