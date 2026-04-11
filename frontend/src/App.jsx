import React, { useState, useEffect, Suspense, lazy, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { UserProvider, useUser } from './context/UserContext';
import { TabNavigation } from './components/TabNavigation';
import { IntroLoading } from './components/IntroLoading';
import { Profile } from './pages/Profile';
import { NotFound } from './pages/NotFound';
import { Modal, ToastProvider, useToast } from './components/UI';
import { Zap } from 'lucide-react';
import { apiFetch } from './api';
import { formatNumber } from './utils';
import { CharActionModal } from './components/CharActionModal';

// Lazy load pages for extreme performance
const Market = lazy(() => import('./pages/Market').then(m => ({ default: m.Market })));
const Nexus = lazy(() => import('./pages/Nexus').then(m => ({ default: m.Nexus })));
const Hatchery = lazy(() => import('./pages/Hatchery').then(m => ({ default: m.Hatchery })));

// Cinematic Error Boundary for high-deployment stability
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Master Audit - UI Crash Detected:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-12 text-center min-h-svh bg-brand-midnight">
          <div className="mb-8 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl max-w-sm">
             <h2 className="text-red-500 font-black mb-2 uppercase tracking-[0.3em]">System Error</h2>
             <p className="text-[10px] text-red-400 font-mono break-all">{this.state.error?.toString() || 'Unknown Error'}</p>
          </div>
          
          <p className="text-slate-500 text-[10px] mb-8 uppercase tracking-widest">A module failure occurred. Re-establish connection?</p>
          
          <button 
            onClick={() => window.location.reload()}
            className="px-8 py-4 bg-brand-accent text-white font-black rounded-2xl uppercase tracking-widest text-[11px] neon-shadow shadow-brand-accent/50 active:scale-95 transition-transform"
          >
            RECONNECT
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}


const AppContent = () => {
  const { user, loading, error } = useUser();
  const { addToast } = useToast();
  
  // Intelligence: Read the start_param for deep-linking (e.g., Shop/Gallery/Profile)
  const getInitialTab = () => {
    const startParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param;
    if (startParam === 'shop' || startParam === 'market' || startParam === 'gallery') return 'market';
    if (startParam === 'leaderboard' || startParam === 'pass' || startParam === 'quests') return 'nexus';
    return 'profile';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab());
  const [selectedChar, setSelectedChar] = useState(null);
  const [purchaseStage, setPurchaseStage] = useState('idle'); // 'idle', 'confirm', 'buying'

  // FIX: Stable ref for the BackButton handler to prevent accumulating listeners.
  // Telegram's BackButton.onClick is additive (like addEventListener), so we must
  // offClick the previous handler before registering a new one each render cycle.
  const backHandlerRef = useRef(null);

  // Reset stage when modal closes or changes
  useEffect(() => {
    if (!selectedChar) setPurchaseStage('idle');
  }, [selectedChar]);

  // Native Telegram Integration: Back Button & Haptics
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;

    try {
      // FIX: Always remove the previous handler before adding a new one.
      // BackButton.onClick is additive — not calling offClick first causes
      // the handler to fire N times (once per render that registered it).
      if (backHandlerRef.current) {
        tg.BackButton?.offClick?.(backHandlerRef.current);
      }

      if (selectedChar) {
        const handler = () => setSelectedChar(null);
        backHandlerRef.current = handler;
        tg.BackButton?.show?.();
        tg.BackButton?.onClick?.(handler);
      } else {
        backHandlerRef.current = null;
        tg.BackButton?.hide?.();
      }

      // Theme Sync: Only call if method exists (not all Telegram versions)
      tg.setHeaderColor?.('#0A0A0B');
      tg.setBackgroundColor?.('#0A0A0B');
      tg.expand?.();
    } catch (e) {
      // Silently ignore Telegram API errors on older clients
      console.warn('Telegram API error (non-critical):', e.message);
    }

    return () => {
      try {
        if (backHandlerRef.current) {
          tg?.BackButton?.offClick?.(backHandlerRef.current);
        }
      } catch (e) {
        // ignore
      }
    };
  }, [selectedChar]);

  const handleNavigate = useCallback((tab) => {
    const tg = window.Telegram?.WebApp;
    // Context-Aware Haptics: Profile & Shop get more 'Weight'
    if (tab === 'profile' || tab === 'market') {
      tg?.HapticFeedback?.impactOccurred('medium');
    } else {
      tg?.HapticFeedback?.impactOccurred('light');
    }
    setActiveTab(tab);
  }, []);

  if (loading) return <IntroLoading />;

  if (error || (!loading && !user)) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-10 text-center min-h-svh bg-brand-midnight relative overflow-hidden bg-mesh">
        {/* Cinematic Glitch Background for Error */}
        <div className="absolute inset-0 bg-brand-accent/5 opacity-10 animate-pulse" />
        
        <div className="relative z-10">
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="mb-8"
          >
            <div className="w-20 h-20 mx-auto rounded-3xl border border-brand-accent/30 flex items-center justify-center bg-brand-accent/5">
              <span className="text-4xl">📡</span>
            </div>
          </motion.div>
          
          <h2 className="text-brand-accent font-black mb-2 uppercase tracking-[0.3em] text-xl">Connection Lost</h2>
          <p className="text-slate-500 text-[10px] mb-10 leading-relaxed uppercase tracking-widest max-w-[200px] mx-auto">
            {error || "Authentication timed out. Please restart the bot."}
          </p>
          
          <div className="space-y-4">
            <button 
              onClick={() => window.location.reload()}
              className="w-full px-10 py-5 rounded-2xl bg-brand-accent text-brand-midnight font-black uppercase text-[10px] tracking-[0.2em] shadow-xl shadow-brand-accent/20 transition-all active:scale-95 flex items-center justify-center gap-3"
            >
              RETRY
            </button>
            <button 
              onClick={() => { 
                if (window.confirm("Are you sure you want to perform a Deep Reset? This will wipe your local session data.")) {
                  // FIX: Auth token lives in sessionStorage, not localStorage.
                  // Clear both so the reset actually removes the stale session.
                  sessionStorage.clear();
                  localStorage.clear(); 
                  window.location.reload(); 
                }
              }}
              className="w-full py-4 text-slate-600 text-[8px] font-bold uppercase tracking-[0.2em] hover:text-slate-400 transition-colors"
            >
              Deep Reset (Recovery Mode)
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden bg-brand-midnight">
      <AnimatePresence mode="wait">
        <motion.main
          key={activeTab}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15, ease: 'easeOut' }}
          className="app-scroller adaptive-px bg-mesh overflow-x-hidden"
        >
          <Suspense fallback={
            <div className="flex items-center justify-center h-full bg-brand-midnight bg-mesh">
              <Loader2 size={24} className="animate-spin text-brand-neon/20" />
            </div>
          }>
            {activeTab === 'profile' && <Profile onCharClick={setSelectedChar} />}
            {activeTab === 'market' && <Market onCharClick={setSelectedChar} />}
            {activeTab === 'nexus' && <Nexus />}
            {activeTab === 'incubation' && <Hatchery />}
            {!['profile', 'market', 'nexus', 'incubation'].includes(activeTab) && (
              <NotFound onReset={() => setActiveTab('profile')} />
            )}
          </Suspense>
        </motion.main>
      </AnimatePresence>

      <AnimatePresence>
        {selectedChar && (
          <CharActionModal
            selectedChar={selectedChar}
            setSelectedChar={setSelectedChar}
            activeTab={activeTab}
            user={user}
          />
        )}
      </AnimatePresence>

      <TabNavigation activeTab={activeTab} onNavigate={handleNavigate} />
    </div>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <UserProvider>
          <AppContent />
        </UserProvider>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
