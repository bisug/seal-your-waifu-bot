import { useEffect } from 'react';
import {
  X,
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
  Heart,
  Settings,
  HelpCircle,
  LogOut,
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
      { id: 'mypets', label: 'Companions', icon: PawPrint },
      { id: 'achievements', label: 'Milestones', icon: BadgeCheck },
      { id: 'exchange', label: 'Currency', icon: Repeat2 },
    ]
  },
  {
    title: "SOCIAL",
    items: [
      { id: 'referrals', label: 'Recruit', icon: UserPlus },
      { id: 'quests', label: 'Daily Tasks', icon: ListChecks },
      { id: 'pass', label: 'Waifu Pass', icon: Ticket },
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
            className="fixed inset-0 z-[110] bg-black/80 backdrop-blur-sm"
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed top-0 right-0 z-[120] h-full w-[280px] bg-[#050506] border-l border-white/[0.05] flex flex-col shadow-2xl"
          >
            {/* Header */}
            <div className="p-6 flex items-center justify-between border-b border-white/[0.04]">
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                    <Terminal size={14} className="text-brand-accent" />
                    <span className="text-[11px] font-black text-white tracking-[0.2em] uppercase">SYSTEM</span>
                </div>
                <span className="text-[8px] font-bold text-neutral-600 uppercase tracking-widest mt-1">PROTO_v2.4_READY</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="w-9 h-9 p-0 rounded-xl bg-white/[0.02] border border-white/[0.05]"
                aria-label="Close"
              >
                <X size={18} />
              </Button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto px-3 py-6 space-y-8 scrollbar-hide">
              {sections.map((section) => (
                <div key={section.title} className="space-y-2">
                  <h3 className="px-4 text-[9px] font-black text-neutral-700 uppercase tracking-[0.3em]">
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
                            "group w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300 relative overflow-hidden",
                            isActive
                              ? "bg-brand-accent/10 text-brand-accent shadow-[inset_3px_0_0_rgba(59,130,246,1)]"
                              : "text-neutral-500 hover:text-white hover:bg-white/[0.03]"
                          )}
                        >
                          <div className="flex items-center gap-4">
                            <Icon size={16} strokeWidth={isActive ? 2.5 : 2} className={isActive ? "text-brand-accent" : "text-neutral-600 group-hover:text-neutral-300"} />
                            <span className={cn(
                              "text-[11px] font-bold tracking-widest uppercase",
                              isActive ? "text-brand-accent" : "text-neutral-500 group-hover:text-neutral-300"
                            )}>
                              {item.label}
                            </span>
                          </div>

                          {isActive && (
                            <div className="w-1 h-1 rounded-full bg-brand-accent shadow-[0_0_8px_rgba(59,130,246,0.6)]" />
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}

              {/* Secondary Actions */}
              <div className="space-y-2 pt-4">
                  <h3 className="px-4 text-[9px] font-black text-neutral-700 uppercase tracking-[0.3em]">PREFERENCES</h3>
                  <div className="space-y-1">
                      {[
                          { icon: Settings, label: 'Settings' },
                          { icon: HelpCircle, label: 'Support' },
                          { icon: LogOut, label: 'Disconnect' },
                      ].map((item) => (
                          <button key={item.label} className="w-full flex items-center gap-4 px-4 py-3 text-neutral-600 hover:text-neutral-300 transition-colors">
                              <item.icon size={16} />
                              <span className="text-[11px] font-bold tracking-widest uppercase">{item.label}</span>
                          </button>
                      ))}
                  </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-white/[0.04] bg-white/[0.01]">
               <div className="flex items-center gap-4 p-3 rounded-xl bg-black border border-white/[0.03] mb-5">
                  <div className="w-10 h-10 rounded-lg bg-brand-accent/10 flex items-center justify-center shrink-0 border border-brand-accent/20">
                    <Heart size={18} className="text-brand-accent" fill="currentColor" />
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-[10px] font-black text-white uppercase tracking-widest truncate">
                        {user?.role_label || user?.role_tag || 'OPERATOR'}
                    </span>
                    <span className="text-[8px] font-bold text-neutral-600 uppercase tracking-tighter">SECURE ACCESS GRANTED</span>
                  </div>
               </div>

               <div className="flex items-center justify-between px-1">
                  <div className="text-[8px] font-black text-neutral-800 uppercase tracking-[0.2em]">NODE_STATUS</div>
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                    <span className="text-[8px] font-mono text-success/60 uppercase">ONLINE</span>
                  </div>
               </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
