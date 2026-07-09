import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiFetch, getErrorMessage } from '../api/client';

const apiCache = new Map<string, { data: any, timestamp: number }>();
const CACHE_TTL = 1000 * 60 * 5; // 5 minutes

// Shallow array comparison utility
function shallowEqual(obj1: any, obj2: any) {
  if (obj1 === obj2) return true;
  const keys1 = Object.keys(obj1 || {});
  const keys2 = Object.keys(obj2 || {});
  if (keys1.length !== keys2.length) return false;
  for (const key of keys1) {
      if (obj1[key] !== obj2[key]) return false;
  }
  return true;
}

interface UseApiOptions<T> extends RequestInit {
  initialData?: T;
  manual?: boolean;
}

/**
 * Standardized API Hook
 */
export const useApi = <T = any>(endpoint: string, options: UseApiOptions<T> = {}, deps: any[] = []) => {
  const queryClient = useQueryClient();
  const isManual = options.manual;
  const isGet = !options.method || options.method === 'GET';

  const queryKey = [endpoint, options.body, ...deps];

  const { data, isLoading, error, refetch } = useQuery<T, Error>({
    queryKey,
    queryFn: async () => {
      const res = await apiFetch(endpoint, options);
      return res;
    },
    enabled: !isManual && isGet,
    initialData: options.initialData,
  });

  const [manualData, setManualData] = useState<T | null>(options.initialData || null);
  const [manualLoading, setManualLoading] = useState(false);
  const [manualError, setManualError] = useState<string | null>(null);

  const execute = useCallback(async (overrides: RequestInit = {}) => {
    if (isGet && !isManual) {
      const result = await refetch();
      return result.data;
    }

    setManualLoading(true);
    setManualError(null);
    try {
      const res = await apiFetch(endpoint, { ...options, ...overrides });
      setManualData(res);
      // Invalidate related queries if it was a mutation
      if (!isGet) {
        queryClient.invalidateQueries({ queryKey: [endpoint] });
      }
      return res;
    } catch (err: any) {
      const msg = getErrorMessage(err);
      setManualError(msg);
      throw err;
    } finally {
      setManualLoading(false);
    }
  }, [endpoint, isGet, isManual, options, queryClient, refetch]);

  return {
    data: isGet && !isManual ? data : manualData,
    loading: isGet && !isManual ? isLoading : manualLoading,
    error: isGet && !isManual ? (error ? error.message : null) : manualError,
    execute,
    setData: setManualData
  };
};
