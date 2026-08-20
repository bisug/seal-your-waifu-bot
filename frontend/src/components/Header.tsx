import { memo } from 'react';
import { Coins, Gem, Menu } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { formatNumber } from '../utils';
import { Avatar } from './Avatar';
import { Button } from './ui/Button';

interface HeaderProps {
  onMenuClick: () => void;
}

export const Header = memo(({ onMenuClick }: HeaderProps) => {
  const { user, loading } = useUser();

  return (
    <header className="sticky top-0 z-[100] flex items-center justify-between px-5 bg-zinc-950/95 h-14 shrink-0 select-none border-b border-white/[0.04]">
      {/* Brand Section */}
      <div className="flex items-center gap-3">
        <Avatar
          src={user?.avatar}
          alt={user?.username || 'User avatar'}
          fallbackText={user?.first_name?.[0] || user?.username?.[0]}
          className="w-8 h-8 rounded-md border border-white/5"
        />
        <div className="flex flex-col justify-center">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-black text-zinc-100 tracking-wider uppercase leading-none">
              SEAL
            </span>
            <span className="text-[8px] font-mono text-zinc-500 uppercase">V2.4</span>
          </div>
          <div className="flex items-center gap-1 mt-0.5">
            <div className="w-1 h-1 rounded-full bg-emerald-500" />
            <span className="text-[8px] font-bold text-zinc-500 uppercase tracking-widest leading-none">
              READY
            </span>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="flex items-center gap-1.5 sm:gap-2">
        <div className="flex items-center gap-1.5 sm:gap-2.5 px-2.5 sm:px-3 h-8 rounded-md bg-zinc-900 border border-white/5 transition-colors hover:border-white/10 group">
          <Coins size={12} className="text-amber-500 shrink-0" />
          <div className="flex items-baseline gap-1">
            <span className="text-[11px] font-mono font-bold text-zinc-100 tabular-nums">
              {loading ? (
                <span className="inline-block w-8 h-3 rounded-sm bg-zinc-800 animate-pulse align-middle" />
              ) : (
                formatNumber(user?.stats?.points ?? user?.balance ?? 0)
              )}
            </span>
            <span className="hidden sm:inline text-[8px] font-bold text-zinc-500 uppercase tracking-wider">
              SHARDS
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2.5 px-2.5 sm:px-3 h-8 rounded-md bg-zinc-900 border border-white/5 transition-colors hover:border-white/10 group">
          <Gem size={12} className="text-brand-accent shrink-0" />
          <div className="flex items-baseline gap-1">
            <span className="text-[11px] font-mono font-bold text-zinc-100 tabular-nums">
              {loading ? (
                <span className="inline-block w-8 h-3 rounded-sm bg-zinc-800 animate-pulse align-middle" />
              ) : (
                formatNumber(user?.stats?.zenith || 0)
              )}
            </span>
            <span className="hidden sm:inline text-[8px] font-bold text-zinc-500 uppercase tracking-wider">
              ZENITH
            </span>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
          className="w-9 h-9 p-0 rounded-md border border-white/5 hover:bg-zinc-900 transition-all shrink-0"
          aria-label="Open Menu"
        >
          <Menu size={18} />
        </Button>
      </div>
    </header>
  );
});
