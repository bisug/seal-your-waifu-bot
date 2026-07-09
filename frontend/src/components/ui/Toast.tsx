import { useState, createContext, useContext, useCallback, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import { cn } from '../../utils';

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
    }, type === 'error' ? 6000 : 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[300] w-full max-w-[400px] px-4 pointer-events-none flex flex-col items-center space-y-3">
        <AnimatePresence mode="popLayout">
          {toasts.map(toast => (
            <motion.div
              key={toast.id}
              layout
              initial={{ y: 20, opacity: 0, scale: 0.9 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: 10, opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
              className="w-full pointer-events-auto"
            >
              <div className="bg-brand-midnight/80 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-[0_15px_40px_rgba(0,0,0,0.4)] flex items-center gap-4">
                <div className={cn(
                  "w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border",
                  toast.type === 'success' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                  toast.type === 'error' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                  'bg-brand-accent/10 text-brand-accent border-brand-accent/20'
                )}>
                  {toast.type === 'success' ? <CheckCircle2 size={20} /> :
                   toast.type === 'error' ? <AlertCircle size={20} /> :
                   <Info size={20} />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] font-black uppercase text-neutral-500 tracking-widest mb-0.5">
                    {toast.type === 'error' ? 'System Alert' : toast.type === 'success' ? 'Operation Success' : 'Information'}
                  </p>
                  <p className="text-sm font-bold text-white leading-snug truncate uppercase">
                    {toast.message}
                  </p>
                </div>
                <button
                  onClick={() => removeToast(toast.id)}
                  className="p-1.5 rounded-lg hover:bg-white/5 text-neutral-600 transition-colors"
                >
                  <X size={16} />
                </button>
              </div>
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
