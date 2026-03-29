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

const AppContent = () => {
  const { user, loading, error } = useUser();
  const [activeTab, setActiveTab] = useState('profile');
  const [selectedChar, setSelectedChar] = useState(null);

  if (loading) return <LoadingScreen />;

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-10 text-center">
        <h2 className="text-brand-neon font-black mb-4 uppercase tracking-widest">Connection Error</h2>
        <p className="text-slate-400 text-sm mb-6 leading-relaxed">{error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="px-8 py-3 rounded-full bg-brand-neon text-brand-midnight font-bold uppercase text-xs transition-transform hover:scale-105"
        >
          RETRY
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
