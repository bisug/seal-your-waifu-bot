import { motion } from 'framer-motion';
import { cn } from '../utils';
import { User, ShoppingBag, Egg, Activity, LucideIcon } from 'lucide-react';
import { useUser } from '../context/UserContext';

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
  const { liteMode } = useUser();
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
    <nav className={cn(
      "flex-shrink-0 border-t border-white/10 pt-2 bg-brand-midnight/80",
      !liteMode && "glass-panel backdrop-blur-3xl shadow-[0_-10px_30px_rgba(0,0,0,0.4)]"
    )} style={{ paddingBottom: 'calc(0.7rem + env(safe-area-inset-bottom))' }}>
      <div className="max-w-screen-sm mx-auto flex justify-around px-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <motion.button
              key={tab.id}
              onClick={() => handleNavigate(tab.id)}
              whileTap={liteMode ? undefined : { scale: 0.9 }}
              className="relative flex flex-col items-center justify-center min-w-[60px] py-0.5"
            >
              <motion.div
                initial={false}
                animate={liteMode ? undefined : {
                  y: isActive ? -6 : 0,
                  color: isActive ? '#ffffff' : '#64748b',
                }}
                className={cn(
                  "p-3 rounded-2xl transition-all duration-300 relative",
                  isActive ? "bg-gradient-to-tr from-brand-accent to-brand-accent-secondary shadow-neon" : ""
                )}
                style={liteMode ? { color: isActive ? '#ffffff' : '#64748b', transform: isActive ? 'translateY(-6px)' : undefined } : undefined}
              >
                <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
              </motion.div>
              
              <span className={cn(
                "text-[9px] font-bold uppercase tracking-widest mt-1.5 transition-all duration-300",
                isActive ? "text-white opacity-100" : "text-slate-500 opacity-60"
              )}>
                {tab.label}
              </span>
            </motion.button>
          );
        })}
      </div>
    </nav>
  );
};
