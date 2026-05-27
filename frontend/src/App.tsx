import React, { useState, useEffect, Suspense, lazy, useCallback, useRef, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { UserProvider, useUser } from './context/UserContext';
import { TabNavigation } from './components/TabNavigation';
import { IntroLoading } from './components/IntroLoading';
import { Profile } from './pages/Profile';
import { NotFound } from './pages/NotFound';
import { ToastProvider } from './components/ui/Toast';
import { CharActionModal } from './components/character/CharActionModal';
import { PetActionModal } from './components/pet/PetActionModal';
import { GachaReveal } from './components/ui/GachaReveal';

const Market = lazy(() => import('./pages/Market').then(m => ({ default: m.Market })));
const Nexus = lazy(() => import('./pages/Nexus').then(m => ({ default: m.Nexus })));
const Hatchery = lazy(() => import('./pages/Hatchery').then(m => ({ default: m.Hatchery })));

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
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
            className="px-8 py-4 bg-brand-accent text-white font-black rounded-2xl uppercase tracking-widest text-[11px] shadow-lg shadow-brand-accent/50 active:scale-95 transition-transform"
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
  const { user, loading, error, liteMode } = useUser();
  
  const getInitialTab = () => {
    const startParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param;
    if (startParam === 'shop' || startParam === 'market' || startParam === 'gallery') return 'market';
    if (startParam === 'leaderboard' || startParam === 'pass' || startParam === 'quests') return 'nexus';
    return 'profile';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab());
  const [selectedChar, setSelectedChar] = useState<any>(null);
  const [selectedPet, setSelectedPet] = useState<any>(null);
  const [revealedChar, setRevealedChar] = useState<any>(null);

  const backHandlerRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;

    try {
      if (backHandlerRef.current) {
        tg.BackButton?.offClick?.(backHandlerRef.current);
      }

      if (selectedChar || selectedPet) {
        const handler = () => {
          setSelectedChar(null);
          setSelectedPet(null);
        };
        backHandlerRef.current = handler;
        tg.BackButton?.show?.();
        tg.BackButton?.onClick?.(handler);
      } else {
        backHandlerRef.current = null;
        tg.BackButton?.hide?.();
      }

      tg.setHeaderColor?.('#0A0A0B');
      tg.setBackgroundColor?.('#0A0A0B');
      tg.expand?.();
       } catch {
      console.warn('Telegram API error (non-critical):', );
    }

    return () => {
      try {
        if (backHandlerRef.current) {
          tg?.BackButton?.offClick?.(backHandlerRef.current);
        }
         } catch {
        // ignore
      }
    };
  }, [selectedChar, selectedPet]);

  const handleNavigate = useCallback((tab: string) => {
    const tg = window.Telegram?.WebApp;
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
        <div className="absolute inset-0 bg-brand-accent/5 opacity-10 animate-pulse" />
        
        <div className="relative z-10">
          <motion.div 
            initial={liteMode ? false : { scale: 0.9, opacity: 0 }}
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
              className="w-full px-10 py-4 rounded-2xl bg-brand-accent text-brand-midnight font-black uppercase text-[10px] tracking-[0.15em] shadow-xl shadow-brand-accent/20 transition-all active:scale-95 flex items-center justify-center gap-2"
            >
              RETRY
            </button>
            <button 
              onClick={() => { 
                window.Telegram?.WebApp?.showConfirm(
                  "Are you sure you want to perform a Deep Reset? This will wipe your local session data.",
                  (confirmed) => {
                    if (confirmed) {
                      sessionStorage.clear();
                      localStorage.clear();
                      window.location.reload();
                    }
                  }
                );
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
          initial={liteMode ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={liteMode ? undefined : { opacity: 0 }}
          transition={liteMode ? undefined : { duration: 0.12, ease: [0.22, 1, 0.36, 1] }}
          className="app-scroller adaptive-px bg-mesh overflow-x-hidden"
        >
          <Suspense fallback={
            <div className="flex items-center justify-center h-full bg-brand-midnight bg-mesh">
              <Loader2 size={24} className="animate-spin text-brand-accent/20" />
            </div>
          }>
            {activeTab === 'profile' && <Profile onCharClick={setSelectedChar} />}
            {activeTab === 'market' && (
                <Market
                    onCharClick={setSelectedChar}
                    onPetClick={setSelectedPet}
                    onNavigate={handleNavigate}
                />
            )}
            {activeTab === 'nexus' && <Nexus />}
            {activeTab === 'incubation' && <Hatchery onPetClick={setSelectedPet} />}
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
            // Trigger TS re-evaluation
            onPurchaseSuccess={setRevealedChar}
          />
        )}
        {selectedPet && (
          <PetActionModal
            selectedPet={selectedPet}
            setSelectedPet={setSelectedPet}
            user={user}
          />
        )}
        {revealedChar && (
          <GachaReveal
            character={revealedChar}
            onClose={() => setRevealedChar(null)}
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
