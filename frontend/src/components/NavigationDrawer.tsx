import React, { useEffect } from 'react';
import {
  X, User, Egg, ShoppingBag, Search, Dog,
  Zap, Trophy, Swords, Users, Award, PawPrint
} from 'lucide-react';
import { cn } from '../utils';
import { AnimatePresence, motion } from 'framer-motion';

interface NavItem {
  id: string;
  label: string;
  icon: any;
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
      { id: 'quests', label: 'Tasks', icon: Zap },
      { id: 'pass', label: 'Pass', icon: Trophy },
      { id: 'leaderboard', label: 'Leaderboards', icon: Swords },
    ]
  }
];

export const NavigationDrawer = ({ isOpen, onClose, activeTab, onNavigate }: NavigationDrawerProps) => {
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
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[60] bg-black/40"
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'tween', duration: 0.2, ease: "easeOut" }}
            className="fixed top-0 right-0 z-[70] h-full w-[280px] bg-brand-midnight border-l border-white/5 flex flex-col shadow-2xl"
          >
            <div className="p-4 flex items-center justify-between">
              <span className="text-xs font-semibold text-zinc-500">Menu</span>
              <button
                onClick={onClose}
                className="p-1.5 rounded-md hover:bg-zinc-900 border border-transparent hover:border-white/5 text-zinc-400 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-2 py-2 space-y-6">
              {SECTIONS.map((section) => (
                <div key={section.title} className="space-y-1">
                  <h3 className="px-3 text-[10px] font-medium text-zinc-500 uppercase tracking-wider mb-2">
                    {section.title}
                  </h3>
                  <div className="space-y-0.5">
                    {section.items.map((item) => {
                      const Icon = item.icon;
                      const isActive = activeTab === item.id;

                      return (
                        <button
                          key={item.id}
                          onClick={() => handleItemClick(item.id)}
                          className={cn(
                            "w-full flex items-center space-x-3 px-3 py-2 rounded-md transition-all",
                            isActive
                              ? "bg-zinc-900 text-brand-accent border border-white/5"
                              : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/50 border border-transparent"
                          )}
                        >
                          <Icon size={16} strokeWidth={isActive ? 2.5 : 2} />
                          <span className={cn(
                            "text-sm font-medium",
                            isActive ? "text-zinc-100" : ""
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

            <div className="p-4 border-t border-white/5">
               <div className="text-[10px] font-medium text-zinc-600">v2.1.0-stable</div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
