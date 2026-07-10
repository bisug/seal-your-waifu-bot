import React, { useState, useEffect, Suspense, lazy, useCallback, useRef, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { SpeedInsights } from '@vercel/speed-insights/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { UserProvider, useUser } from './context/UserContext';
import { Header } from './components/Header';
import { NavigationDrawer } from './components/NavigationDrawer';
import { IntroLoading } from './components/IntroLoading';
import { Profile } from './pages/Profile';
import { NotFound } from './pages/NotFound';
import { Forbidden } from './pages/Forbidden';
import { ServerError } from './pages/ServerError';
import { Landing } from './pages/Landing';
import { ToastProvider } from './components/ui/Toast';
import { CharActionModal } from './components/character/CharActionModal';
import { PetActionModal } from './components/pet/PetActionModal';
import { GachaReveal } from './components/ui/GachaReveal';
import { AnimatePresence, motion } from 'framer-motion';

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
const Upload = lazy(() => import('./pages/Upload').then(m => ({ default: m.Upload })));
const Staff = lazy(() => import('./pages/Staff').then(m => ({ default: m.Staff })));
const Minigames = lazy(() => import('./pages/Minigames').then(m => ({ default: m.Minigames })));

const VALID_TABS = ['profile', 'incubation', 'shop', 'exchange', 'gallery', 'pets', 'referrals', 'quests', 'pass', 'leaderboard', 'achievements', 'mypets', 'upload', 'staff', 'minigames'];
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
  upload: 'upload',
  uploads: 'upload',
  admin: 'upload',
  sudo: 'staff',
  sudos: 'staff',
  staff: 'staff',
  contributors: 'staff',
  contributions: 'staff',
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
  minigames: 'minigames',
  games: 'minigames',
  nexus_games: 'minigames',
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
    // ignore
  }

  token = token
    .toLowerCase()
    .replace(/^https?:\/\/[^/]+/i, '')
    .replace(/^#/, '')
    .replace(/^[?/]+/, '')
    .split(/[?&#=]/)[0]
    .replace(/^\/+|\/+$/g, '');

  const lastSegment = token.split('/').filter(Boolean).pop() || token;
  return lastSegment.replace(/[-\s]+/g, '_').replace(/[^a-z0-9_]/g, '') || null;
};

const resolveRouteToken = (value?: string | null): RouteTarget | null => {
  const alias = normalizeRouteToken(value);
  if (!alias) return null;

  const tab = TAB_ALIASES[alias] || alias;
  return { tab, alias };
};

const getCandidates = () => {
  const params = new URLSearchParams(window.location.search);
  const hash = window.location.hash.replace(/^#/, '').split(/[?&]/)[0];
  return [
    hash,
    params.get('tgWebAppStartParam'),
    params.get('startapp'),
    params.get('tab'),
    params.get('route'),
  ];
};

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <ServerError onRetry={() => window.location.reload()} />;
    }
    return this.props.children;
  }
}


const AppContent = () => {
  const { user, loading, error } = useUser();
  
  const getInitialRoute = useCallback((): RouteTarget => {
    const startParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param;
    const candidates = [...getCandidates(), startParam];

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

    return () => {
        if (backHandlerRef.current) {
            tg?.BackButton?.offClick?.(backHandlerRef.current);
        }
    };
  }, [selectedChar, selectedPet, isMenuOpen]);

  const handleNavigate = useCallback((tab: string) => {
    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
    setActiveRoute({ tab, alias: tab });
    if (VALID_TABS.includes(tab) && window.location.hash !== `#${tab}`) {
      window.history.replaceState(null, '', `#${tab}`);
    }
  }, []);

  if (loading) return <IntroLoading />;

  if (error || (!loading && !user)) {
    const hasTelegramInit = Boolean(window.Telegram?.WebApp?.initData);
    if (!hasTelegramInit && !sessionStorage.getItem('auth_token')) {
      return <Landing error={error} onRetry={() => window.location.reload()} />;
    }

    return <ServerError onRetry={() => window.location.reload()} />;
  }

  const canViewUpload = Boolean(user?.can_upload ?? user?.is_sudo);
  const canViewStaff = Boolean(user?.is_sudo);
  const isBlockedTab = (activeTab === 'upload' && !canViewUpload) || (activeTab === 'staff' && !canViewStaff);

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden bg-zinc-950">
      <Header onMenuClick={() => setIsMenuOpen(true)} />

      <main className="app-scroller adaptive-px pb-8">
        <Suspense fallback={
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <Loader2 size={24} className="animate-spin text-zinc-700" />
          </div>
        }>
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
              className="page-transition-wrapper"
            >
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
              {activeTab === 'minigames' && <Minigames />}
              {activeTab === 'upload' && canViewUpload && <Upload />}
              {activeTab === 'staff' && canViewStaff && <Staff />}

              {isBlockedTab ? (
                <Forbidden onReset={() => handleNavigate('profile')} />
              ) : !VALID_TABS.includes(activeTab) ? (
                <NotFound onReset={() => handleNavigate('profile')} />
              ) : null}
            </motion.div>
          </AnimatePresence>
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

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      gcTime: 1000 * 60 * 30,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <UserProvider>
            <AppContent />
          </UserProvider>
        </ToastProvider>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
      <SpeedInsights />
    </ErrorBoundary>
  );
}

export default App;
