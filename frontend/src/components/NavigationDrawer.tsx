import { useEffect } from 'react';
import {
  X,
  UserRound,
  Egg,
  Store,
  BookOpen,
  Bone,
  Repeat2,
  ListChecks,
  Ticket,
  ChartNoAxesColumnIncreasing,
  UserPlus,
  BadgeCheck,
  PawPrint,
  CloudUpload,
  ShieldCheck,
  Terminal,
} from 'lucide-react';
import { cn } from '../utils';
import { AnimatePresence, motion } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';

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
    title: "OPERATIONS",
    items: [
      { id: 'profile', label: 'Dashboard', icon: UserRound },
      { id: 'incubation', label: 'Incubator', icon: Egg },
      { id: 'mypets', label: 'Companions', icon: PawPrint },
      { id: 'achievements', label: 'Milestones', icon: BadgeCheck },
    ]
  },
  {
    title: "LOGISTICS",
    items: [
      { id: 'shop', label: 'Daily Market', icon: Store },
      { id: 'exchange', label: 'Currency', icon: Repeat2 },
      { id: 'gallery', label: 'Archives', icon: BookOpen },
      { id: 'pets', label: 'Breeder', icon: Bone },
    ]
  },
  {
    title: "ENGAGEMENT",
    items: [
      { id: 'referrals', label: 'Recruit', icon: UserPlus },
      { id: 'quests', label: 'Missions', icon: ListChecks },
      { id: 'pass', label: 'Operations Pass', icon: Ticket },
      { id: 'leaderboard', label: 'Rankings', icon: ChartNoAxesColumnIncreasing },
    ]
  }
];

export const NavigationDrawer = ({ isOpen, onClose, activeTab, onNavigate }: NavigationDrawerProps) => {
  const { user } = useUser();
  const staffItems = [
    ...(user?.is_sudo ? [{ id: 'staff', label: 'Admin Terminal', icon: ShieldCheck }] : []),
    ...((user?.can_upload ?? user?.is_sudo) ? [{ id: 'upload', label: 'Asset Intake', icon: CloudUpload }] : []),
  ];
  const sections = staffItems.length > 0
    ? [
        ...SECTIONS,
        {
          title: "SYSTEM",
          items: staffItems,
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
            className="fixed inset-0 z-[110] bg-black/90 backdrop-blur-md"
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 350 }}
            className="fixed top-0 right-0 z-[120] h-full w-[260px] sm:w-[320px] bg-[#050506] border-l border-white/[0.05] flex flex-col shadow-2xl"
          >
            {/* Header */}
            <div className="p-4 flex items-center justify-between border-b border-white/[0.04] bg-white/[0.01]">
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                    <Terminal size={12} className="text-brand-accent" />
                    <span className="text-[10px] font-black text-white tracking-[0.2em] uppercase">SYSTEM MENU</span>
                </div>
                <span className="text-[8px] font-bold text-neutral-600 uppercase tracking-widest mt-1">v2.2.0-AUTH_OK</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="w-8 h-8 p-0 rounded-md hover:bg-white/5"
                aria-label="Close"
              >
                <X size={16} />
              </Button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto px-2 py-4 space-y-6 scrollbar-hide">
              {sections.map((section) => (
                <div key={section.title} className="space-y-1">
                  <h3 className="px-3 py-2 text-[9px] font-black text-neutral-700 uppercase tracking-[0.3em]">
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
                            "group w-full flex items-center justify-between px-3 py-2.5 rounded-md transition-all duration-150 relative overflow-hidden",
                            isActive
                              ? "bg-brand-accent/10 text-brand-accent shadow-[inset_2px_0_0_rgba(59,130,246,1)]"
                              : "text-neutral-500 hover:text-white hover:bg-white/[0.03] active:scale-[0.98]"
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              "w-7 h-7 rounded-sm flex items-center justify-center transition-colors",
                              isActive ? "bg-brand-accent/20" : "bg-white/[0.02] border border-white/[0.03]"
                            )}>
                              <Icon size={14} strokeWidth={isActive ? 2.5 : 2} />
                            </div>
                            <span className={cn(
                              "text-[11px] font-bold tracking-widest uppercase",
                              isActive ? "text-brand-accent" : "text-neutral-400"
                            )}>
                              {item.label}
                            </span>
                          </div>

                          {isActive && (
                            <motion.div
                                layoutId="nav-active-indicator"
                                className="w-1 h-1 rounded-full bg-brand-accent shadow-[0_0_8px_rgba(59,130,246,0.6)]"
                            />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-white/[0.04] bg-white/[0.01]">
               <div className="flex items-center gap-3 p-2.5 rounded-lg bg-black border border-white/[0.03] mb-4">
                  <div className="w-8 h-8 rounded bg-brand-accent/10 flex items-center justify-center shrink-0 border border-brand-accent/20">
                    <ShieldCheck size={16} className="text-brand-accent" />
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-[9px] font-black text-white uppercase tracking-widest truncate">
                        {user?.role_label || user?.role_tag || 'MEMBER'} STATUS
                    </span>
                    <span className="text-[8px] font-bold text-neutral-600 uppercase tracking-tighter">AUTHENTICATED SESSION</span>
                  </div>
               </div>

               <div className="flex items-center justify-between px-1">
                  <div className="text-[8px] font-black text-neutral-800 uppercase tracking-[0.2em]">CONNECTION SECURE</div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-1 h-1 rounded-full bg-emerald-500" />
                    <span className="text-[8px] font-mono text-emerald-500/60 uppercase">9.1ms / SFO</span>
                  </div>
               </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
