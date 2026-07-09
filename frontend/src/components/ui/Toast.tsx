import { useState, createContext, useContext, useCallback, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X, ShieldCheck, Terminal, Zap } from 'lucide-react';
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
    }, type === 'error' ? 7000 : 5000);
  }, []);

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[300] w-full max-w-[440px] px-6 pointer-events-none flex flex-col items-center space-y-3">
        <AnimatePresence mode="popLayout">
          {toasts.map(toast => (
            <motion.div
              key={toast.id}
              layout
              initial={{ y: -30, opacity: 0, scale: 0.9 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: -20, opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
              className="w-full pointer-events-auto"
            >
              <div className="bg-brand-midnight/90 backdrop-blur-2xl border border-white/[0.08] rounded-[24px] p-5 shadow-[0_30px_70px_rgba(0,0,0,0.7)] flex items-center gap-5 group relative overflow-hidden">
                <div className="absolute inset-0 bg-scanline opacity-[0.02] pointer-events-none" />

                <div className={cn(
                  "w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 border shadow-inner transition-transform duration-500 group-hover:scale-110",
                  toast.type === 'success' ? 'bg-success/10 text-success border-success/20 shadow-success/10' :
                  toast.type === 'error' ? 'bg-danger/10 text-danger border-danger/20 shadow-danger/10' :
                  'bg-brand-accent/10 text-brand-accent border-brand-accent/20 shadow-brand-accent/10'
                )}>
                  {toast.type === 'success' ? <CheckCircle2 size={24} strokeWidth={2.5} /> :
                   toast.type === 'error' ? <AlertCircle size={24} strokeWidth={2.5} /> :
                   <Terminal size={24} strokeWidth={2.5} />}
                </div>

                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2">
                     <span className={cn(
                       "text-[9px] font-black uppercase tracking-[0.3em] leading-none",
                       toast.type === 'error' ? 'text-danger' : toast.type === 'success' ? 'text-success' : 'text-brand-accent'
                     )}>
                       {toast.type === 'error' ? 'PROTOCOL_ALERT' : toast.type === 'success' ? 'OP_SUCCESS' : 'SYSTEM_INFO'}
                     </span>
                     <div className="h-1 w-1 rounded-full bg-white/10" />
                     <span className="text-[8px] font-black text-neutral-700 uppercase tracking-widest font-mono">CODE_{toast.id.slice(0, 4).toUpperCase()}</span>
                  </div>
                  <p className="text-[13px] font-bold text-white leading-tight truncate uppercase tracking-widest">
                    {toast.message}
                  </p>
                </div>

                <button
                  onClick={() => {
                      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
                      removeToast(toast.id);
                  }}
                  className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-white/5 text-neutral-700 hover:text-white transition-all active:scale-90"
                >
                  <X size={18} strokeWidth={3} />
                </button>

                {/* Auto-dismiss progress bar */}
                <div className="absolute bottom-0 left-0 h-1 bg-white/[0.03] w-full overflow-hidden">
                   <motion.div
                     initial={{ width: '100%' }}
                     animate={{ width: 0 }}
                     transition={{ duration: toast.type === 'error' ? 7 : 5, ease: 'linear' }}
                     className={cn(
                       "h-full",
                       toast.type === 'success' ? 'bg-success/40' :
                       toast.type === 'error' ? 'bg-danger/40' :
                       'bg-brand-accent/40'
                     )}
                   />
                </div>
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
