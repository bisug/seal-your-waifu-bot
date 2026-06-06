import { useState, useEffect, useCallback, useRef } from 'react';
import { ApiError, apiFetch, getErrorMessage } from '../api/client';

const gridCache = new Map<string, { items: any[], page: number, hasMore: boolean, timestamp: number }>();
const CACHE_TTL = 1000 * 60 * 5; // 5 mins
const MAX_CACHE_ENTRIES = 24;

const writeGridCache = (
  key: string,
  value: { items: any[], page: number, hasMore: boolean, timestamp: number },
) => {
  if (gridCache.has(key)) gridCache.delete(key);
  gridCache.set(key, value);
  while (gridCache.size > MAX_CACHE_ENTRIES) {
    const oldest = gridCache.keys().next().value;
    if (!oldest) break;
    gridCache.delete(oldest);
  }
};

interface InfiniteGridOptions {
  limit?: number;
  params?: Record<string, any>;
}

export const useInfiniteGrid = <T = any>(endpoint: string, options: InfiniteGridOptions = {}) => {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [rarity, setRarity] = useState('');
  const [initialized, setInitialized] = useState(false);

  const observer = useRef<IntersectionObserver | null>(null);
  const searchAbortController = useRef<AbortController | null>(null);
  const requestSeq = useRef(0);
  const paramsKey = JSON.stringify(options.params || {});

  const lastElementRef = useCallback((node: HTMLElement | null) => {
    if (loading) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore && !loading) {
        setPage(prev => prev + 1);
      }
    });
    if (node) observer.current.observe(node);
  }, [loading, hasMore]);

  const fetchData = useCallback(async (isNew = false, force = false) => {
    const requestId = ++requestSeq.current;
    setLoading(true);
    setError(null);

    if (isNew) {
      if (searchAbortController.current) {
        searchAbortController.current.abort();
      }
      searchAbortController.current = new AbortController();
    }

    const currentPage = isNew ? 1 : page;
    const optionParams = JSON.parse(paramsKey) as Record<string, any>;
    const queryParams = new URLSearchParams({
      page: currentPage.toString(),
      limit: (options.limit || 24).toString(),
      search: search.trim(),
      rarity: rarity.trim(),
      ...optionParams
    });

    const cacheKey = `${endpoint}?${search.trim()}:${rarity.trim()}:${options.limit || 24}:${paramsKey}`;

    if (isNew && !force) {
        if (gridCache.has(cacheKey)) {
            const cached = gridCache.get(cacheKey)!;
            if (Date.now() - cached.timestamp < CACHE_TTL) {
                if (requestId !== requestSeq.current) return;
                setItems(cached.items);
                setPage(cached.page);
                setHasMore(cached.hasMore);
                setError(null);
                setLoading(false);
                setInitialized(true);
                return;
            }
        }
    }
    setInitialized(true);

    try {
      const data = await apiFetch(
        `${endpoint}?${queryParams.toString()}`,
        { signal: searchAbortController.current?.signal }
      );

      if (requestId !== requestSeq.current) return;

      let newItems;
      if (isNew) {
        newItems = data.items;
      } else {
        newItems = [...items, ...data.items];
      }

      setItems(newItems);
      setError(null);
      const total = typeof data.total === 'number' ? data.total : null;
      const newHasMore = total === null
        ? data.items.length === (options.limit || 24)
        : currentPage * (options.limit || 24) < total;
      setHasMore(newHasMore);

      // Save to cache
      writeGridCache(cacheKey, {
          items: newItems,
          page: currentPage,
          hasMore: newHasMore,
          timestamp: Date.now()
      });

    } catch (err: any) {
      if (err instanceof ApiError && err.code === 'cancelled') return;
      if (requestId !== requestSeq.current) return;
      const message = getErrorMessage(err);
      setError(message);
      console.error(`Fetch error for ${endpoint}: ${message}`, err);
    } finally {
      if (requestId === requestSeq.current) {
        setLoading(false);
      }
    }
  }, [endpoint, page, search, rarity, options.limit, paramsKey, items, initialized]);

  // Initial fetch and search/rarity debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchData(true);
    }, 400);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, rarity, paramsKey]);

  // Infinite scroll trigger
  useEffect(() => {
    let mounted = true;
    if (page > 1 && mounted) {
      Promise.resolve().then(() => {
        if (mounted) fetchData(false);
      });
    }
    return () => { mounted = false; };
  }, [page, fetchData]);

  const refresh = useCallback(() => {
      setPage(1);
      fetchData(true, true);
  }, [fetchData]);

  return {
    items,
    loading,
    hasMore,
    error,
    page,
    setPage,
    search,
    setSearch,
    rarity,
    setRarity,
    lastElementRef,
    refresh
  };
};
