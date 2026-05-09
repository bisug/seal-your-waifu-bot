import { motion } from 'framer-motion';
import { cn } from '../utils';
import { User, Search, Trophy, ShoppingBag, Star, LayoutGrid, Egg, Activity } from 'lucide-react';

export const TabNavigation = ({ activeTab, onNavigate }) => {
  const tabs = [
    { id: 'profile', icon: User, label: 'Profile' },
    { id: 'incubation', icon: Egg, label: 'Hatchery' },
    { id: 'market', icon: ShoppingBag, label: 'Market' },
    { id: 'nexus', icon: Activity, label: 'Nexus' },
  ];

  const handleNavigate = (tabId) => {
    if (activeTab !== tabId) {
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
      onNavigate(tabId);
    }
  };

  return (
    <nav className="flex-shrink-0 glass-panel border-t border-white/10 pt-3 backdrop-blur-3xl bg-brand-midnight/70 shadow-[0_-15px_40px_rgba(0,0,0,0.4)]" style={{ paddingBottom: 'calc(1.1rem + env(safe-area-inset-bottom))' }}>
      <div className="max-w-screen-sm mx-auto flex justify-around px-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <motion.button
              key={tab.id}
              onClick={() => handleNavigate(tab.id)}
              whileTap={{ scale: 0.9 }}
              className="relative flex flex-col items-center justify-center min-w-[64px] py-1"
            >
              <motion.div
                initial={false}
                animate={{
                  y: isActive ? -4 : 0,
                  color: isActive ? '#34d399' : '#64748b',
                }}
                className={cn(
                  "p-2.5 rounded-2xl transition-all duration-300 relative",
                  isActive ? "bg-brand-neon/10 shadow-[0_0_20px_rgba(52,211,153,0.1)]" : ""
                )}
              >
                <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
              </motion.div>
              
              <span className={cn(
                "text-[9px] font-black uppercase tracking-[0.2em] mt-1.5 transition-all duration-300",
                isActive ? "text-brand-neon opacity-100" : "text-slate-500 opacity-60"
              )}>
                {tab.label}
              </span>

              {isActive && (
                <motion.div
                  layoutId="activeTabGlow"
                  initial={false}
                  className="absolute -bottom-3 inset-x-0 h-1 rounded-full bg-brand-neon neon-shadow shadow-brand-neon/40 z-10 mx-auto w-10"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
            </motion.button>
          );
        })}
      </div>
    </nav>
  );
};
