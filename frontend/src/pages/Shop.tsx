import React, { useEffect, useMemo, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { Card as CharacterCard } from '../components/character/Card';
import { Skeleton, CardSkeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { AlertCircle, CalendarDays, CheckCircle2, Clock, Coins, Gem, PackageOpen, RefreshCw, Store, Sparkles } from 'lucide-react';
import { Character, useUser } from '../context/UserContext';
import { formatNumber, cn } from '../utils';

interface ShopProps {
  onCharClick: (char: Character) => void;
  triggerRefresh?: () => void;
}

interface ShopHub {
  balance: number;
  zenith: number;
  pass_type: string;
  characters_rarity: string;
  rotation_date: string;
  reset_at: string;
}

const getStockRemaining = (character: Character) => {
  if (typeof character.stock_remaining === 'number') return Math.max(0, character.stock_remaining);
  if (typeof character.stock_limit === 'number' && typeof character.sold_count === 'number') {
    return Math.max(0, character.stock_limit - character.sold_count);
  }
  return null;
};

const isSoldOut = (character: Character) => {
  const remaining = getStockRemaining(character);
  return Boolean(character.sold_out) || (remaining !== null && remaining <= 0);
};

const getCountdown = (resetAt: string | undefined, now: number) => {
  if (!resetAt) return 'DAILY RESET';

  const resetTime = new Date(resetAt).getTime();
  if (!Number.isFinite(resetTime)) return 'DAILY RESET';

  const diff = Math.max(0, resetTime - now);
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (hours <= 0 && minutes <= 0) return 'RESET SOON';
  if (hours <= 0) return `${minutes}M`;
  return `${hours}H ${minutes}M`;
};

const Metric = ({
  icon: Icon,
  label,
  value,
  variant = 'secondary',
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  variant?: 'primary' | 'secondary' | 'warning' | 'success';
}) => (
  <Card variant="tactical" className="p-3 flex flex-col justify-between border-white/[0.03]">
    <div className="flex items-center gap-1.5 mb-1.5">
      <Icon
        size={11}
        className={cn(
          variant === 'primary' && 'text-brand-accent',
          variant === 'success' && 'text-emerald-500',
          variant === 'warning' && 'text-amber-500',
          variant === 'secondary' && 'text-neutral-600'
        )}
      />
      <span className="text-[8px] font-black text-neutral-600 uppercase tracking-[0.2em] truncate">{label}</span>
    </div>
    <p className="text-xs font-black text-white stats-value tabular-nums uppercase truncate">{value}</p>
  </Card>
);

export const Shop = ({ onCharClick, triggerRefresh }: ShopProps) => {
  const { user, refreshUser } = useUser();
  const { data: shopData, loading, error, execute: fetchShop } = useApi<Character[]>('/shop/characters');
  const { data: hubData, loading: hubLoading, error: hubError, execute: fetchHub } = useApi<ShopHub>('/shop/hub');
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const refreshShop = () => {
      fetchShop().catch(() => undefined);
      fetchHub().catch(() => undefined);
      refreshUser().catch(() => undefined);
    };

    window.addEventListener('shop-refresh', refreshShop);
    return () => window.removeEventListener('shop-refresh', refreshShop);
  }, [fetchHub, fetchShop, refreshUser]);

  const zenithBalance = Number(hubData?.zenith ?? user?.stats?.zenith ?? user?.zenith ?? 0);
  const shardBalance = Number(hubData?.balance ?? user?.balance ?? 0);

  const inventory = useMemo(() => {
    const ownedIds = new Set((user?.characters || []).map((char) => String(char.id)));

    return (shopData || [])
      .map((char) => {
        const owned = char.owned || ownedIds.has(String(char.id));
        const stockRemaining = getStockRemaining(char);
        const soldOut = isSoldOut(char);

        return {
          ...char,
          owned,
          stock_remaining: stockRemaining ?? char.stock_remaining,
          sold_out: soldOut,
        };
      })
      .sort((a, b) => {
        const rank = (char: Character) => {
          if (char.owned) return 3;
          if (isSoldOut(char)) return 4;
          if (Number(char.zenith_price || 0) <= zenithBalance) return 1;
          return 2;
        };

        const rankDiff = rank(a) - rank(b);
        if (rankDiff !== 0) return rankDiff;
        return Number(a.zenith_price || 0) - Number(b.zenith_price || 0);
      });
  }, [shopData, user?.characters, zenithBalance]);

  const summary = useMemo(() => {
    const owned = inventory.filter((char) => char.owned).length;
    const available = inventory.filter((char) => !char.owned && !isSoldOut(char)).length;
    const affordable = inventory.filter((char) => !char.owned && !isSoldOut(char) && Number(char.zenith_price || 0) <= zenithBalance).length;
    const soldOut = inventory.filter((char) => !char.owned && isSoldOut(char)).length;

    return { owned, available, affordable, soldOut };
  }, [inventory, zenithBalance]);

  const handleRefresh = async () => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    await Promise.allSettled([fetchShop(), fetchHub(), refreshUser()]);
    if (triggerRefresh) triggerRefresh();
  };

  if (loading && !shopData) return (
    <div className="pb-24 pt-4 max-w-5xl mx-auto adaptive-px">
       <div className="space-y-4">
          <div className="flex flex-col gap-1.5">
             <Skeleton className="h-6 w-40 rounded-md" />
             <Skeleton className="h-3 w-56 rounded-md" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
             {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-14 rounded-lg" />)}
          </div>
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-6 gap-2.5">
             {Array.from({ length: 12 }).map((_, i) => <CardSkeleton key={i} />)}
          </div>
       </div>
    </div>
  );

  if (error && !shopData) return (
    <div className="px-4 py-12 max-w-2xl mx-auto">
      <ErrorState message={error} onAction={handleRefresh} />
    </div>
  );

  return (
    <div className="pb-24 pt-4 max-w-5xl mx-auto adaptive-px space-y-6">
      <header className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-md bg-brand-accent/5 border border-brand-accent/20 flex items-center justify-center">
                 <Store size={20} className="text-brand-accent" />
              </div>
              <h1 className="text-lg font-black text-white tracking-tighter uppercase">Gacha Market</h1>
            </div>
            <p className="text-[10px] font-bold text-neutral-600 uppercase tracking-widest max-w-xs leading-relaxed">
              SUMMON NEW WAIFUS. SHARED GLOBAL STOCK.
            </p>
          </div>

          <Button
            variant="secondary"
            onClick={handleRefresh}
            isLoading={loading || hubLoading}
            className="w-9 h-9 p-0 rounded-md border-white/5"
            aria-label="Refresh market"
          >
            <RefreshCw size={16} className={loading || hubLoading ? 'animate-spin' : ''} />
          </Button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
          <Metric icon={Coins} label="Credit Shards" value={formatNumber(shardBalance)} variant="warning" />
          <Metric icon={Gem} label="Zenith Assets" value={formatNumber(zenithBalance)} variant="primary" />
          <Metric icon={Clock} label="Next Rotation" value={getCountdown(hubData?.reset_at, now)} variant="secondary" />
          <Metric icon={PackageOpen} label="In Stock" value={`${summary.available} UNITS`} variant="success" />
          <Metric icon={CheckCircle2} label="Secured" value={`${summary.owned} OWNED`} variant="secondary" />
        </div>

        {(error || hubError) && shopData && (
          <Badge variant="warning" icon={AlertCircle} size="xs" className="w-full py-2 rounded-md justify-center border-amber-500/10">
            CONNECTION UNSTABLE: DISPLAYING CACHED MARKET DATA
          </Badge>
        )}
      </header>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3 border-b border-white/[0.03] pb-2">
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-brand-accent" />
            <h2 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Current Summon List</h2>
          </div>
          <Badge variant="tactical" size="xs" className="opacity-60">
            {summary.affordable} AFFORDABLE
          </Badge>
        </div>

        {inventory.length > 0 ? (
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2.5 sm:gap-3">
            {inventory.map((char) => (
              <CharacterCard key={char.id} character={char} onClick={() => onCharClick(char)} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Store}
            title="Market Closed"
            message="No waifus available in the current rotation."
          />
        )}
      </section>
    </div>
  );
};
