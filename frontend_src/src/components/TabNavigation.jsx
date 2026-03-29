import { motion } from 'framer-motion';
import { User, Search, Trophy, ShoppingBag, Star, LayoutGrid } from 'lucide-react';
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
    <nav className="fixed bottom-0 left-0 right-0 glass-panel border-t border-brand-glass-border pb-8 pt-4 z-50">
      <div className="max-w-2xl mx-auto flex justify-between items-center px-6">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => handleNavigate(tab.id)}
              className="relative flex flex-col items-center justify-center p-2"
            >
              <motion.div
                initial={false}
                animate={{
                  scale: isActive ? 1.2 : 1,
                  color: isActive ? '#00f2ff' : '#94a3b8',
                }}
                className={cn(
                  "p-2 rounded-xl transition-colors",
                  isActive ? "text-brand-neon" : "text-slate-400"
                )}
              >
                <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-brand-neon neon-shadow"
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
