import React, { useEffect } from 'react';
import {
  X, User, Egg, ShoppingBag, Search, Dog, ArrowLeftRight,
  Zap, Trophy, Swords, Users, Award, PawPrint, UploadCloud
} from 'lucide-react';
import { cn } from '../utils';
import { AnimatePresence, motion } from 'framer-motion';
import { useUser } from '../context/UserContext';

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
      { id: 'exchange', label: 'Exchange', icon: ArrowLeftRight },
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
  const { user } = useUser();
  const sections = user?.is_sudo
    ? [
        ...SECTIONS,
        {
          title: "Admin",
          items: [{ id: 'upload', label: 'Upload', icon: UploadCloud }],
        },
      ]
    : SECTIONS;

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
            className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm"
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'tween', duration: 0.25, ease: "circOut" }}
            className="fixed top-0 right-0 z-[70] h-full w-[280px] sm:w-[320px] bg-brand-midnight border-l border-white/10 flex flex-col shadow-2xl"
          >
            <div className="p-4 flex items-center justify-between border-b border-white/5">
              <span className="text-sm font-semibold text-white">Menu</span>
              <button
                onClick={onClose}
                className="p-2 -mr-2 rounded-lg text-neutral-400 hover:text-white hover:bg-white/5 transition-colors"
                aria-label="Close Menu"
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
              {sections.map((section) => (
                <div key={section.title} className="space-y-2">
                  <h3 className="px-2 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
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
                            "w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all",
                            isActive
                              ? "bg-brand-accent/10 text-brand-accent"
                              : "text-neutral-400 hover:text-neutral-200 hover:bg-white/5"
                          )}
                        >
                          <Icon size={18} strokeWidth={isActive ? 2.5 : 2} />
                          <span className={cn(
                            "text-sm font-medium",
                            isActive ? "text-brand-accent" : "text-neutral-300"
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
               <div className="text-xs font-medium text-neutral-500 text-center">v2.1.0-stable</div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
