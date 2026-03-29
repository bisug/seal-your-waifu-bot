import { motion } from 'framer-motion';
import { User, Search, Trophy, ShoppingBag, Star, LayoutGrid, Egg } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility for combining Tailwind classes cleanly.
 */
function cn(...inputs) {
  return twMerge(clsx(inputs));
}

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
    <nav className="fixed bottom-0 left-0 right-0 glass-panel border-t border-white/10 pt-3 z-50 backdrop-blur-2xl bg-brand-midnight/40" style={{ height: 'var(--nav-height)', paddingBottom: 'env(safe-area-inset-bottom)' }}>
      <div className="max-w-2xl mx-auto flex justify-around items-center px-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => handleNavigate(tab.id)}
              className="relative flex flex-col items-center justify-center p-1.5 min-w-[38px]"
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
