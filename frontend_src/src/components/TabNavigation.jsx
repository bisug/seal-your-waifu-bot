import { motion } from 'framer-motion';
import { cn } from '../utils';
import { User, Search, Trophy, ShoppingBag, Star, LayoutGrid, Egg } from 'lucide-react';

export const TabNavigation = ({ activeTab, onNavigate }) => {
  const tabs = [
    { id: 'profile', icon: User, label: 'Profile' },
    { id: 'gallery', icon: Search, label: 'Gallery' },
    { id: 'quests', icon: LayoutGrid, label: 'Quests' },
    { id: 'hatchery', icon: Egg, label: 'Hatchery' },
    { id: 'leaderboard', icon: Trophy, label: 'Rank' },
    { id: 'pass', icon: Star, label: 'Pass' },
    { id: 'shop', icon: ShoppingBag, label: 'Shop' },
  ];

  const handleNavigate = (tabId) => {
    if (activeTab !== tabId) {
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
      onNavigate(tabId);
    }
  };

  return (
    <nav className="flex-shrink-0 glass-panel border-t border-white/10 pt-3 backdrop-blur-2xl bg-brand-midnight/40" style={{ paddingBottom: 'calc(1rem + env(safe-area-inset-bottom))' }}>
      <div className="max-w-2xl mx-auto grid grid-cols-7 gap-1 px-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => handleNavigate(tab.id)}
              className="relative flex flex-col items-center justify-center py-3 min-h-[44px] transition-transform active:scale-90"
            >
              <motion.div
                initial={false}
                animate={{
                  scale: isActive ? 1.1 : 1,
                  color: isActive ? '#00f2ff' : '#64748b',
                }}
                className={cn(
                  "p-1 rounded-lg transition-colors",
                  isActive ? "text-brand-neon" : "text-slate-500"
                )}
              >
                <Icon size={18} strokeWidth={isActive ? 2.5 : 2} />
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute -bottom-1 inset-x-0 h-0.5 rounded-full bg-brand-neon neon-shadow shadow-brand-neon/50 z-10 mx-1"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
              </motion.div>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
