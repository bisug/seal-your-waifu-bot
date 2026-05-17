import { useState, useEffect, useCallback, useRef } from 'react';
import { apiFetch } from '../api/client';

// Shallow array comparison utility
function shallowEqual(obj1, obj2) {
  if (obj1 === obj2) return true;
  const keys1 = Object.keys(obj1 || {});
  const keys2 = Object.keys(obj2 || {});
  if (keys1.length !== keys2.length) return false;
  for (let key of keys1) {
      if (obj1[key] !== obj2[key]) return false;
  }
  return true;
}

/**
 * Standardized API Hook
 */
export const useApi = (endpoint, options = {}, deps = []) => {
  const [data, setData] = useState(options.initialData || null);
  const [loading, setLoading] = useState(!options.manual);
  const [error, setError] = useState(null);

  const optionsRef = useRef(options);
  const [currentOptions, setCurrentOptions] = useState(options);

  useEffect(() => {
    if (!shallowEqual(currentOptions, options)) {
      optionsRef.current = options;
      // Use setTimeout to move the state update out of the render/effect cycle
      // to avoid cascading renders warning.
      setTimeout(() => {
        setData(options.initialData || null);
        setCurrentOptions(options);
      }, 0);
    }
  }, [options, currentOptions]);

  const execute = useCallback(async (overrides = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(endpoint, { ...optionsRef.current, ...overrides });
      setData(res);
      return res;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    if (!optionsRef.current.manual) {
      execute();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error, execute, setData };
};
