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
    <nav className="flex-shrink-0 border-t border-white/5 bg-brand-midnight pt-1"
         style={{ paddingBottom: 'calc(0.5rem + env(safe-area-inset-bottom))' }}>
      <div className="max-w-screen-sm mx-auto flex justify-around px-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => handleNavigate(tab.id)}
              className="relative flex flex-col items-center justify-center min-w-[64px] py-2 transition-colors duration-200"
            >
              <div className={cn(
                "p-2 rounded-xl transition-all duration-200",
                isActive ? "text-brand-accent bg-brand-accent/10" : "text-slate-500 hover:text-slate-400"
              )}>
                <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
              </div>
              
              <span className={cn(
                "text-[8px] font-bold uppercase tracking-widest mt-1 transition-colors duration-200",
                isActive ? "text-brand-accent" : "text-slate-600"
              )}>
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
