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
    <header className="sticky top-0 z-50 flex items-center justify-between px-4 bg-brand-midnight border-b border-white/5 h-14 shrink-0">
      <div className="flex items-center space-x-2.5">
        <div className="w-8 h-8 rounded-lg bg-zinc-900 border border-white/5 flex items-center justify-center shadow-sm">
           <Shield size={16} className="text-brand-accent" strokeWidth={2.5} />
        </div>
        <span className="text-sm font-bold tracking-tight text-white">Grabber</span>
      </div>

      <div className="flex items-center space-x-2">
        <div className="flex items-center space-x-1.5 bg-zinc-900 border border-white/5 px-2.5 py-1.5 rounded-md shadow-sm">
          <Activity size={12} className="text-brand-accent" />
          <span className="text-xs font-semibold text-zinc-100 tabular-nums">
            {formatNumber(user?.stats?.zenith || 0)}
          </span>
        </div>

        <button
          onClick={onMenuClick}
          className="p-2 rounded-md hover:bg-zinc-900 border border-transparent hover:border-white/5 text-zinc-400 active:bg-zinc-900 transition-colors"
        >
          <Menu size={20} />
        </button>
      </div>
    </header>
  );
};
