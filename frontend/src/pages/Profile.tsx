import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useUser } from '../context/UserContext';
import { apiFetch } from '../api/client';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Card as CharacterCard } from '../components/character/Card';
import { Skeleton, CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Avatar } from '../components/Avatar';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import {
  BadgeCheck,
  BookOpen,
  CalendarCheck,
  ChevronDown,
  Coins,
  Crown,
  Egg,
  Gem,
  Loader2,
  PawPrint,
  Search,
  Ticket,
  Trophy,
  TrendingUp,
} from 'lucide-react';
import { cleanRarityLabel, formatNumber, cn } from '../utils';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';
import { Character } from '../context/UserContext';

interface ProfileProps {
  onCharClick: (character: Character) => void;
  focusCollection?: boolean;
}

const BentoTile = ({ children, className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <Card
    className={cn("p-4 flex flex-col justify-between group", className)}
    {...props}
  >
    {children}
  </Card>
);

export const Profile = ({ onCharClick, focusCollection = false }: ProfileProps) => {
  const { user, loading: userLoading } = useUser();
  const collectionRef = useRef<HTMLElement | null>(null);
  const {
    items,
    loading,
    page,
    search,
    setSearch,
    rarity,
    setRarity,
    lastElementRef,
    error,
    refresh
  } = useInfiniteGrid<Character>('/harem');
  
  const [availableRarities, setAvailableRarities] = useState<string[]>([]);
  const rarityOptions = useMemo(
    () => availableRarities.map((value) => ({ value, label: cleanRarityLabel(value) || value })),
    [availableRarities],
  );

  useEffect(() => {
    apiFetch('/rarities').then(setAvailableRarities).catch(console.error);
  }, []);

  useEffect(() => {
    window.addEventListener('harem-refresh', refresh);
    return () => window.removeEventListener('harem-refresh', refresh);
  }, [refresh]);

  useEffect(() => {
    if (!focusCollection || userLoading) return;

    const timeoutId = window.setTimeout(() => {
      collectionRef.current?.scrollIntoView({ block: 'start', behavior: 'smooth' });
    }, 150);

    return () => window.clearTimeout(timeoutId);
  }, [focusCollection, userLoading]);

  if (userLoading && items.length === 0) return (
    <div className="pb-24 pt-6 px-4 max-w-5xl mx-auto space-y-6">
       <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="md:col-span-2 h-40 rounded-2xl" />
          <Skeleton className="h-40 rounded-2xl" />
       </div>
       <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-24 rounded-2xl" />)}
       </div>
       <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3">
          {Array.from({ length: 12 }).map((_, i) => (
            <CardSkeleton key={`prof-skeleton-${i}`} />
          ))}
       </div>
    </div>
  );

  if (!user) return null;

  const stats = user.stats;
  const passType = stats?.pass_type || 'free';
  const passLabel = `${passType.charAt(0).toUpperCase()}${passType.slice(1)} PASS`;
  const collectionOwned = stats?.unique_characters ?? stats?.total_characters ?? 0;
  const collectionTotal = stats?.total_available_characters || Math.max(collectionOwned, 1);
  const collectionPercent = stats?.collection_percent ?? (
    collectionTotal > 0 ? Math.round((collectionOwned / collectionTotal) * 1000) / 10 : 0
  );
  const rankLabel = stats?.rank ? `#${formatNumber(stats.rank)}` : 'N/A';
  const percentileLabel = typeof stats?.percentile === 'number' && stats.percentile > 0
    ? `TOP ${stats.percentile}%`
    : 'UNRANKED';
  const currentTitle = user.titles?.current || 'ROOKIE';
  const activePet = user.current_pet;
  const usernameLabel = user.username ? `@${user.username}` : `ID ${user.id}`;

  return (
    <div className="pb-24 pt-6 max-w-5xl mx-auto adaptive-px space-y-8">
      {/* Bento Header Section */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* User Profile Tile */}
        <BentoTile className="md:col-span-2 md:flex-row items-center gap-6 p-6">
          <div className="relative shrink-0">
            <div className="absolute -inset-1 bg-gradient-to-tr from-brand-accent/40 to-purple-500/40 rounded-2xl blur-sm opacity-50" />
            <Avatar
              src={user.avatar}
              alt="User"
              className="w-24 h-24 rounded-2xl border-2 border-white/10 relative z-10"
            />
            <div className="absolute -bottom-2 -right-2 z-20 shadow-lg">
                <Badge variant="primary" className="px-2 py-1 rounded-lg border-2 border-brand-deep">
                    LVL {stats?.level || 1}
                </Badge>
            </div>
          </div>

          <div className="flex-1 text-center md:text-left space-y-3">
            <div>
                <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 mb-1">
                    <h1 className="text-2xl font-black text-white tracking-tight uppercase">
                        {user.first_name || 'Collector'}
                    </h1>
                    {user.role_tag && (
                        <Badge variant="primary" className="px-2 py-0.5 rounded-md">
                            {user.role_symbol} {user.role_label || user.role_tag}
                        </Badge>
                    )}
                </div>
                <p className="text-sm font-bold text-neutral-500 tracking-wider uppercase">{usernameLabel}</p>
            </div>

            <div className="flex flex-wrap items-center justify-center md:justify-start gap-2">
                <Badge variant="purple" icon={Crown} className="rounded-lg">
                    {currentTitle}
                </Badge>
                <Badge variant="secondary" icon={Ticket} className="rounded-lg">
                    {passLabel}
                </Badge>
            </div>

            <div className="pt-2 w-full max-w-sm mx-auto md:mx-0">
                <ProgressBar
                    current={stats?.xp_current || 0}
                    total={Math.max(1, stats?.xp_needed || 1000)}
                    label="XP PROGRESSION"
                    compact
                />
            </div>
          </div>
        </BentoTile>

        {/* Collection Stats Tile */}
        <BentoTile className="bg-gradient-to-br from-brand-deep to-brand-surface border-white/5 shadow-xl">
           <div className="flex items-center justify-between mb-4">
              <span className="text-[10px] font-black text-neutral-500 uppercase tracking-[0.2em]">Archive Status</span>
              <BookOpen size={16} className="text-purple-500" />
           </div>

           <div className="space-y-4">
              <div className="flex items-end justify-between">
                 <div className="text-3xl font-black text-white tabular-nums">
                    {collectionPercent}<span className="text-sm text-purple-500 ml-0.5">%</span>
                 </div>
                 <div className="text-right">
                    <div className="text-[10px] font-bold text-neutral-500 uppercase tracking-tighter">Characters</div>
                    <div className="text-xs font-black text-white tabular-nums">
                        {formatNumber(collectionOwned)} / {formatNumber(collectionTotal)}
                    </div>
                 </div>
              </div>
              <ProgressBar
                current={collectionOwned}
                total={collectionTotal}
                color="bg-purple-500"
                compact
              />
           </div>
        </BentoTile>
      </section>

      {/* Quick Stats Grid */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <BentoTile>
           <div className="flex items-center justify-between mb-3">
              <Coins size={18} className="text-amber-500" />
              <Badge variant="warning" size="xs">SHARDS</Badge>
           </div>
           <div className="text-xl font-black text-white tabular-nums">{formatNumber(stats?.points ?? user.balance ?? 0)}</div>
        </BentoTile>

        <BentoTile>
           <div className="flex items-center justify-between mb-3">
              <Gem size={18} className="text-brand-accent" />
              <Badge variant="primary" size="xs">ZENITH</Badge>
           </div>
           <div className="text-xl font-black text-white tabular-nums">{formatNumber(stats?.zenith || 0)}</div>
        </BentoTile>

        <BentoTile>
           <div className="flex items-center justify-between mb-3">
              <Trophy size={18} className="text-emerald-500" />
              <Badge variant="success" size="xs">RANK</Badge>
           </div>
           <div className="flex items-baseline gap-1.5">
              <span className="text-xl font-black text-white tabular-nums">{rankLabel}</span>
              <span className="text-[9px] font-bold text-neutral-500 uppercase">{percentileLabel}</span>
           </div>
        </BentoTile>

        <BentoTile>
           <div className="flex items-center justify-between mb-3">
              <CalendarCheck size={18} className="text-blue-400" />
              <Badge variant="secondary" size="xs">STREAK</Badge>
           </div>
           <div className="text-xl font-black text-white tabular-nums">{formatNumber(stats?.streak || 0)} <span className="text-xs text-neutral-500 font-bold uppercase ml-1">Days</span></div>
        </BentoTile>
      </section>

      {/* Companions & System Grid */}
      <section className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <BentoTile className="flex-row items-center gap-4 py-4">
           <div className="w-12 h-12 rounded-xl bg-brand-surface flex items-center justify-center shrink-0 border border-white/5">
              <PawPrint size={24} className="text-brand-accent" />
           </div>
           <div className="min-w-0 flex-1">
              <div className="text-[10px] font-black text-neutral-500 uppercase tracking-widest">Active Companion</div>
              <div className="text-sm font-black text-white truncate uppercase">{activePet?.name || 'None Selected'}</div>
           </div>
           {activePet && (
              <Badge variant="secondary" className="font-bold">LVL {activePet.level || 1}</Badge>
           )}
        </BentoTile>

        <BentoTile className="flex-row items-center gap-4 py-4">
           <div className="w-12 h-12 rounded-xl bg-brand-surface flex items-center justify-center shrink-0 border border-white/5">
              <Egg size={24} className="text-emerald-500" />
           </div>
           <div className="min-w-0 flex-1">
              <div className="text-[10px] font-black text-neutral-500 uppercase tracking-widest">Incubation Slots</div>
              <div className="text-sm font-black text-white truncate uppercase">{stats?.active_incubations || 0} / {stats?.incubation_slots || 1} ACTIVE</div>
           </div>
           <div className="w-8 h-8 rounded-full border-2 border-emerald-500/20 flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
           </div>
        </BentoTile>
      </section>

      {/* Character Collection Header */}
      <section ref={collectionRef} className="pt-4 space-y-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div className="space-y-1">
                <h2 className="text-2xl font-black text-white tracking-tighter uppercase">Character Archive</h2>
                <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Explore and manage your collection</p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
                <div className="w-full sm:w-64">
                    <Input
                        icon={Search}
                        placeholder="SEARCH ARCHIVE..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <div className="relative group">
                    <select
                        aria-label="Filter by rarity"
                        value={rarity}
                        onChange={(event) => setRarity(event.target.value)}
                        className="h-10 pl-4 pr-10 bg-brand-deep border border-white/10 rounded-xl text-xs font-black text-white uppercase tracking-widest outline-none focus:border-brand-accent transition-all appearance-none cursor-pointer"
                    >
                        <option value="">ALL RARITIES</option>
                        {rarityOptions.map(({ value, label }) => (
                            <option key={value} value={value}>{label.toUpperCase()}</option>
                        ))}
                    </select>
                    <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 pointer-events-none group-focus-within:text-brand-accent transition-colors" />
                </div>
            </div>
        </div>

        {error && items.length === 0 ? (
          <ErrorState message={error} onAction={refresh} />
        ) : items.length > 0 || (loading && page > 1) ? (
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3 sm:gap-4">
               {items.map((char, i) => (
                 <CharacterCard
                  key={char.id}
                  ref={i === items.length - 1 ? lastElementRef : null}
                  character={char}
                  onClick={onCharClick}
                 />
               ))}
             {loading && page > 1 && Array.from({ length: 6 }).map((_, i) => (
                <CardSkeleton key={`loading-${i}`} />
             ))}
          </div>
        ) : loading && page === 1 ? (
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3 sm:gap-4">
             {Array.from({ length: 18 }).map((_, i) => (
                <CardSkeleton key={`loading-new-${i}`} />
             ))}
          </div>
        ) : (
          <EmptyState
            icon={BookOpen}
            title="Archive Empty"
            message="Characters you collect will appear in your archive."
          />
        )}

        {loading && items.length > 0 && (
           <div className="flex justify-center py-12">
              <Loader2 className="animate-spin text-brand-accent/50" size={32} />
           </div>
        )}
      </section>
    </div>
  );
};
