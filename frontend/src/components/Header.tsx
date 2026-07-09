import 'react';
import { Menu, Gem, Stamp, Zap, Heart } from 'lucide-react';
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
    <header className="sticky top-0 z-[100] flex items-center justify-between px-4 bg-background/80 backdrop-blur-xl h-14 shrink-0 select-none border-b border-white/[0.04]">
      {/* Brand Section */}
      <div className="flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-md bg-brand-surface border border-white/10 flex items-center justify-center relative overflow-hidden group">
           <Heart size={18} className="text-white relative z-10" fill="currentColor" />
           <div className="absolute inset-0 bg-brand-accent/10 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-black text-white tracking-[0.15em] uppercase leading-none">WAIFU PROTOCOL</span>
            <div className="w-1 h-1 rounded-full bg-brand-accent animate-pulse" />
          </div>
          <div className="mt-1 flex items-center gap-1">
            <span className="text-[8px] font-bold text-neutral-600 uppercase tracking-widest">SENSITIVE ASSETS</span>
            <span className="text-[8px] font-bold text-neutral-800 uppercase tracking-widest">•</span>
            <span className="text-[8px] font-bold text-brand-accent/60 uppercase tracking-widest">v2.2-STABLE</span>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="flex items-center gap-1.5">
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-white/[0.02] border border-white/[0.05] shadow-sm group hover:border-brand-accent/20 transition-colors">
          <Gem size={12} className="text-brand-accent group-hover:scale-110 transition-transform" />
          <span className="text-[11px] font-mono font-extrabold text-white tabular-nums tracking-tighter">
            {formatNumber(user?.stats?.zenith || 0)}
          </span>
          <div className="h-2 w-[1px] bg-white/10" />
          <span className="text-[8px] font-black text-neutral-500 uppercase tracking-widest">ZENITH</span>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
          className="w-9 h-9 p-0 rounded-md hover:bg-brand-accent/10 hover:text-brand-accent transition-all"
          aria-label="Open Menu"
        >
          <Menu size={20} strokeWidth={2.5} />
        </Button>
      </div>
    </header>
  );
};
