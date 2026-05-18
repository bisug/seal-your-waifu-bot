import { motion } from 'framer-motion';
import { cn } from '../utils';
import { User, ShoppingBag, Egg, Activity, LucideIcon } from 'lucide-react';

interface Tab {
  id: string;
  icon: LucideIcon;
  label: string;
}

interface TabNavigationProps {
  activeTab: string;
  onNavigate: (tabId: string) => void;
}

export const TabNavigation = ({ activeTab, onNavigate }: TabNavigationProps) => {
  const tabs: Tab[] = [
    { id: 'profile', icon: User, label: 'Profile' },
    { id: 'incubation', icon: Egg, label: 'Hatchery' },
    { id: 'market', icon: ShoppingBag, label: 'Market' },
    { id: 'nexus', icon: Activity, label: 'Nexus' },
  ];

  const handleNavigate = (tabId: string) => {
    if (activeTab !== tabId) {
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
      onNavigate(tabId);
    }
  };

  return (
    <nav className="flex-shrink-0 glass-panel border-t border-white/10 pt-2 backdrop-blur-3xl bg-brand-midnight/70 shadow-[0_-10px_30px_rgba(0,0,0,0.4)]" style={{ paddingBottom: 'calc(0.7rem + env(safe-area-inset-bottom))' }}>
      <div className="max-w-screen-sm mx-auto flex justify-around px-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <motion.button
              key={tab.id}
              onClick={() => handleNavigate(tab.id)}
              whileTap={{ scale: 0.9 }}
              className="relative flex flex-col items-center justify-center min-w-[60px] py-0.5"
            >
              <motion.div
                initial={false}
                animate={{
                  y: isActive ? -2 : 0,
                  color: isActive ? 'var(--color-brand-accent)' : '#64748b',
                }}
                className={cn(
                  "p-2 rounded-xl transition-all duration-300 relative",
                  isActive ? "bg-brand-accent/10" : ""
                )}
              >
                <Icon size={18} strokeWidth={isActive ? 2.5 : 2} />
              </motion.div>
              
              <span className={cn(
                "text-[8px] font-black uppercase tracking-[0.15em] mt-1 transition-all duration-300",
                isActive ? "text-brand-accent opacity-100" : "text-slate-500 opacity-60"
              )}>
                {tab.label}
              </span>

              {isActive && (
                <motion.div
                  layoutId="activeTabGlow"
                  initial={false}
                  className="absolute -bottom-2.5 inset-x-0 h-0.5 rounded-full bg-brand-accent neon-shadow shadow-brand-accent/40 z-10 mx-auto w-8"
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
