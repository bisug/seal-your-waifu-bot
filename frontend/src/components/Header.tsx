import React from 'react';
import { Menu, Activity, Shield } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { formatNumber } from '../utils';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header = ({ onMenuClick }: HeaderProps) => {
  const { user } = useUser();

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-4 bg-zinc-950/80 backdrop-blur-md border-b border-white/5 h-14 shrink-0 select-none">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-white/10 flex items-center justify-center">
           <Shield size={16} className="text-white" strokeWidth={2.5} />
        </div>
        <span className="text-[11px] font-black uppercase tracking-[0.2em] text-white">Grabber</span>
      </div>

      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-2 bg-zinc-900 border border-white/5 px-3 py-1.5 rounded-lg">
          <Activity size={12} className="text-brand-accent" />
          <span className="text-[10px] font-bold text-white tabular-nums tracking-wider">
            {formatNumber(user?.stats?.zenith || 0)}
          </span>
        </div>

        <button
          onClick={onMenuClick}
          className="p-2 rounded-lg bg-zinc-900 border border-white/5 text-zinc-400 active:scale-95 transition-all"
        >
          <Menu size={18} />
        </button>
      </div>
    </header>
  );
};
