import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useRef } from 'react';
import { apiFetch, getErrorMessage } from '../api/client';

interface UseApiOptions<T> extends RequestInit {
  initialData?: T;
  manual?: boolean;
}

/**
 * Standardized API Hook — thin wrapper over @tanstack/react-query.
 * Keeps the legacy { data, loading, error, execute, setData } shape so
 * existing pages work unchanged; caching and dedup come from react-query.
 */
export const useApi = <T = any>(
  endpoint: string,
  options: UseApiOptions<T> = {},
  deps: any[] = [],
) => {
  const queryClient = useQueryClient();
  const optionsRef = useRef(options);
  optionsRef.current = options;

  const isGet = !options.method || options.method === 'GET';
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const queryKey = ['api', endpoint, options.body ?? null, ...deps];

  const query = useQuery<T>({
    queryKey,
    // biome-ignore lint/correctness/useExhaustiveDependencies: options read via ref to avoid refetch loops
    queryFn: ({ signal }) => apiFetch(endpoint, { ...optionsRef.current, signal }),
    enabled: !options.manual,
    ...(options.initialData !== undefined ? { initialData: options.initialData } : {}),
    // apiFetch already retries idempotent requests internally.
    retry: false,
  });

  const execute = useCallback(
    async (overrides: RequestInit = {}) => {
      const res = await apiFetch(endpoint, { ...optionsRef.current, ...overrides });
      if (isGet) {
        queryClient.setQueryData(queryKey, res);
      }
      return res;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [endpoint, isGet, queryClient, ...queryKey],
  );

  const setData = useCallback(
    (value: T) => queryClient.setQueryData(queryKey, value),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    // biome-ignore lint/correctness/useExhaustiveDependencies: queryKey spread is intentional
    [queryClient, ...queryKey],
  );

  return {
    data: query.data ?? null,
    loading: query.isPending || query.isFetching,
    error: query.error ? getErrorMessage(query.error) : null,
    execute,
    setData,
  };
};
