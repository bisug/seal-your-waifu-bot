import React, { useState, useEffect, Suspense, lazy, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { UserProvider, useUser } from './context/UserContext';
import { TabNavigation } from './components/TabNavigation';
import { Profile } from './pages/Profile';
import { NotFound } from './pages/NotFound';
import { Modal, ToastProvider } from './components/UI';
import { Zap } from 'lucide-react';
import { apiFetch } from './api';
import { toast } from 'react-hot-toast';
import { formatNumber } from './utils';

// Lazy load pages for extreme performance
const Gallery = lazy(() => import('./pages/Gallery').then(m => ({ default: m.Gallery })));
const Quests = lazy(() => import('./pages/Quests').then(m => ({ default: m.Quests })));
const Leaderboard = lazy(() => import('./pages/Leaderboard').then(m => ({ default: m.Leaderboard })));
const Pass = lazy(() => import('./pages/Pass').then(m => ({ default: m.Pass })));
const Shop = lazy(() => import('./pages/Shop').then(m => ({ default: m.Shop })));
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
             <h2 className="text-red-500 font-black mb-2 uppercase tracking-[0.3em]">Critical Overload</h2>
             <p className="text-[10px] text-red-400 font-mono break-all">{this.state.error?.toString() || 'Unknown Error Signature'}</p>
          </div>
          
          <p className="text-slate-500 text-[10px] mb-8 uppercase tracking-widest">A UI module has desynchronized. Initiate recovery?</p>
          
          <button 
            onClick={() => window.location.reload()}
            className="px-8 py-4 bg-brand-accent text-white font-black rounded-2xl uppercase tracking-widest text-[11px] neon-shadow shadow-brand-accent/50 active:scale-95 transition-transform"
          >
            RESTABILIZE
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const LoadingScreen = () => (
  <div className="fixed inset-0 bg-brand-midnight flex flex-col items-center justify-center p-12 bg-mesh overflow-hidden">
    {/* Ambient Glows */}
    <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-brand-neon/5 blur-[120px] rounded-full" />
    <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-brand-accent/5 blur-[120px] rounded-full" />
    <motion.div 
      animate={{ 
        scale: [1, 1.1, 1],
        opacity: [0.5, 1, 0.5] 
      }}
      transition={{ 
        repeat: Infinity, 
        duration: 2,
        ease: "easeInOut"
      }}
      className="w-24 h-24 mb-8 relative"
    >
      <div className="absolute inset-0 rounded-full border-4 border-brand-neon opacity-20" />
      <div className="absolute inset-0 rounded-full border-t-4 border-brand-neon animate-spin" />
      <div className="absolute inset-4 rounded-full bg-brand-neon/10 flex items-center justify-center blur-sm transform scale-150 animate-pulse" />
    </motion.div>
    <p className="text-brand-neon font-black uppercase tracking-[0.5em] text-[10px] animate-pulse">Syncing Protocols</p>
  </div>
);

const AppContent = () => {
  const { user, loading, error } = useUser();
  
  // Intelligence: Read the start_param for deep-linking (e.g., Shop/Gallery/Profile)
  const getInitialTab = () => {
    const startParam = window.Telegram?.WebApp?.initDataUnsafe?.start_param;
    if (startParam === 'shop') return 'shop';
    if (startParam === 'gallery') return 'gallery';
    if (startParam === 'leaderboard') return 'leaderboard';
    return 'profile';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab());
  const [selectedChar, setSelectedChar] = useState(null);

  // Native Telegram Integration: Back Button & Haptics
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (!tg) return;

    try {
      if (selectedChar) {
        tg.BackButton?.show?.();
        tg.BackButton?.onClick?.(() => setSelectedChar(null));
      } else {
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
        tg.BackButton?.offClick?.(() => setSelectedChar(null));
      } catch (e) {
        // ignore
      }
    };
  }, [selectedChar]);

  const handleNavigate = useCallback((tab) => {
    const tg = window.Telegram?.WebApp;
    // Context-Aware Haptics: Profile & Shop get more 'Weight'
    if (tab === 'profile' || tab === 'shop') {
      tg?.HapticFeedback?.impactOccurred('medium');
    } else {
      tg?.HapticFeedback?.impactOccurred('light');
    }
    setActiveTab(tab);
  }, []);

  if (loading) return <LoadingScreen />;

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
          
          <h2 className="text-brand-accent font-black mb-2 uppercase tracking-[0.3em] text-xl">Signal Interrupted</h2>
          <p className="text-slate-500 text-[10px] mb-10 leading-relaxed uppercase tracking-widest max-w-[200px] mx-auto">
            {error || "Authentication handshake timeout. Please re-open the portal."}
          </p>
          
          <div className="space-y-4">
            <button 
              onClick={() => window.location.reload()}
              className="w-full px-10 py-5 rounded-2xl bg-brand-accent text-brand-midnight font-black uppercase text-[10px] tracking-[0.2em] shadow-xl shadow-brand-accent/20 transition-all active:scale-95 flex items-center justify-center gap-3"
            >
              RE-ESTABLISH LINK
            </button>
            <button 
              onClick={() => { localStorage.clear(); window.location.reload(); }}
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
            {activeTab === 'gallery' && <Gallery onCharClick={setSelectedChar} />}
            {activeTab === 'quests' && <Quests />}
            {activeTab === 'leaderboard' && <Leaderboard />}
            {activeTab === 'pass' && <Pass />}
            {activeTab === 'shop' && <Shop onCharClick={setSelectedChar} />}
            {activeTab === 'hatchery' && <Hatchery />}
            {!['profile', 'gallery', 'quests', 'leaderboard', 'pass', 'shop', 'hatchery'].includes(activeTab) && (
              <NotFound onReset={() => setActiveTab('profile')} />
            )}
          </Suspense>
        </motion.main>
      </AnimatePresence>

      <AnimatePresence>
        {selectedChar && (
          <Modal
            character={selectedChar}
            onClose={() => setSelectedChar(null)}
            actions={
              activeTab === 'profile' && selectedChar.count > 1 ? (
                <button 
                  onClick={async () => {
                    try {
                        const confirm = window.confirm(`Recycle 1 x ${selectedChar.name} for Zenith?`);
                        if (!confirm) return;
                        await apiFetch('/recycle', { 
                            method: 'POST', 
                            body: JSON.stringify([selectedChar.id]) 
                        });
                        toast.success('Nexus Fusion Complete');
                        setSelectedChar(null);
                        window.dispatchEvent(new CustomEvent('user-data-refresh'));
                    } catch (err) {
                        toast.error(err.message || 'Fusion failed');
                    }
                  }}
                  className="w-full py-3.5 rounded-xl bg-brand-accent/10 border border-brand-accent/20 text-brand-accent text-[10px] font-black uppercase tracking-widest hover:bg-brand-accent/20 transition-all flex items-center justify-center space-x-2 mb-4"
                >
                    <Zap size={14} />
                    <span>Recycle Duplicate</span>
                </button>
              ) : activeTab === 'shop' && !selectedChar.owned ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-brand-neon/5 border border-brand-neon/20 rounded-2xl">
                     <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-full bg-brand-neon/20 flex items-center justify-center text-brand-neon shadow-lg shadow-brand-neon/20">
                           <Zap size={20} />
                        </div>
                        <div>
                           <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest">Buy Value</p>
                           <p className="text-sm font-black text-white">✧ {formatNumber(selectedChar.zenith_price || 5)}</p>
                        </div>
                     </div>
                     <button 
                        onClick={() => {
                            const confirm = window.confirm(`Authorize purchase of ${selectedChar.name}?`);
                            if (confirm) {
                                window.dispatchEvent(new CustomEvent('shop-buy-character', { detail: { charId: String(selectedChar.id) } }));
                                setSelectedChar(null);
                            }
                        }}
                        className="px-6 py-3 rounded-2xl bg-brand-neon text-brand-midnight text-[10px] font-black uppercase tracking-[0.2em] shadow-xl shadow-brand-neon/30 active:scale-95 transition-all"
                     >
                        BUY NOW
                     </button>
                  </div>
                </div>
              ) : null
            }
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
