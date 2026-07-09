import 'react';
import { Menu, Gem, Stamp } from 'lucide-react';
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
    <header className="sticky top-0 z-50 flex items-center justify-between px-4 bg-background/80 backdrop-blur-md h-16 shrink-0 select-none border-b border-white/5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-brand-deep border border-white/5 shadow-inner">
           <Stamp size={20} className="text-white" strokeWidth={2} />
        </div>
        <div className="flex flex-col">
          <span className="text-[11px] font-black text-white tracking-tighter uppercase leading-none">SEAL YOUR WAIFU</span>
          <div className="mt-1 flex items-center gap-1.5">
            {user?.role_tag && (
              <Badge variant="primary" size="xs">
                {user.role_symbol} {user.role_tag}
              </Badge>
            )}
            <span className="text-[9px] font-bold text-neutral-500 uppercase tracking-widest">BETA v2.1</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-deep border border-white/5 shadow-sm">
          <Gem size={14} className="text-brand-accent animate-pulse" />
          <span className="text-xs font-bold text-white tabular-nums">
            {formatNumber(user?.stats?.zenith || 0)}
          </span>
          <span className="hidden xs:inline text-[10px] font-bold text-neutral-500 uppercase tracking-tighter">Zenith</span>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
          className="w-10 h-10 p-0 rounded-xl"
          aria-label="Menu"
        >
          <Menu size={22} />
        </Button>
      </div>
    </header>
  );
};
