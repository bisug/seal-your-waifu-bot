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
const Exchange = lazy(() => import('./pages/Exchange').then(m => ({ default: m.Exchange })));

const VALID_TABS = ['profile', 'incubation', 'shop', 'exchange', 'gallery', 'pets', 'referrals', 'quests', 'pass', 'leaderboard', 'achievements', 'mypets'];
const TAB_ALIASES: Record<string, string> = {
  profile: 'profile',
  home: 'profile',
  me: 'profile',
  harem: 'profile',
  collection: 'profile',
  inventory: 'profile',
  eggs: 'incubation',
  egg: 'incubation',
  hatch: 'incubation',
  hatching: 'incubation',
  incubation: 'incubation',
  incubator: 'incubation',
  shop: 'shop',
  market: 'shop',
  cshop: 'shop',
  store: 'shop',
  daily_shop: 'shop',
  dailyshop: 'shop',
  exchange: 'exchange',
  currency: 'exchange',
  currencies: 'exchange',
  conversion: 'exchange',
  convert: 'exchange',
  zenith: 'exchange',
  shard: 'exchange',
  shards: 'exchange',
  gallery: 'gallery',
  catalog: 'gallery',
  characters: 'gallery',
  pets: 'pets',
  petshop: 'pets',
  pet_store: 'pets',
  companionshop: 'pets',
  mypets: 'mypets',
  mypet: 'mypets',
  pet: 'mypets',
  companions: 'mypets',
  referrals: 'referrals',
  referral: 'referrals',
  invite: 'referrals',
  quests: 'quests',
  quest: 'quests',
  tasks: 'quests',
  task: 'quests',
  missions: 'quests',
  pass: 'pass',
  battlepass: 'pass',
  battle_pass: 'pass',
  bp: 'pass',
  leaderboard: 'leaderboard',
  leaderboards: 'leaderboard',
  top: 'leaderboard',
  ranks: 'leaderboard',
  achievements: 'achievements',
  achievement: 'achievements',
  badges: 'achievements',
};

interface RouteTarget {
  tab: string;
  alias: string;
}

const normalizeRouteToken = (value?: string | null) => {
  if (!value) return null;

  let token = value.trim();
  try {
    token = decodeURIComponent(token);
  } catch {
    // Keep the raw token if Telegram/browser encoding is malformed.
  }

  token = token
    .toLowerCase()
    .replace(/^https?:\/\/[^/]+/i, '')
    .replace(/^#/, '')
    .replace(/^[?/]+/, '')
    .split(/[?&#=]/)[0]
    .replace(/^\/+|\/+$/g, '');

  const lastSegment = token.split('/').filter(Boolean).pop() || token;
  const normalized = lastSegment.replace(/[-\s]+/g, '_').replace(/[^a-z0-9_]/g, '');

  return normalized || null;
};

const resolveRouteToken = (value?: string | null): RouteTarget | null => {
  const alias = normalizeRouteToken(value);
  if (!alias) return null;

  const tab = TAB_ALIASES[alias] || (VALID_TABS.includes(alias) ? alias : null);
  return tab ? { tab, alias } : null;
};

const getHashCandidates = () => {
  const hash = window.location.hash.replace(/^#/, '');
  if (!hash) return [];

  const params = new URLSearchParams(hash.startsWith('?') ? hash.slice(1) : hash);
  return [
    hash.split(/[?&]/)[0],
    params.get('tgWebAppStartParam'),
    params.get('startapp'),
    params.get('start_param'),
    params.get('tab'),
    params.get('section'),
    params.get('route'),
  ];
};

const getSearchCandidates = () => {
  const params = new URLSearchParams(window.location.search);
  return [
    params.get('tgWebAppStartParam'),
    params.get('startapp'),
    params.get('start_param'),
    params.get('tab'),
    params.get('section'),
    params.get('route'),
  ];
};

const getPathCandidates = () => window.location.pathname.split('/').filter(Boolean).reverse();

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
    console.error("UI error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center min-h-svh bg-zinc-950 select-none">
          <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center mb-8">
             <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          </div>
          
          <h2 className="text-white font-bold mb-4 tracking-tight text-base">Something went wrong</h2>
          <p className="text-sm text-zinc-500 font-medium leading-relaxed mb-10 max-w-[260px]">
            This screen crashed. Reload the app and try again.
          </p>

          <button 
            onClick={() => window.location.reload()}
            className="w-full max-w-[200px] py-4 bg-white text-zinc-950 font-bold rounded-xl uppercase tracking-widest text-[10px] active:scale-[0.98] transition-transform"
          >
            Reload
          </button>

          {this.state.error && (
            <div className="mt-12 p-3 bg-zinc-900/50 border border-white/5 rounded-lg max-w-xs overflow-hidden">
               <p className="text-[8px] text-zinc-600 font-mono break-all line-clamp-2 uppercase">
                  Error: {this.state.error.toString()}
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
  
  const getInitialRoute = useCallback((): RouteTarget => {
    const startParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param;
    const candidates = [
      ...getHashCandidates(),
      ...getSearchCandidates(),
      startParam,
      ...getPathCandidates(),
    ];

    for (const candidate of candidates) {
      const route = resolveRouteToken(candidate);
      if (route) return route;
    }

    return { tab: 'profile', alias: 'profile' };
  }, []);

  const [activeRoute, setActiveRoute] = useState(getInitialRoute());
  const activeTab = activeRoute.tab;
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [selectedChar, setSelectedChar] = useState<any>(null);
  const [selectedPet, setSelectedPet] = useState<any>(null);
  const [revealedChar, setRevealedChar] = useState<any>(null);

  const backHandlerRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    const handleHashChange = () => {
      setActiveRoute(getInitialRoute());
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [getInitialRoute]);

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
    setActiveRoute({ tab, alias: tab });
    if (VALID_TABS.includes(tab) && window.location.hash !== `#${tab}`) {
      window.history.replaceState(null, '', `#${tab}`);
    }
  }, []);

  if (loading) return <IntroLoading />;

  if (error || (!loading && !user)) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-8 text-center min-h-svh bg-zinc-950 relative overflow-hidden select-none">
        <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-white/5 flex items-center justify-center mb-8">
           <div className="w-2 h-2 rounded-full bg-zinc-700 animate-pulse" />
        </div>

        <h2 className="text-white font-bold mb-4 tracking-tight text-base">Could not connect</h2>
        <p className="text-sm text-zinc-500 font-medium leading-relaxed mb-10 max-w-[280px]">
          {error || "We could not authenticate your Telegram session. Open the app from the bot and try again."}
        </p>

        <div className="w-full max-w-[240px] space-y-3">
          <button
            onClick={() => window.location.reload()}
            className="w-full py-4 rounded-xl bg-white text-zinc-950 font-bold uppercase text-[10px] tracking-widest transition-transform active:scale-[0.98]"
          >
            Try again
          </button>
          <button
            onClick={() => {
              window.Telegram?.WebApp?.showConfirm(
                "Clear saved session data and reload?",
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
            Clear saved session
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
          {activeTab === 'profile' && (
            <Profile
              onCharClick={setSelectedChar}
              focusCollection={activeRoute.alias === 'harem' || activeRoute.alias === 'collection'}
            />
          )}
          {activeTab === 'incubation' && <Hatchery />}
          {activeTab === 'shop' && <Shop onCharClick={setSelectedChar} />}
          {activeTab === 'exchange' && <Exchange />}
          {activeTab === 'gallery' && <Gallery onCharClick={setSelectedChar} />}
          {activeTab === 'pets' && <PetShop onPetClick={setSelectedPet} />}
          {activeTab === 'referrals' && <Referrals />}
          {activeTab === 'quests' && <Quests />}
          {activeTab === 'pass' && <Pass />}
          {activeTab === 'leaderboard' && <Leaderboard />}
          {activeTab === 'achievements' && <Achievements />}
          {activeTab === 'mypets' && <MyPets onPetClick={setSelectedPet} />}

          {!VALID_TABS.includes(activeTab) && (
            <NotFound onReset={() => handleNavigate('profile')} />
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
