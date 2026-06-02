import { useState, useEffect, useCallback, useRef } from 'react';
import { apiFetch } from '../api/client';

const gridCache = new Map<string, { items: any[], page: number, hasMore: boolean, timestamp: number }>();
const CACHE_TTL = 1000 * 60 * 5; // 5 mins

interface InfiniteGridOptions {
  limit?: number;
  params?: Record<string, any>;
}

export const useInfiniteGrid = <T = any>(endpoint: string, options: InfiniteGridOptions = {}) => {
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [search, setSearch] = useState('');
  const [rarity, setRarity] = useState('');
  const [initialized, setInitialized] = useState(false);

  const observer = useRef<IntersectionObserver | null>(null);
  const searchAbortController = useRef<AbortController | null>(null);

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

  const fetchData = useCallback(async (isNew = false) => {
    setLoading(true);

    if (isNew) {
      if (searchAbortController.current) {
        searchAbortController.current.abort();
      }
      searchAbortController.current = new AbortController();
    }

    const currentPage = isNew ? 1 : page;
    const queryParams = new URLSearchParams({
      page: currentPage.toString(),
      limit: (options.limit || 24).toString(),
      search: search.trim(),
      rarity: rarity.trim(),
      ...options.params
    });

    const cacheKey = `${endpoint}?${search.trim()}:${rarity.trim()}`;

    // On exact first mount, try to restore from cache
    if (!initialized && isNew) {
        if (gridCache.has(cacheKey)) {
            const cached = gridCache.get(cacheKey)!;
            if (Date.now() - cached.timestamp < CACHE_TTL) {
                setItems(cached.items);
                setPage(cached.page);
                setHasMore(cached.hasMore);
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

      let newItems;
      if (isNew) {
        newItems = data.items;
      } else {
        newItems = [...items, ...data.items];
      }

      setItems(newItems);
      const newHasMore = data.items.length === (options.limit || 24);
      setHasMore(newHasMore);

      // Save to cache
      gridCache.set(cacheKey, {
          items: newItems,
          page: currentPage,
          hasMore: newHasMore,
          timestamp: Date.now()
      });

    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.error(`Fetch error for ${endpoint}:`, err);
    } finally {
      setLoading(false);
    }
  }, [endpoint, page, search, rarity, options.limit, options.params, items, initialized]);

  // Initial fetch and search/rarity debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      fetchData(true);
    }, 400);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, rarity]);

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
      fetchData(true);
  }, [fetchData]);

  return {
    items,
    loading,
    hasMore,
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
