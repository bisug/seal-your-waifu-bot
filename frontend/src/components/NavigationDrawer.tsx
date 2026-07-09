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
    title: "Account",
    items: [
      { id: 'profile', label: 'Dashboard', icon: UserRound },
      { id: 'mypets', label: 'My Companions', icon: PawPrint },
      { id: 'incubation', label: 'Incubator', icon: Egg },
      { id: 'achievements', label: 'Milestones', icon: BadgeCheck },
    ]
  },
  {
    title: "Market",
    items: [
      { id: 'shop', label: 'Daily Market', icon: Store },
      { id: 'exchange', label: 'Currency', icon: Repeat2 },
      { id: 'gallery', label: 'Character Archive', icon: BookOpen },
      { id: 'pets', label: 'Pet Breeder', icon: Bone },
    ]
  },
  {
    title: "Activity",
    items: [
      { id: 'referrals', label: 'Invite Friends', icon: UserPlus },
      { id: 'quests', label: 'Daily Tasks', icon: ListChecks },
      { id: 'pass', label: 'Battle Pass', icon: Ticket },
      { id: 'leaderboard', label: 'Global Ranking', icon: ChartNoAxesColumnIncreasing },
    ]
  }
];

export const NavigationDrawer = ({ isOpen, onClose, activeTab, onNavigate }: NavigationDrawerProps) => {
  const { user } = useUser();
  const staffItems = [
    ...(user?.is_sudo ? [{ id: 'staff', label: 'Admin Panel', icon: ShieldCheck }] : []),
    ...((user?.can_upload ?? user?.is_sudo) ? [{ id: 'upload', label: 'Creator Hub', icon: CloudUpload }] : []),
  ];
  const sections = staffItems.length > 0
    ? [
        ...SECTIONS,
        {
          title: "System",
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
            className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-sm"
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-0 right-0 z-[70] h-full w-[280px] sm:w-[340px] bg-brand-midnight border-l border-white/5 flex flex-col shadow-2xl"
          >
            <div className="p-5 flex items-center justify-between border-b border-white/5 bg-brand-deep/50">
              <div className="flex flex-col">
                <span className="text-sm font-black text-white tracking-tight uppercase">Menu Navigation</span>
                <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mt-0.5">Explore the seal</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="w-9 h-9 p-0 rounded-lg hover:bg-white/10"
                aria-label="Close Menu"
              >
                <X size={18} />
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-8 scrollbar-hide">
              {sections.map((section) => (
                <div key={section.title} className="space-y-3">
                  <h3 className="px-3 text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em]">
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
                            "group w-full flex items-center justify-between px-3 py-3 rounded-xl transition-all duration-200",
                            isActive
                              ? "bg-brand-accent/10 text-brand-accent ring-1 ring-brand-accent/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                              : "text-neutral-400 hover:text-white hover:bg-white/5 active:scale-[0.98]"
                          )}
                        >
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              "w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
                              isActive ? "bg-brand-accent/20" : "bg-brand-surface group-hover:bg-brand-surface/80"
                            )}>
                              <Icon size={16} strokeWidth={isActive ? 2.5 : 2} />
                            </div>
                            <span className={cn(
                              "text-sm font-bold tracking-tight",
                              isActive ? "text-brand-accent" : "text-neutral-300"
                            )}>
                              {item.label}
                            </span>
                          </div>
                          {isActive && <div className="w-1.5 h-1.5 rounded-full bg-brand-accent shadow-[0_0_8px_rgba(59,130,246,0.5)]" />}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-6 border-t border-white/5 bg-brand-deep/30">
               {user?.role_tag && (
                 <div className="mb-4">
                   <Badge variant="primary" className="w-full py-2.5 justify-center rounded-xl text-[11px] uppercase tracking-widest border-brand-accent/30 bg-brand-accent/5">
                     {user.role_symbol} {user.role_label || user.role_tag} MEMBER
                   </Badge>
                 </div>
               )}
               <div className="flex items-center justify-between px-1">
                  <div className="text-[10px] font-black text-neutral-600 uppercase tracking-tighter">System Stability</div>
                  <div className="text-[10px] font-mono text-emerald-500 uppercase">99.9% / v2.1</div>
               </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
