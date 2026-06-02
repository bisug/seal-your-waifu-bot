import React from 'react';
import { Menu, Gem, Shield } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { formatNumber } from '../utils';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header = ({ onMenuClick }: HeaderProps) => {
  const { user } = useUser();

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-4 bg-brand-midnight h-14 shrink-0 select-none border-b border-white/5">
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-brand-deep">
           <Shield size={16} className="text-white" strokeWidth={2} />
        </div>
        <span className="text-sm font-semibold tracking-tight text-white">Seal</span>
      </div>

      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-brand-deep">
          <Gem size={14} className="text-brand-accent" />
          <span className="text-xs font-semibold text-white tabular-nums">
            {formatNumber(user?.stats?.zenith || 0)}
          </span>
          <span className="text-[10px] font-semibold text-neutral-500">Zenith</span>
        </div>

        <button
          onClick={onMenuClick}
          className="p-2 -mr-2 rounded-lg text-neutral-400 hover:text-white hover:bg-white/5 active:scale-95 transition-all"
          aria-label="Menu"
        >
          <Menu size={20} />
        </button>
      </div>
    </header>
  );
};
