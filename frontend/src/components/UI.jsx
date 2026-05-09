import React, { useState, createContext, useContext, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { apiFetch } from '../api';

export * from './Rarity';
export * from './Card';
export * from './Modal';
export * from './ProgressBar';

/**
 * Cinematic Skeleton Loaders
 */
export const Skeleton = ({ className }) => (
  <div className={`bg-white/[0.03] overflow-hidden relative ${className}`}>
    <div className="absolute inset-0 animate-shimmer opacity-40" />
  </div>
);

export const CardSkeleton = () => (
  <div className="rounded-[1.5rem] glass-panel border border-white/5 overflow-hidden aspect-[3/4]">
    <div className="h-full p-4 flex flex-col justify-end space-y-3">
      <Skeleton className="h-2.5 w-1/3 rounded-full" />
      <Skeleton className="h-3.5 w-2/3 rounded-full" />
    </div>
  </div>
);

/**
 * Horizontal Scroll with Fade Mask
 */
export const ScrollArea = ({ children, className = "" }) => (
  <div className={`relative ${className}`}>
    <div className="scroll-fade-mask overflow-x-auto no-scrollbar flex space-x-2 py-1">
      {children}
    </div>
  </div>
);

/**
 * Branded Toast Notification System
 */
const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[300] w-full max-w-[280px] pointer-events-none flex flex-col items-center space-y-2">
        <AnimatePresence>
          {toasts.map(toast => (
            <motion.div
              key={toast.id}
              initial={{ y: -20, opacity: 0, scale: 0.9 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: -10, opacity: 0, scale: 0.95 }}
              className="glass-panel w-full px-4 py-3 rounded-2xl border border-white/10 shadow-2xl flex items-center space-x-3 pointer-events-auto"
            >
              <div className={toast.type === 'success' ? 'text-brand-neon' : toast.type === 'error' ? 'text-red-500' : 'text-brand-accent'}>
                {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
              </div>
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-200 truncate pr-2">
                {toast.message}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => useContext(ToastContext);

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
  
  if (!shallowEqual(optionsRef.current, options)) {
    optionsRef.current = options;
  }

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
  }, deps);

  return { data, loading, error, execute, setData };
};

