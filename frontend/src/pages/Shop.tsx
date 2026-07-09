import React, { useEffect, useMemo, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { Card as CharacterCard } from '../components/character/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { EmptyState } from '../components/ui/EmptyState';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { AlertCircle, CalendarDays, CheckCircle2, Clock, Coins, Gem, PackageOpen, RefreshCw, Store } from 'lucide-react';
import { Character, useUser } from '../context/UserContext';
import { cn, formatNumber } from '../utils';

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
  <Card className="p-3 flex flex-col justify-between">
    <div className="flex items-center gap-1.5 mb-2">
      <Icon
        size={12}
        className={cn(
          variant === 'primary' && 'text-brand-accent',
          variant === 'success' && 'text-emerald-500',
          variant === 'warning' && 'text-amber-500',
          variant === 'secondary' && 'text-neutral-500'
        )}
      />
      <span className="text-[9px] font-black text-neutral-500 uppercase tracking-widest truncate">{label}</span>
    </div>
    <p className="text-sm font-black text-white tabular-nums uppercase truncate">{value}</p>
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
    <div className="pb-24 pt-6 max-w-5xl mx-auto adaptive-px">
       <div className="space-y-6">
          <div className="flex flex-col gap-2">
             <Skeleton className="h-8 w-48 rounded-lg" />
             <Skeleton className="h-4 w-64 rounded-lg" />
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
             {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-16 rounded-xl" />)}
          </div>
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-6 gap-3">
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
    <div className="pb-24 pt-6 max-w-5xl mx-auto adaptive-px space-y-8">
      <header className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                 <Store size={22} className="text-brand-accent" />
              </div>
              <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Daily Market</h1>
            </div>
            <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest max-w-lg">
              SHARED GLOBAL STOCK WITH LIVE ROTATION. SECURE YOUR WAIFUS BEFORE THEY'RE GONE.
            </p>
          </div>

          <Button
            variant="secondary"
            onClick={handleRefresh}
            isLoading={loading || hubLoading}
            className="w-12 h-12 p-0 rounded-xl border-white/5"
            aria-label="Refresh shop"
          >
            <RefreshCw size={18} className={loading || hubLoading ? 'animate-spin' : ''} />
          </Button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <Metric icon={Coins} label="Shards" value={formatNumber(shardBalance)} variant="warning" />
          <Metric icon={Gem} label="Zenith" value={formatNumber(zenithBalance)} variant="primary" />
          <Metric icon={Clock} label="Rotation" value={getCountdown(hubData?.reset_at, now)} variant="secondary" />
          <Metric icon={PackageOpen} label="Stock" value={`${summary.available} AVAIL`} variant="success" />
          <Metric icon={CheckCircle2} label="Secured" value={`${summary.owned} OWNED`} variant="secondary" />
        </div>

        {(error || hubError) && shopData && (
          <Badge variant="warning" icon={AlertCircle} className="w-full py-2 rounded-xl justify-center">
            OFFLINE MODE: DATA MAY BE STALE. REFRESH TO SYNC.
          </Badge>
        )}
      </header>

      <section className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <CalendarDays size={18} className="text-brand-accent" />
            <h2 className="text-sm font-black text-white uppercase tracking-widest">Active Rotation</h2>
          </div>
          <span className="text-[10px] font-black text-neutral-500 uppercase tracking-widest bg-brand-deep px-2 py-1 rounded-lg">
            {summary.affordable} AFFORDABLE
          </span>
        </div>

        {inventory.length > 0 ? (
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3 sm:gap-4">
            {inventory.map((char) => (
              <CharacterCard key={char.id} character={char} onClick={() => onCharClick(char)} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Store}
            title="Market Closed"
            message="No characters available in the current rotation. Check back soon."
          />
        )}
      </section>
    </div>
  );
};
