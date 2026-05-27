import React, { useState, useEffect, Suspense, lazy, useCallback, useRef, ReactNode } from 'react';
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
    console.error("System Audit - UI Crash Detected:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center min-h-svh bg-brand-midnight">
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl max-w-sm">
             <h2 className="text-red-500 font-bold mb-2 uppercase tracking-wider text-sm">System Error</h2>
             <p className="text-[10px] text-red-400 font-mono break-all">{this.state.error?.toString() || 'Unknown Error'}</p>
          </div>
          
          <button 
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-brand-accent text-white font-bold rounded-xl uppercase tracking-wider text-[11px] active:scale-95 transition-transform"
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
      console.warn('Telegram API error (non-critical)');
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
    tg?.HapticFeedback?.impactOccurred('light');
    setActiveTab(tab);
  }, []);

  if (loading) return <IntroLoading />;

  if (error || (!loading && !user)) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-10 text-center min-h-svh bg-brand-midnight relative overflow-hidden">
        <div className="relative z-10">
          <div className="mb-6">
            <div className="w-16 h-16 mx-auto rounded-2xl border border-brand-accent/20 flex items-center justify-center bg-brand-accent/5">
              <span className="text-3xl">📡</span>
            </div>
          </div>
          
          <h2 className="text-brand-accent font-bold mb-2 uppercase tracking-wider text-lg">Connection Lost</h2>
          <p className="text-slate-500 text-[10px] mb-8 leading-relaxed uppercase tracking-widest max-w-[200px] mx-auto">
            {error || "Authentication timed out. Please restart the bot."}
          </p>
          
          <div className="space-y-3">
            <button 
              onClick={() => window.location.reload()}
              className="w-full px-8 py-3.5 rounded-xl bg-brand-accent text-white font-bold uppercase text-[10px] tracking-wider transition-all active:scale-95 flex items-center justify-center gap-2"
            >
              RETRY
            </button>
            <button 
              onClick={() => { 
                window.Telegram?.WebApp?.showConfirm(
                  "Deep Reset will wipe your local session data. Continue?",
                  (confirmed) => {
                    if (confirmed) {
                      sessionStorage.clear();
                      localStorage.clear();
                      window.location.reload();
                    }
                  }
                );
              }}
              className="w-full py-3 text-slate-600 text-[8px] font-bold uppercase tracking-wider hover:text-slate-400 transition-colors"
            >
              Deep Reset
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden bg-brand-midnight">
      <main className="app-scroller adaptive-px overflow-x-hidden">
        <Suspense fallback={
          <div className="flex items-center justify-center h-full bg-brand-midnight">
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
      </main>

      {selectedChar && (
        <CharActionModal
          selectedChar={selectedChar}
          setSelectedChar={setSelectedChar}
          activeTab={activeTab}
          user={user}
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
