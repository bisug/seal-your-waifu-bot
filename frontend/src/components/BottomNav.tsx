import { motion } from 'framer-motion';
import { Heart, Egg, Store, BookOpen, Repeat2 } from 'lucide-react';
import { cn } from '../utils';

interface BottomNavProps {
  activeTab: string;
  onNavigate: (tab: string) => void;
}

const NAV_ITEMS = [
  { id: 'profile', label: 'Dashboard', icon: Heart },
  { id: 'incubation', label: 'Hatchery', icon: Egg },
  { id: 'shop', label: 'Summon', icon: Store },
  { id: 'exchange', label: 'Market', icon: Repeat2 },
  { id: 'gallery', label: 'Archive', icon: BookOpen },
];

export const BottomNav = ({ activeTab, onNavigate }: BottomNavProps) => {
  return (
    <nav className="fixed bottom-0 inset-x-0 z-[90] pb-[calc(var(--sab,24px)+8px)] pt-3 px-4 bg-zinc-950/80 backdrop-blur-md border-t border-white/[0.04] safe-bottom">
      <div className="max-w-md mx-auto flex items-center justify-between">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => {
                window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                onNavigate(item.id);
              }}
              className={cn(
                "flex flex-col items-center gap-1.5 transition-all duration-200 relative py-1 flex-1",
                isActive ? "text-brand-accent" : "text-zinc-500 hover:text-zinc-300"
              )}
            >
              <div className="relative">
                <Icon
                  size={20}
                  strokeWidth={isActive ? 2.5 : 2}
                  className={cn(
                    "transition-all duration-200",
                    isActive && "scale-110"
                  )}
                />
                {isActive && (
                  <motion.div
                    layoutId="active-nav-indicator"
                    className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-brand-accent rounded-full"
                  />
                )}
              </div>
              <span className={cn(
                "text-[9px] font-bold uppercase tracking-widest transition-opacity duration-200",
                isActive ? "opacity-100" : "opacity-50"
              )}>
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
