import { motion } from 'framer-motion';
import { Heart, Egg, Store, BookOpen, Repeat2 } from 'lucide-react';
import { cn } from '../utils';

interface BottomNavProps {
  activeTab: string;
  onNavigate: (tab: string) => void;
}

const NAV_ITEMS = [
  { id: 'profile', label: 'Dashboard', icon: Heart },
  { id: 'incubation', label: 'Incubator', icon: Egg },
  { id: 'shop', label: 'Gacha', icon: Store },
  { id: 'exchange', label: 'Market', icon: Repeat2 },
  { id: 'gallery', label: 'Archive', icon: BookOpen },
];

export const BottomNav = ({ activeTab, onNavigate }: BottomNavProps) => {
  return (
    <nav className="fixed bottom-0 inset-x-0 z-[90] pb-[calc(var(--sab,24px)+4px)] pt-3 px-6 bg-brand-midnight/80 backdrop-blur-2xl border-t border-white/[0.04] safe-bottom">
      <div className="max-w-lg mx-auto flex items-center justify-between">
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
                "flex flex-col items-center gap-1.5 transition-all duration-300 relative py-1 px-3 rounded-xl",
                isActive ? "text-brand-accent" : "text-neutral-500 hover:text-neutral-300"
              )}
            >
              <div className="relative">
                <Icon
                  size={20}
                  strokeWidth={isActive ? 2.5 : 2}
                  className={cn(
                    "transition-transform duration-300",
                    isActive && "scale-110 drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]"
                  )}
                />
                {isActive && (
                  <motion.div
                    layoutId="active-nav-glow"
                    className="absolute -inset-2 bg-brand-accent/10 rounded-full blur-md -z-10"
                  />
                )}
              </div>
              <span className={cn(
                "text-[9px] font-black uppercase tracking-[0.1em] transition-opacity duration-300",
                isActive ? "opacity-100" : "opacity-40"
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
