import React, { useState, Suspense, lazy } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UserProvider, useUser } from './context/UserContext';
import { TabNavigation } from './components/TabNavigation';
import { Profile } from './pages/Profile';
import { Modal } from './components/UI';

// Lazy load pages for extreme performance
const Gallery = lazy(() => import('./pages/Gallery').then(m => ({ default: m.Gallery })));
const Quests = lazy(() => import('./pages/Quests').then(m => ({ default: m.Quests })));
const Leaderboard = lazy(() => import('./pages/Leaderboard').then(m => ({ default: m.Leaderboard })));
const Pass = lazy(() => import('./pages/Pass').then(m => ({ default: m.Pass })));
const Shop = lazy(() => import('./pages/Shop').then(m => ({ default: m.Shop })));

const LoadingScreen = () => (
  <div className="fixed inset-0 bg-brand-midnight flex flex-col items-center justify-center p-12">
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
  const [activeTab, setActiveTab] = useState('profile');
  const [selectedChar, setSelectedChar] = useState(null);

  if (loading) return <LoadingScreen />;

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-10 text-center min-h-svh">
        <h2 className="text-brand-neon font-black mb-4 uppercase tracking-widest text-xl">Connection Offline</h2>
        <p className="text-slate-500 text-xs mb-8 leading-relaxed uppercase tracking-widest">{error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="px-10 py-4 rounded-2xl bg-brand-neon text-brand-midnight font-black uppercase text-[10px] tracking-[0.2em] shadow-xl shadow-brand-neon/20 transition-transform active:scale-95"
        >
          RETRY STABILIZATION
        </button>
      </div>
    );
  }

  return (
    <div className="relative min-h-svh flex flex-col overflow-x-hidden">
      <AnimatePresence mode="wait">
        <motion.main
          key={activeTab}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -10 }}
          transition={{ duration: 0.2 }}
          className="flex-1 adaptive-px"
        >
          <Suspense fallback={<div className="flex-1 animate-pulse bg-brand-midnight" />}>
            {activeTab === 'profile' && <Profile onCharClick={setSelectedChar} />}
            {activeTab === 'gallery' && <Gallery onCharClick={setSelectedChar} />}
            {activeTab === 'quests' && <Quests />}
            {activeTab === 'leaderboard' && <Leaderboard />}
            {activeTab === 'pass' && <Pass />}
            {activeTab === 'shop' && <Shop onCharClick={setSelectedChar} />}
          </Suspense>
        </motion.main>
      </AnimatePresence>

      <AnimatePresence>
        {selectedChar && (
          <Modal 
            character={selectedChar} 
            onClose={() => setSelectedChar(null)} 
          />
        )}
      </AnimatePresence>

      <TabNavigation activeTab={activeTab} onNavigate={setActiveTab} />
    </div>
  );
};

function App() {
  return (
    <UserProvider>
      <AppContent />
    </UserProvider>
  );
}

export default App;
