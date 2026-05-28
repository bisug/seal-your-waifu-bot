import React, { useState, useEffect, Suspense, lazy, useCallback, useRef, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { SpeedInsights } from '@vercel/speed-insights/react';
import { UserProvider, useUser } from './context/UserContext';
import { Header } from './components/Header';
import { NavigationDrawer } from './components/NavigationDrawer';
import { IntroLoading } from './components/IntroLoading';
import { Profile } from './pages/Profile';
import { NotFound } from './pages/NotFound';
import { ToastProvider } from './components/ui/Toast';
import { CharActionModal } from './components/character/CharActionModal';
import { PetActionModal } from './components/pet/PetActionModal';
import { GachaReveal } from './components/ui/GachaReveal';

// Lazy load all pages
const Shop = lazy(() => import('./pages/Shop').then(m => ({ default: m.Shop })));
const Gallery = lazy(() => import('./pages/Gallery').then(m => ({ default: m.Gallery })));
const PetShop = lazy(() => import('./pages/PetShop').then(m => ({ default: m.PetShop })));
const Hatchery = lazy(() => import('./pages/Hatchery').then(m => ({ default: m.Hatchery })));
const Quests = lazy(() => import('./pages/Quests').then(m => ({ default: m.Quests })));
const Pass = lazy(() => import('./pages/Pass').then(m => ({ default: m.Pass })));
const Leaderboard = lazy(() => import('./pages/Leaderboard').then(m => ({ default: m.Leaderboard })));
const Referrals = lazy(() => import('./pages/Referrals').then(m => ({ default: m.Referrals })));
const Achievements = lazy(() => import('./pages/Achievements').then(m => ({ default: m.Achievements })));
const MyPets = lazy(() => import('./pages/MyPets').then(m => ({ default: m.MyPets })));

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
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center min-h-svh bg-zinc-950 select-none">
          <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center mb-8">
             <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          </div>
          
          <h2 className="text-white font-bold mb-4 uppercase tracking-[0.2em] text-sm">System Crash</h2>
          <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-widest leading-relaxed mb-10 max-w-[240px]">
            The runtime environment encountered an unrecoverable exception.
          </p>

          <button 
            onClick={() => window.location.reload()}
            className="w-full max-w-[200px] py-4 bg-white text-zinc-950 font-bold rounded-xl uppercase tracking-widest text-[10px] active:scale-[0.98] transition-transform"
          >
            Re-initialize
          </button>

          {this.state.error && (
            <div className="mt-12 p-3 bg-zinc-900/50 border border-white/5 rounded-lg max-w-xs overflow-hidden">
               <p className="text-[8px] text-zinc-600 font-mono break-all line-clamp-2 uppercase">
                  Log: {this.state.error.toString()}
               </p>
            </div>
          )}
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
    if (startParam === 'shop') return 'shop';
    if (startParam === 'market') return 'shop';
    if (startParam === 'gallery') return 'gallery';
    if (startParam === 'leaderboard') return 'leaderboard';
    if (startParam === 'pass') return 'pass';
    if (startParam === 'quests') return 'quests';
    return 'profile';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab());
  const [isMenuOpen, setIsMenuOpen] = useState(false);
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

      if (selectedChar || selectedPet || isMenuOpen) {
        const handler = () => {
          setSelectedChar(null);
          setSelectedPet(null);
          setIsMenuOpen(false);
        };
        backHandlerRef.current = handler;
        tg.BackButton?.show?.();
        tg.BackButton?.onClick?.(handler);
      } else {
        backHandlerRef.current = null;
        tg.BackButton?.hide?.();
      }

      tg.setHeaderColor?.('#09090b');
      tg.setBackgroundColor?.('#09090b');
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
  }, [selectedChar, selectedPet, isMenuOpen]);

  const handleNavigate = useCallback((tab: string) => {
    const tg = window.Telegram?.WebApp;
    tg?.HapticFeedback?.impactOccurred('light');
    setActiveTab(tab);
  }, []);

  if (loading) return <IntroLoading />;

  if (error || (!loading && !user)) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-8 text-center min-h-svh bg-zinc-950 relative overflow-hidden select-none">
        <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center mb-8">
           <div className="w-2 h-2 rounded-full bg-zinc-700 animate-pulse" />
        </div>

        <h2 className="text-white font-bold mb-4 uppercase tracking-[0.2em] text-sm">Link Severed</h2>
        <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-widest leading-relaxed mb-10 max-w-[240px]">
          {error || "Neural handshake failed. Please re-authenticate via the main console."}
        </p>

        <div className="w-full max-w-[240px] space-y-3">
          <button
            onClick={() => window.location.reload()}
            className="w-full py-4 rounded-xl bg-white text-zinc-950 font-bold uppercase text-[10px] tracking-widest transition-transform active:scale-[0.98]"
          >
            Retry Handshake
          </button>
          <button
            onClick={() => {
              window.Telegram?.WebApp?.showConfirm(
                "Perform deep system reset?",
                (confirmed) => {
                  if (confirmed) {
                    sessionStorage.clear();
                    localStorage.clear();
                    window.location.reload();
                  }
                }
              );
            }}
            className="w-full py-3 text-zinc-700 text-[9px] font-bold uppercase tracking-[0.2em] hover:text-zinc-500 transition-colors"
          >
            Deep Reset
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden bg-brand-midnight">
      <Header onMenuClick={() => setIsMenuOpen(true)} />

      <main className="app-scroller adaptive-px overflow-x-hidden">
        <Suspense fallback={
          <div className="flex items-center justify-center h-full bg-brand-midnight">
            <Loader2 size={24} className="animate-spin text-brand-accent/20" />
          </div>
        }>
          {activeTab === 'profile' && <Profile onCharClick={setSelectedChar} />}
          {activeTab === 'incubation' && <Hatchery onPetClick={setSelectedPet} />}
          {activeTab === 'shop' && <Shop onCharClick={setSelectedChar} />}
          {activeTab === 'gallery' && <Gallery onCharClick={setSelectedChar} />}
          {activeTab === 'pets' && <PetShop onPetClick={setSelectedPet} />}
          {activeTab === 'referrals' && <Referrals />}
          {activeTab === 'quests' && <Quests />}
          {activeTab === 'pass' && <Pass />}
          {activeTab === 'leaderboard' && <Leaderboard />}
          {activeTab === 'achievements' && <Achievements />}
          {activeTab === 'mypets' && <MyPets onPetClick={setSelectedPet} />}

          {!['profile', 'incubation', 'shop', 'gallery', 'pets', 'referrals', 'quests', 'pass', 'leaderboard', 'achievements', 'mypets'].includes(activeTab) && (
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

      <NavigationDrawer
        isOpen={isMenuOpen}
        onClose={() => setIsMenuOpen(false)}
        activeTab={activeTab}
        onNavigate={handleNavigate}
      />
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
      <SpeedInsights />
    </ErrorBoundary>
  );
}

export default App;
