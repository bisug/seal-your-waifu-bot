import 'react';
import { Menu, Gem, User } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { formatNumber } from '../utils';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header = ({ onMenuClick }: HeaderProps) => {
  const { user } = useUser();

  return (
    <header className="sticky top-0 z-[100] flex items-center justify-between px-5 bg-background/60 backdrop-blur-2xl h-16 shrink-0 select-none border-b border-white/[0.04]">
      {/* Brand Section */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-brand-surface border border-white/10 flex items-center justify-center relative overflow-hidden group shadow-inner">
           <User size={20} className="text-white relative z-10 transition-transform group-hover:scale-110" />
           <div className="absolute inset-0 bg-brand-accent/5 opacity-0 group-hover:opacity-100 transition-opacity" />
           <div className="absolute inset-0 bg-gradient-to-br from-white/[0.05] to-transparent pointer-events-none" />
        </div>
        <div className="flex flex-col justify-center">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-black text-white tracking-[0.2em] uppercase leading-none">PROTOCOL</span>
            <Badge variant="tactical" size="xs" className="px-1 py-0 opacity-40">v2.4</Badge>
          </div>
          <div className="mt-1.5 flex items-center gap-1.5">
            <div className="w-1 h-1 rounded-full bg-success shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            <span className="text-[8px] font-bold text-neutral-600 uppercase tracking-widest leading-none">SYSTEM_READY</span>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:border-brand-accent/30 transition-all duration-300 group">
          <Gem size={13} className="text-brand-accent transition-transform group-hover:scale-110" />
          <div className="flex flex-col items-start leading-none gap-0.5">
             <span className="text-[12px] font-mono font-extrabold text-white tabular-nums tracking-tight">
                {formatNumber(user?.stats?.zenith || 0)}
             </span>
             <span className="text-[7px] font-black text-neutral-600 uppercase tracking-widest">ZENITH</span>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
          className="w-10 h-10 p-0 rounded-xl bg-white/[0.02] border border-white/[0.05] hover:bg-brand-accent/10 hover:text-brand-accent transition-all"
          aria-label="Open Menu"
        >
          <Menu size={20} strokeWidth={2.5} />
        </Button>
      </div>
    </header>
  );
};
