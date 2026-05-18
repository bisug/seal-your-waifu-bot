import React, { useState, createContext, useContext, useCallback, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface ToastContextType {
  addToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = crypto.randomUUID();
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
              className="glass-panel w-full px-4 py-3 rounded-2xl border border-white/10 shadow-lg flex items-center space-x-3 pointer-events-auto"
            >
            <div className={toast.type === 'success' ? 'text-brand-accent' : toast.type === 'error' ? 'text-red-500' : 'text-brand-accent'}>
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

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
