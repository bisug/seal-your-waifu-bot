import { motion } from 'framer-motion';
import { cn } from '../utils';
import { User, Search, Trophy, ShoppingBag, Star, LayoutGrid, Egg } from 'lucide-react';

export const TabNavigation = ({ activeTab, onNavigate }) => {
  const tabs = [
    { id: 'profile', icon: User, label: 'Harem' },
    { id: 'incubation', icon: Egg, label: 'Hatchery' },
    { id: 'market', icon: ShoppingBag, label: 'Market' },
    { id: 'nexus', icon: Zap, label: 'Nexus' },
  ];

  const handleNavigate = (tabId) => {
    if (activeTab !== tabId) {
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
      onNavigate(tabId);
    }
  };

  return (
    <nav className="flex-shrink-0 glass-panel border-t border-white/10 pt-2 backdrop-blur-3xl bg-brand-midnight/60 shadow-[0_-10px_40px_rgba(0,0,0,0.5)]" style={{ paddingBottom: 'calc(0.75rem + env(safe-area-inset-bottom))' }}>
      <div className="max-w-screen-sm mx-auto grid grid-cols-7 gap-0.5 px-0.5">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => handleNavigate(tab.id)}
              className="relative flex flex-col items-center justify-center py-2.5 min-h-[44px] transition-transform active:scale-90"
            >
              <motion.div
                initial={false}
                animate={{
                  scale: isActive ? 1.05 : 1,
                  color: isActive ? '#34d399' : '#475569',
                }}
                className={cn(
                  "p-1.5 rounded-xl transition-colors relative",
                  isActive ? "bg-brand-neon/5" : "text-slate-500"
                )}
              >
                <Icon size={18} strokeWidth={isActive ? 2.5 : 2} />
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute -bottom-2 inset-x-2 h-0.5 rounded-full bg-brand-neon neon-shadow shadow-brand-neon/50 z-10"
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
