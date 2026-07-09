import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Home, Compass, ShieldAlert, Sparkles, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const NotFound = ({ onReset }: { onReset: () => void }) => {
  useEffect(() => {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('warning');
  }, []);

  return (
    <div className="min-h-[80svh] flex flex-col items-center justify-center p-8 text-center select-none relative overflow-hidden">
      <div className="tactical-grid absolute inset-0 opacity-10 pointer-events-none" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(239,68,68,0.05),transparent_70%)] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-sm flex flex-col items-center relative z-10"
      >
        <div className="relative mb-10">
            <div className="w-24 h-24 rounded-[2rem] bg-danger/10 border border-danger/20 flex items-center justify-center shadow-2xl relative z-10">
               <ShieldAlert className="text-danger" size={44} strokeWidth={2} />
            </div>
            <div className="absolute -inset-4 bg-danger/5 blur-3xl rounded-full animate-pulse" />
        </div>

        <div className="space-y-3 mb-12">
            <h1 className="text-6xl font-black text-white tracking-tighter drop-shadow-2xl">404</h1>
            <div className="flex flex-col gap-1">
                <h2 className="text-xl font-black text-white uppercase tracking-widest leading-none">Access Denied</h2>
                <p className="text-[10px] font-black text-danger uppercase tracking-[0.3em]">Protocol_Error: Page_Not_Found</p>
            </div>
            <p className="text-[13px] font-bold text-neutral-500 leading-relaxed max-w-[280px] mx-auto uppercase tracking-widest pt-4">
               The requested sector is currently offline or unauthorized. Return to the secure terminal.
            </p>
        </div>

        <div className="w-full max-w-[240px] space-y-4">
            <Button
                onClick={() => {
                    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                    onReset();
                }}
                className="w-full h-16 rounded-2xl shadow-xl active:scale-95"
            >
                <Home size={18} className="mr-3" strokeWidth={2.5} />
                <span>RESTORE_SESSION</span>
            </Button>

            <button
                onClick={() => window.history.back()}
                className="w-full flex items-center justify-center gap-2 py-4 text-[10px] font-black text-neutral-600 uppercase tracking-[0.4em] hover:text-white transition-colors"
            >
                <ArrowLeft size={12} strokeWidth={3} />
                <span>GO_BACK</span>
            </button>
        </div>
      </motion.div>

      <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex items-center gap-3 opacity-20">
         <Sparkles size={12} className="text-danger" />
         <span className="text-[8px] font-black uppercase tracking-[0.4em] text-white">System Anomaly Detected</span>
      </div>
    </div>
  );
};
