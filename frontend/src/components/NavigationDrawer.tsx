import React, { useEffect } from 'react';
import {
  X, User, Egg, ShoppingBag, Search, Dog,
  Zap, Trophy, Swords, Repeat, Heart, Users, Activity,
  LucideIcon, Award, PawPrint
} from 'lucide-react';
import { cn } from '../utils';
import { AnimatePresence, motion } from 'framer-motion';

interface NavItem {
  id: string;
  label: string;
  icon: LucideIcon;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

interface NavigationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: string;
  onNavigate: (tabId: string) => void;
}

const SECTIONS: NavSection[] = [
  {
    title: "Personal",
    items: [
      { id: 'profile', label: 'Profile', icon: User },
      { id: 'mypets', label: 'My Pets', icon: PawPrint },
      { id: 'incubation', label: 'Incubation', icon: Egg },
      { id: 'achievements', label: 'Achievements', icon: Award },
    ]
  },
  {
    title: "Marketplace",
    items: [
      { id: 'shop', label: 'Daily Shop', icon: ShoppingBag },
      { id: 'gallery', label: 'Catalog', icon: Search },
      { id: 'pets', label: 'Pet Store', icon: Dog },
    ]
  },
  {
    title: "Social",
    items: [
      { id: 'referrals', label: 'Referrals', icon: Users },
    ]
  },
  {
    title: "Competitive",
    items: [
      { id: 'quests', label: 'Tasks/Quests', icon: Zap },
      { id: 'pass', label: 'Battle Pass', icon: Trophy },
      { id: 'leaderboard', label: 'Leaderboards', icon: Swords },
    ]
  }
];

export const NavigationDrawer = ({ isOpen, onClose, activeTab, onNavigate }: NavigationDrawerProps) => {
  // Lock body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const handleItemClick = (id: string) => {
    onNavigate(id);
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[60] bg-black/60"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-0 right-0 z-[70] h-full w-4/5 max-w-[320px] bg-brand-midnight border-l border-white/5 flex flex-col"
          >
            {/* Drawer Header */}
            <div className="p-4 border-b border-white/5 flex items-center justify-between">
              <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Navigation</span>
              <button
                onClick={onClose}
                className="p-2 rounded-xl bg-white/5 border border-white/5 text-slate-400 active:scale-95 transition-all"
              >
                <X size={18} />
              </button>
            </div>

            {/* Nav Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {SECTIONS.map((section) => (
                <div key={section.title} className="space-y-2">
                  <h3 className="px-2 text-[9px] font-black uppercase tracking-[0.25em] text-brand-accent/60">
                    {section.title}
                  </h3>
                  <div className="space-y-1">
                    {section.items.map((item) => {
                      const Icon = item.icon;
                      const isActive = activeTab === item.id;

                      return (
                        <button
                          key={item.id}
                          onClick={() => handleItemClick(item.id)}
                          className={cn(
                            "w-full flex items-center space-x-3 px-3 py-3 rounded-xl transition-all border active:scale-[0.98]",
                            isActive
                              ? "bg-brand-accent/10 border-brand-accent/20 text-brand-accent"
                              : "bg-white/5 border-transparent text-slate-400 hover:border-white/5"
                          )}
                        >
                          <Icon size={16} strokeWidth={isActive ? 2.5 : 2} />
                          <span className={cn(
                            "text-[11px] font-bold tracking-wide uppercase",
                            isActive ? "text-white" : "text-slate-500"
                          )}>
                            {item.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            {/* Bottom Branding */}
            <div className="p-6 border-t border-white/5 flex flex-col items-center">
               <div className="text-[10px] font-black text-slate-700 uppercase tracking-[0.3em] mb-1">Lite Build v2.0</div>
               <div className="text-[8px] font-bold text-slate-800 uppercase tracking-widest">© 2026 GRABBER BOT</div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
