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
  BookOpen,
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
  Activity,
  Heart,
  Sparkles,
  Zap,
} from 'lucide-react';
import { cleanRarityLabel, formatNumber, cn } from '../utils';
import { useInfiniteGrid } from '../hooks/useInfiniteGrid';
import { Character } from '../context/UserContext';

interface ProfileProps {
  onCharClick: (character: Character) => void;
  focusCollection?: boolean;
}

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
    () => (Array.isArray(availableRarities) ? availableRarities : []).map((value) => ({ value, label: cleanRarityLabel(value) || value })),
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

  if (userLoading && (items?.length || 0) === 0) return (
    <div className="pb-24 pt-6 px-5 max-w-5xl mx-auto space-y-6">
       <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="md:col-span-2 h-40 rounded-2xl" />
          <Skeleton className="h-40 rounded-2xl" />
       </div>
       <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-24 rounded-2xl" />)}
       </div>
       <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3 sm:gap-4">
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
  const currentTitle = user.titles?.current || 'COLLECTOR';
  const activePet = user.current_pet;
  const usernameLabel = user.username ? `@${user.username}` : `ID ${user.id}`;

  return (
    <div className="pb-32 pt-6 max-w-5xl mx-auto adaptive-px space-y-6">
      {/* Primary Status Section */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* User Profile Card */}
        <Card isBento variant="tactical" className="md:col-span-2 flex-row items-center gap-6 p-6 min-h-[160px]">
          <div className="relative shrink-0">
            <div className="absolute -inset-2 bg-brand-accent/20 rounded-2xl blur-xl opacity-30 group-hover:opacity-50 transition-opacity" />
            <Avatar
              src={user.avatar}
              alt="User"
              className="w-24 h-24 rounded-2xl border border-white/10 relative z-10 object-cover shadow-2xl"
            />
            <div className="absolute -bottom-2 -right-2 z-20">
                <Badge variant="tactical" size="xs" className="px-2 py-1.5 border-white/10 shadow-lg backdrop-blur-md">
                    LVL {stats?.level || 1}
                </Badge>
            </div>
          </div>

          <div className="flex-1 min-w-0 space-y-3">
            <div>
                <div className="flex flex-wrap items-center gap-2.5 mb-1">
                    <h1 className="text-xl font-black text-white tracking-tight uppercase truncate">
                        {user.first_name || 'Operator'}
                    </h1>
                    {user.role_tag && (
                        <Badge variant="primary" size="xs" className="tracking-[0.1em] font-black">
                            {user.role_symbol} {user.role_tag}
                        </Badge>
                    )}
                </div>
                <p className="text-[10px] font-mono font-bold text-neutral-600 tracking-widest uppercase">{usernameLabel}</p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
                <Badge variant="epic" size="xs" icon={Crown} className="rounded-md border-epic/20 font-black">
                    {currentTitle}
                </Badge>
                <Badge variant="secondary" size="xs" icon={Ticket} className="rounded-md font-black">
                    {passLabel}
                </Badge>
            </div>

            <div className="pt-2 w-full max-w-[280px]">
                <ProgressBar
                    current={stats?.xp_current || 0}
                    total={Math.max(1, stats?.xp_needed || 1000)}
                    label="SYSTEM EXPERIENCE"
                    compact
                    variant="default"
                />
            </div>
          </div>

          <div className="absolute right-6 top-6 opacity-[0.03] pointer-events-none select-none text-white transition-transform group-hover:scale-110 duration-700">
             <Zap size={100} strokeWidth={1} />
          </div>
        </Card>

        {/* Collection Progress Card */}
        <Card isBento variant="tactical" className="p-6 border-epic/10 bg-epic/[0.02]">
           <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <BookOpen size={14} className="text-epic" />
                <span className="text-[10px] font-black text-neutral-500 uppercase tracking-[0.25em]">Registry</span>
              </div>
              <div className="w-2 h-2 rounded-full bg-epic/40 animate-pulse shadow-[0_0_8px_rgba(168,85,247,0.4)]" />
           </div>

           <div className="space-y-4">
              <div className="flex items-end justify-between">
                 <div className="text-3xl font-black text-white stats-value tabular-nums leading-none">
                    {collectionPercent}<span className="text-sm text-epic ml-1">%</span>
                 </div>
                 <div className="text-right">
                    <div className="text-[9px] font-black text-neutral-600 uppercase tracking-widest mb-1">UNITS</div>
                    <div className="text-sm font-mono font-bold text-white tabular-nums">
                        {formatNumber(collectionOwned)}<span className="mx-1 opacity-20">/</span>{formatNumber(collectionTotal)}
                    </div>
                 </div>
              </div>
              <ProgressBar
                current={collectionOwned}
                total={collectionTotal}
                variant="epic"
                compact
                showValue={false}
              />
           </div>
        </Card>
      </section>

      {/* Stats Grid */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { icon: Coins, label: 'Shards', value: formatNumber(stats?.points ?? user.balance ?? 0), variant: 'warning' },
          { icon: Gem, label: 'Zenith', value: formatNumber(stats?.zenith || 0), variant: 'primary' },
          { icon: Trophy, label: 'Rank', value: rankLabel, subValue: percentileLabel, variant: 'success' },
          { icon: Activity, label: 'Streak', value: `${formatNumber(stats?.streak || 0)} DAYS`, variant: 'rare' },
        ].map((stat, i) => (
          <Card key={i} variant="tactical" className="p-4 border-white/[0.03] hover:border-white/[0.08] transition-colors group">
            <div className="flex items-center gap-2 mb-3">
              <stat.icon size={14} className={cn(
                stat.variant === 'primary' && 'text-brand-accent',
                stat.variant === 'success' && 'text-success',
                stat.variant === 'warning' && 'text-warning',
                stat.variant === 'rare' && 'text-rare',
              )} />
              <span className="stats-label">{stat.label}</span>
            </div>
            <div className="flex flex-col gap-0.5">
               <div className="stats-value text-lg text-white tabular-nums truncate leading-none uppercase">
                 {stat.value}
               </div>
               {stat.subValue && (
                 <span className="text-[8px] font-black text-neutral-600 uppercase tracking-widest truncate">{stat.subValue}</span>
               )}
            </div>
            <div className="absolute top-2 right-2 w-1 h-1 rounded-full bg-white/[0.05] group-hover:bg-white/[0.2] transition-colors" />
          </Card>
        ))}
      </section>

      {/* Sub-Systems Section */}
      <section className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card variant="tactical" className="flex flex-row items-center gap-5 p-4 border-white/[0.03] group cursor-pointer hover:bg-white/[0.01]">
           <div className="w-12 h-12 rounded-xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center shrink-0 shadow-inner group-hover:border-brand-accent/20 transition-colors">
              <PawPrint size={24} className="text-brand-accent transition-transform group-hover:scale-110" />
           </div>
           <div className="min-w-0 flex-1">
              <div className="text-[9px] font-black text-neutral-600 uppercase tracking-widest mb-1">Companion active</div>
              <div className="text-sm font-black text-white truncate uppercase tracking-tight">{activePet?.name || 'STANDBY...'}</div>
           </div>
           {activePet ? (
              <Badge variant="tactical" size="xs" className="font-mono px-2 py-1 border-white/10">LVL {activePet.level || 1}</Badge>
           ) : (
              <div className="w-8 h-8 rounded-full border border-dashed border-white/10 flex items-center justify-center">
                 <div className="w-1 h-1 rounded-full bg-neutral-800" />
              </div>
           )}
        </Card>

        <Card variant="tactical" className="flex flex-row items-center gap-5 p-4 border-white/[0.03] group cursor-pointer hover:bg-white/[0.01]">
           <div className="w-12 h-12 rounded-xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center shrink-0 shadow-inner group-hover:border-success/20 transition-colors">
              <Egg size={24} className="text-success transition-transform group-hover:scale-110" />
           </div>
           <div className="min-w-0 flex-1">
              <div className="text-[9px] font-black text-neutral-600 uppercase tracking-widest mb-1">Incubator status</div>
              <div className="text-sm font-black text-white truncate uppercase tracking-tight">
                 {stats?.active_incubations || 0}<span className="text-neutral-700 mx-1.5 opacity-40">/</span>{stats?.incubation_slots || 1} ACTIVE
              </div>
           </div>
           <div className="w-8 h-8 rounded-full bg-success/5 border border-success/10 flex items-center justify-center relative">
                <div className="absolute inset-0 bg-success/10 rounded-full animate-ping opacity-20" />
                <div className="w-1.5 h-1.5 rounded-full bg-success shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
           </div>
        </Card>
      </section>

      {/* Registry Section */}
      <section ref={collectionRef} className="pt-4 space-y-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 px-1">
            <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                   <h2 className="text-2xl font-black text-white tracking-tighter uppercase">My Registry</h2>
                   <Badge variant="tactical" size="xs" className="bg-brand-accent/10 text-brand-accent border-brand-accent/20">PRIVATE</Badge>
                </div>
                <div className="flex items-center gap-2 opacity-50">
                    <Sparkles size={11} className="text-brand-accent" />
                    <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-[0.2em]">Synchronizing data with mainframe...</p>
                </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
                <div className="w-full sm:w-64">
                    <Input
                        icon={Search}
                        placeholder="FILTER BY ASSET NAME..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="h-11"
                    />
                </div>
                <div className="relative group">
                    <select
                        aria-label="Filter by rarity"
                        value={rarity}
                        onChange={(event) => setRarity(event.target.value)}
                        className="h-11 pl-4 pr-11 bg-[#0a0a0c] border border-white/10 rounded-xl text-[10px] font-black text-white uppercase tracking-[0.2em] outline-none focus:border-brand-accent transition-all appearance-none cursor-pointer"
                    >
                        <option value="">ALL CLASSES</option>
                        {rarityOptions.map(({ value, label }) => (
                            <option key={value} value={value}>{label.toUpperCase()}</option>
                        ))}
                    </select>
                    <ChevronDown size={14} className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-700 pointer-events-none group-focus-within:text-brand-accent transition-colors" />
                </div>
            </div>
        </div>

        {error && (items?.length || 0) === 0 ? (
          <div className="py-12">
            <ErrorState message={error} onAction={refresh} />
          </div>
        ) : (items?.length || 0) > 0 || (loading && page > 1) ? (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4 px-0.5">
               {(items || []).map((char, i) => (
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
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4 px-0.5">
             {Array.from({ length: 18 }).map((_, i) => (
                <CardSkeleton key={`loading-new-${i}`} />
             ))}
          </div>
        ) : (
          <div className="py-20">
            <EmptyState
              icon={BookOpen}
              title="Registry Empty"
              message="No units found. Personnel recruitment required."
            />
          </div>
        )}

        {loading && (items?.length || 0) > 0 && (
           <div className="flex justify-center py-12">
              <div className="relative">
                 <Loader2 className="animate-spin text-brand-accent" size={32} />
                 <div className="absolute inset-0 bg-brand-accent/20 blur-xl rounded-full" />
              </div>
           </div>
        )}
      </section>
    </div>
  );
};
