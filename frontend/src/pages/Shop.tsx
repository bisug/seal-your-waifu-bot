import React, { useEffect, useMemo, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { Card } from '../components/character/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { EmptyState } from '../components/ui/EmptyState';
import { AlertCircle, CheckCircle2, Clock, Coins, Gem, Package, RefreshCw, ShoppingBag, Sparkles } from 'lucide-react';
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
  if (!resetAt) return 'Daily reset';

  const resetTime = new Date(resetAt).getTime();
  if (!Number.isFinite(resetTime)) return 'Daily reset';

  const diff = Math.max(0, resetTime - now);
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (hours <= 0 && minutes <= 0) return 'Reset soon';
  if (hours <= 0) return `${minutes}m`;
  return `${hours}h ${minutes}m`;
};

const Metric = ({
  icon: Icon,
  label,
  value,
  tone = 'neutral',
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  tone?: 'neutral' | 'accent' | 'success';
}) => (
  <div className="min-w-0 rounded-lg border border-white/5 bg-brand-deep px-3 py-2.5">
    <div className="flex items-center gap-1.5 text-[10px] font-semibold text-neutral-500">
      <Icon
        size={12}
        className={cn(
          tone === 'accent' && 'text-brand-accent',
          tone === 'success' && 'text-emerald-400',
          tone === 'neutral' && 'text-neutral-600'
        )}
      />
      <span className="truncate">{label}</span>
    </div>
    <p className="mt-1 truncate text-sm font-bold text-white tabular-nums">{value}</p>
  </div>
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
    <div className="pb-20 pt-4 max-w-5xl mx-auto">
      <div className="px-4 pb-5 mb-5 border-b border-white/5">
        <div className="h-5 w-32 rounded bg-white/5 mb-3" />
        <div className="h-4 w-56 rounded bg-white/5" />
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 rounded-lg bg-white/5" />
          ))}
        </div>
      </div>
      <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3 px-4">
        {Array.from({ length: 12 }).map((_, i) => <CardSkeleton key={i} />)}
      </div>
    </div>
  );

  if (error && !shopData) return (
    <div className="px-4 py-8 max-w-2xl mx-auto">
      <ErrorState message={error} onAction={handleRefresh} />
    </div>
  );

  return (
    <div className="pb-20 pt-4 max-w-5xl mx-auto">
      <header className="px-4 pb-5 mb-5 border-b border-white/5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <ShoppingBag size={18} className="text-brand-accent shrink-0" />
              <h1 className="text-lg font-bold text-white tracking-tight">Daily Shop</h1>
            </div>
            <p className="text-sm font-medium text-neutral-400 leading-snug">
              A limited character rotation with shared stock and live ownership checks.
            </p>
          </div>

          <button
            onClick={handleRefresh}
            disabled={loading || hubLoading}
            className="p-2.5 rounded-lg bg-brand-deep border border-white/5 text-neutral-400 hover:text-white hover:bg-white/5 disabled:opacity-60 transition-colors active:scale-95 shrink-0"
            aria-label="Refresh shop"
          >
            <RefreshCw size={16} className={loading || hubLoading ? 'animate-spin' : ''} />
          </button>
        </div>

        <div className="mt-4 grid grid-cols-2 sm:grid-cols-5 gap-2">
          <Metric icon={Coins} label="Shards" value={formatNumber(shardBalance)} />
          <Metric icon={Gem} label="Zenith" value={formatNumber(zenithBalance)} tone="accent" />
          <Metric icon={Clock} label="Resets in" value={getCountdown(hubData?.reset_at, now)} />
          <Metric icon={Package} label="Available" value={summary.available} tone="success" />
          <Metric icon={CheckCircle2} label="Owned" value={summary.owned} />
        </div>

        {(error || hubError) && shopData && (
          <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-500/15 bg-amber-500/10 px-3 py-2 text-xs font-medium text-amber-200">
            <AlertCircle size={14} className="mt-0.5 shrink-0" />
            <span>Showing the latest loaded shop data. Refresh again if stock looks out of date.</span>
          </div>
        )}
      </header>

      <section className="px-4">
        <div className="mb-3 flex items-end justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Sparkles size={15} className="text-brand-accent" />
              <h2 className="text-sm font-bold text-white">Today's rotation</h2>
            </div>
            <p className="mt-1 text-xs font-medium text-neutral-500">
              {summary.affordable} affordable, {summary.soldOut} sold out
            </p>
          </div>
        </div>

        {inventory.length > 0 ? (
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3">
            {inventory.map((char) => (
              <Card key={char.id} character={char} onClick={() => onCharClick(char)} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={ShoppingBag}
            title="Shop is empty"
            message="The daily rotation could not find characters right now. Refresh or check back later."
          />
        )}
      </section>
    </div>
  );
};
