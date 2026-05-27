import React from 'react';
import { Menu, Activity } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { formatNumber } from '../utils';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header = ({ onMenuClick }: HeaderProps) => {
  const { user } = useUser();

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-4 bg-brand-midnight border-b border-white/5 h-14 shrink-0">
      <div className="flex items-center space-x-2">
        <div className="w-7 h-7 rounded-lg bg-brand-accent flex items-center justify-center">
           <span className="text-white font-black text-[10px]">G</span>
        </div>
        <span className="text-xs font-black uppercase tracking-[0.2em] text-white">Grabber</span>
      </div>

      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-1.5 bg-white/5 border border-white/5 px-2.5 py-1.5 rounded-xl">
          <Activity size={11} className="text-brand-accent" />
          <span className="text-[10px] font-black text-white tabular-nums tracking-wider">
            {formatNumber(user?.stats?.zenith || 0)}
          </span>
        </div>

        <button
          onClick={onMenuClick}
          className="p-2 rounded-xl bg-white/5 border border-white/5 text-slate-400 active:scale-95 transition-all"
        >
          <Menu size={18} />
        </button>
      </div>
    </header>
  );
};
