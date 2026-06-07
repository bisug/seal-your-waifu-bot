import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useUser } from '../context/UserContext';
import { apiFetch } from '../api/client';
import { ProgressBar } from '../components/ui/ProgressBar';
import { Card } from '../components/character/Card';
import { Skeleton, CardSkeleton } from '../components/ui/Skeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { Avatar } from '../components/Avatar';
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

const statTone = {
  neutral: 'text-neutral-500',
  accent: 'text-brand-accent',
  success: 'text-emerald-500',
  warning: 'text-amber-500',
  purple: 'text-purple-500',
};

interface StatTileProps {
  icon: React.ElementType;
  label: string;
  value: React.ReactNode;
  detail?: string;
  tone?: keyof typeof statTone;
}

const StatTile = ({ icon: Icon, label, value, detail, tone = 'neutral' }: StatTileProps) => (
  <div className="min-w-0 rounded-lg border border-white/5 bg-brand-deep p-3 shadow-sm">
    <div className="mb-2 flex items-center justify-between gap-2">
      <span className="truncate text-[10px] font-semibold text-neutral-500">{label}</span>
      <Icon size={15} className={cn('shrink-0', statTone[tone])} />
    </div>
    <p className="truncate text-base font-bold text-white tabular-nums">{value}</p>
    {detail && <p className="mt-1 truncate text-[11px] font-medium text-neutral-500">{detail}</p>}
  </div>
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
      collectionRef.current?.scrollIntoView({ block: 'start' });
    }, 80);

    return () => window.clearTimeout(timeoutId);
  }, [focusCollection, userLoading]);

  if (userLoading && items.length === 0) return (
    <div className="pb-24 pt-6 px-4">
       <div className="h-28 mb-6">
          <Skeleton className="w-full h-full rounded-2xl" />
       </div>
       <div className="grid grid-cols-3 gap-3 mb-6">
          {[1,2,3].map(i => <Skeleton key={i} className="h-20 rounded-xl" />)}
       </div>
       <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 gap-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <CardSkeleton key={`prof-skeleton-${i}`} />
          ))}
       </div>
    </div>
  );

  if (!user) return null;

  const uploadReward = user.upload_reward
    ? [
        user.upload_reward.balance ? `${formatNumber(user.upload_reward.balance)} Shards` : '',
        user.upload_reward.zenith ? `${formatNumber(user.upload_reward.zenith)} Zenith` : '',
      ].filter(Boolean).join(' + ')
    : '';
  const roleBenefits = user.role_benefits || [];
  const stats = user.stats;
  const passType = stats?.pass_type || 'free';
  const passLabel = `${passType.charAt(0).toUpperCase()}${passType.slice(1)} Pass`;
  const collectionOwned = stats?.unique_characters ?? stats?.total_characters ?? 0;
  const collectionTotal = stats?.total_available_characters || Math.max(collectionOwned, 1);
  const collectionPercent = stats?.collection_percent ?? (
    collectionTotal > 0 ? Math.round((collectionOwned / collectionTotal) * 1000) / 10 : 0
  );
  const totalCopies = stats?.total_characters || 0;
  const shardBalance = stats?.points ?? user.balance ?? 0;
  const rankLabel = stats?.rank ? `#${formatNumber(stats.rank)}` : 'Unranked';
  const percentileLabel = typeof stats?.percentile === 'number' && stats.percentile > 0
    ? `Top ${stats.percentile}%`
    : undefined;
  const currentTitle = user.titles?.current || 'Rookie';
  const achievementCount = user.achievements?.length || 0;
  const activePet = user.current_pet;
  const petDetail = activePet
    ? `Lvl ${activePet.level || 1} / ${activePet.mood || 'Neutral'}`
    : 'Select one in My Pets';
  const activeIncubations = stats?.active_incubations || 0;
  const incubationSlots = stats?.incubation_slots || 1;
  const usernameLabel = user.username ? `@${user.username}` : `ID ${user.id}`;

  return (
    <div className="pb-20 pt-4 max-w-5xl mx-auto">
      <section className="px-4 mb-4">
        <div className="rounded-lg border border-white/5 bg-brand-deep p-4 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="relative shrink-0">
              <Avatar
                src={user.avatar}
                alt="User"
                className="w-16 h-16 rounded-lg border border-white/10"
              />
              <div className="absolute -bottom-2 -right-2 rounded-lg border-2 border-brand-deep bg-brand-accent px-2 py-0.5 text-xs font-bold text-white">
                Lvl {stats?.level || 1}
              </div>
            </div>

            <div className="min-w-0 flex-1">
              <div className="mb-1 flex min-w-0 flex-wrap items-center gap-2">
                <h1 className="truncate text-lg font-bold text-white">
                  {user.first_name || 'Collector'}
                </h1>
                <span className="inline-flex max-w-full items-center gap-1.5 rounded-lg border border-white/5 bg-brand-midnight px-2 py-1 text-[10px] font-semibold text-neutral-300">
                  <Crown size={12} className="shrink-0 text-amber-500" />
                  <span className="truncate">{currentTitle}</span>
                </span>
              </div>

              <p className="truncate text-sm font-medium text-neutral-400">{usernameLabel}</p>

              <div className="mt-3 flex flex-wrap items-center gap-2">
                {user.role_tag && (
                  <span className="inline-flex items-center gap-1.5 rounded-lg border border-brand-accent/20 bg-brand-accent/10 px-2 py-1 text-[10px] font-bold text-brand-accent">
                    <BadgeCheck size={12} className="shrink-0" />
                    <span>{user.role_symbol}</span>
                    <span>{user.role_label || user.role_tag}</span>
                  </span>
                )}
                <span className="inline-flex items-center gap-1.5 rounded-lg border border-white/5 bg-brand-midnight px-2 py-1 text-[10px] font-semibold text-neutral-300">
                  <Ticket size={12} className="shrink-0 text-brand-accent" />
                  <span>{passLabel}</span>
                </span>
                {user.can_upload && uploadReward && (
                  <span className="rounded-lg border border-white/5 bg-brand-midnight px-2 py-1 text-[10px] font-semibold text-neutral-300">
                    Upload reward: {uploadReward}
                  </span>
                )}
                {roleBenefits.slice(0, 2).map((benefit) => (
                  <span
                    key={benefit}
                    className="rounded-lg border border-white/5 bg-brand-midnight px-2 py-1 text-[10px] font-semibold text-neutral-300"
                  >
                    {benefit}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="px-4 mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
        <StatTile icon={Coins} label="Shards" value={formatNumber(shardBalance)} tone="warning" />
        <StatTile icon={Gem} label="Zenith" value={formatNumber(stats?.zenith || 0)} tone="success" />
        <StatTile icon={Trophy} label="Rank" value={rankLabel} detail={percentileLabel} tone="warning" />
        <StatTile icon={BookOpen} label="Collection" value={`${formatNumber(collectionOwned)} / ${formatNumber(collectionTotal)}`} detail={`${collectionPercent}% complete`} tone="purple" />
      </div>

      <section className="px-4 mb-6 grid grid-cols-1 gap-3 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-lg border border-white/5 bg-brand-deep p-4 shadow-sm">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-white">Level progress</h2>
              <p className="mt-1 truncate text-xs font-medium text-neutral-500">
                {formatNumber(stats?.xp || 0)} total XP
              </p>
            </div>
            <TrendingUp size={17} className="shrink-0 text-brand-accent" />
          </div>
          <ProgressBar
            current={stats?.xp_current || 0}
            total={Math.max(1, stats?.xp_needed || 1000)}
            label="Progress to next level"
          />
        </div>

        <div className="rounded-lg border border-white/5 bg-brand-deep p-4 shadow-sm">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-white">Catalog progress</h2>
              <p className="mt-1 truncate text-xs font-medium text-neutral-500">
                {formatNumber(totalCopies)} total owned copies
              </p>
            </div>
            <BookOpen size={17} className="shrink-0 text-purple-500" />
          </div>
          <ProgressBar
            current={collectionOwned}
            total={collectionTotal}
            label="Unique characters"
            color="bg-purple-500"
          />
        </div>
      </section>

      <section className="px-4 mb-8 grid grid-cols-2 gap-2 lg:grid-cols-4">
        <StatTile icon={PawPrint} label="Active Pet" value={activePet?.name || 'None'} detail={petDetail} tone="accent" />
        <StatTile icon={Egg} label="Incubation" value={`${activeIncubations} / ${incubationSlots}`} detail="Active slots" tone="success" />
        <StatTile icon={BadgeCheck} label="Achievements" value={formatNumber(achievementCount)} detail={`${formatNumber(user.titles?.all?.length || 1)} titles`} tone="warning" />
        <StatTile icon={CalendarCheck} label="Streak" value={formatNumber(stats?.streak || 0)} detail="Daily activity" tone="neutral" />
      </section>

      {/* Collection Filters */}
      <section ref={collectionRef} className="px-4">
        <div className="sticky top-0 z-40 bg-brand-midnight/90 backdrop-blur-md py-4 border-b border-white/5 mb-6 -mx-4 px-4 shadow-sm">
          <div className="space-y-4">
            <div className="relative max-w-md mx-auto sm:mx-0">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500" size={16} />
              <input
                type="text"
                placeholder="Search by name, ID, or anime..."
                className="w-full bg-brand-deep border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-sm font-medium focus:border-brand-accent outline-none transition-all placeholder:text-neutral-500 text-white"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div className="relative max-w-xs">
              <select
                aria-label="Filter by rarity"
                value={rarity}
                onChange={(event) => setRarity(event.target.value)}
                className="h-10 w-full appearance-none rounded-lg border border-white/10 bg-brand-deep px-3 pr-9 text-sm font-semibold text-white outline-none transition-colors focus:border-brand-accent"
              >
                <option value="">All Rarities</option>
                {rarityOptions.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              <ChevronDown
                size={16}
                className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500"
              />
            </div>
          </div>
        </div>
        
        {error && items.length === 0 ? (
          <ErrorState message={error} onAction={refresh} />
        ) : items.length > 0 || (loading && page > 1) ? (
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3">
               {items.map((char, i) => (
                 <Card
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
          <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3">
             {Array.from({ length: 18 }).map((_, i) => (
                <CardSkeleton key={`loading-new-${i}`} />
             ))}
          </div>
        ) : (
          <EmptyState
            icon={BookOpen}
            title="Collection empty"
            message="Characters you collect will appear here."
          />
        )}

        {loading && items.length > 0 && (
           <div className="flex justify-center py-8">
              <Loader2 className="animate-spin text-neutral-600" size={24} />
           </div>
        )}
      </section>
    </div>
  );
};
