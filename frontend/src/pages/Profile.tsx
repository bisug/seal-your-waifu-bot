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
  Zap,
  Target,
  Database,
  Activity,
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
    variant="tactical"
    className={cn("p-4 flex flex-col justify-between group relative overflow-hidden", className)}
    {...props}
  >
    {/* Subtle scanline effect for bento tiles */}
    <div className="absolute inset-0 pointer-events-none bg-scanline opacity-[0.03]" />
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

  if (userLoading && items.length === 0) return (
    <div className="pb-24 pt-4 px-4 max-w-5xl mx-auto space-y-4">
       <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Skeleton className="md:col-span-2 h-32 rounded-lg" />
          <Skeleton className="h-32 rounded-lg" />
       </div>
       <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-20 rounded-lg" />)}
       </div>
       <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2.5">
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
  const currentTitle = user.titles?.current || 'OPERATIVE';
  const activePet = user.current_pet;
  const usernameLabel = user.username ? `@${user.username}` : `ID ${user.id}`;

  return (
    <div className="pb-24 pt-4 max-w-5xl mx-auto adaptive-px space-y-4">
      {/* Primary Status Section */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* User Profile Tile */}
        <BentoTile className="md:col-span-2 flex-row items-center gap-5 p-5 min-h-[140px]">
          <div className="relative shrink-0">
            <div className="absolute -inset-1.5 bg-brand-accent/20 rounded-lg blur-md opacity-40 group-hover:opacity-70 transition-opacity" />
            <Avatar
              src={user.avatar}
              alt="User"
              className="w-20 h-20 rounded-md border border-white/10 relative z-10 object-cover"
            />
            <div className="absolute -bottom-1.5 -right-1.5 z-20">
                <Badge variant="tactical" size="xs" className="px-1.5 py-1 border-white/20">
                    LVL {stats?.level || 1}
                </Badge>
            </div>
          </div>

          <div className="flex-1 min-w-0 space-y-2.5">
            <div>
                <div className="flex flex-wrap items-center gap-2 mb-0.5">
                    <h1 className="text-lg font-black text-white tracking-tight uppercase truncate">
                        {user.first_name || 'Collector'}
                    </h1>
                    {user.role_tag && (
                        <Badge variant="primary" size="xs" className="tracking-[0.1em]">
                            {user.role_symbol} {user.role_tag}
                        </Badge>
                    )}
                </div>
                <p className="text-[10px] font-mono font-bold text-neutral-600 tracking-wider uppercase">{usernameLabel}</p>
            </div>

            <div className="flex flex-wrap items-center gap-1.5">
                <Badge variant="purple" size="xs" icon={Crown} className="rounded-sm border-purple-500/30">
                    {currentTitle}
                </Badge>
                <Badge variant="secondary" size="xs" icon={Ticket} className="rounded-sm">
                    {passLabel}
                </Badge>
            </div>

            <div className="pt-1 w-full max-w-[240px]">
                <ProgressBar
                    current={stats?.xp_current || 0}
                    total={Math.max(1, stats?.xp_needed || 1000)}
                    label="XP PROGRESSION"
                    compact
                />
            </div>
          </div>

          {/* Subtle Decorative Element */}
          <div className="absolute right-4 top-4 text-white/[0.02] pointer-events-none select-none">
             <Target size={80} strokeWidth={1} />
          </div>
        </BentoTile>

        {/* Collection Status Tile */}
        <BentoTile className="bg-brand-surface/40 border-white/[0.05]">
           <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-1.5">
                <Database size={12} className="text-purple-500" />
                <span className="text-[9px] font-black text-neutral-500 uppercase tracking-[0.2em]">Data Archives</span>
              </div>
              <div className="w-1.5 h-1.5 rounded-full bg-purple-500/40 animate-pulse" />
           </div>

           <div className="space-y-3">
              <div className="flex items-end justify-between">
                 <div className="text-2xl font-black text-white stats-value tabular-nums leading-none">
                    {collectionPercent}<span className="text-xs text-purple-500 ml-0.5">%</span>
                 </div>
                 <div className="text-right">
                    <div className="text-[9px] font-black text-neutral-600 uppercase tracking-tighter">Inventory</div>
                    <div className="text-[11px] font-mono font-bold text-white tabular-nums">
                        {formatNumber(collectionOwned)}<span className="mx-0.5 text-neutral-700">/</span>{formatNumber(collectionTotal)}
                    </div>
                 </div>
              </div>
              <ProgressBar
                current={collectionOwned}
                total={collectionTotal}
                color="bg-purple-500"
                compact
                showValue={false}
              />
           </div>
        </BentoTile>
      </section>

      {/* Resource Grid */}
      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <BentoTile className="py-3 px-4">
           <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Coins size={14} className="text-amber-500" />
                <span className="stats-label">Shards</span>
              </div>
           </div>
           <div className="stats-value text-lg text-white tabular-nums truncate">{formatNumber(stats?.points ?? user.balance ?? 0)}</div>
        </BentoTile>

        <BentoTile className="py-3 px-4">
           <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Gem size={14} className="text-brand-accent" />
                <span className="stats-label">Zenith</span>
              </div>
           </div>
           <div className="stats-value text-lg text-white tabular-nums truncate">{formatNumber(stats?.zenith || 0)}</div>
        </BentoTile>

        <BentoTile className="py-3 px-4">
           <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Trophy size={14} className="text-emerald-500" />
                <span className="stats-label">Rank</span>
              </div>
           </div>
           <div className="flex items-baseline gap-1.5">
              <span className="stats-value text-lg text-white tabular-nums truncate">{rankLabel}</span>
              <span className="text-[8px] font-black text-neutral-600 uppercase truncate">{percentileLabel}</span>
           </div>
        </BentoTile>

        <BentoTile className="py-3 px-4">
           <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Activity size={14} className="text-blue-400" />
                <span className="stats-label">Uptime</span>
              </div>
           </div>
           <div className="stats-value text-lg text-white tabular-nums truncate">{formatNumber(stats?.streak || 0)} <span className="text-[10px] text-neutral-500 font-black ml-0.5">DAYS</span></div>
        </BentoTile>
      </section>

      {/* Sub-Systems Section */}
      <section className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <BentoTile className="flex-row items-center gap-4 py-3">
           <div className="w-10 h-10 rounded-md bg-white/[0.02] border border-white/[0.05] flex items-center justify-center shrink-0">
              <PawPrint size={20} className="text-brand-accent" />
           </div>
           <div className="min-w-0 flex-1">
              <div className="text-[8px] font-black text-neutral-600 uppercase tracking-widest mb-0.5">Active Companion</div>
              <div className="text-xs font-black text-white truncate uppercase tracking-tight">{activePet?.name || 'STANDBY...'}</div>
           </div>
           {activePet && (
              <Badge variant="tactical" size="xs" className="font-mono px-1.5">L.{activePet.level || 1}</Badge>
           )}
        </BentoTile>

        <BentoTile className="flex-row items-center gap-4 py-3">
           <div className="w-10 h-10 rounded-md bg-white/[0.02] border border-white/[0.05] flex items-center justify-center shrink-0">
              <Egg size={20} className="text-emerald-500" />
           </div>
           <div className="min-w-0 flex-1">
              <div className="text-[8px] font-black text-neutral-600 uppercase tracking-widest mb-0.5">Incubation Status</div>
              <div className="text-xs font-black text-white truncate uppercase tracking-tight">{stats?.active_incubations || 0}<span className="text-neutral-700 mx-1">/</span>{stats?.incubation_slots || 1} SEALS ACTIVE</div>
           </div>
           <div className="w-6 h-6 rounded-full border border-emerald-500/20 flex items-center justify-center">
                <div className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
           </div>
        </BentoTile>
      </section>

      {/* Character Collection Header */}
      <section ref={collectionRef} className="pt-2 space-y-4">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div className="space-y-0.5">
                <h2 className="text-lg font-black text-white tracking-tighter uppercase">Registry Archives</h2>
                <div className="flex items-center gap-1.5">
                    <Zap size={10} className="text-brand-accent animate-pulse" />
                    <p className="text-[9px] font-bold text-neutral-600 uppercase tracking-[0.2em]">Querying centralized storage...</p>
                </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
                <div className="w-full sm:w-56">
                    <Input
                        icon={Search}
                        placeholder="FILTER BY NAME..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="h-9 py-1 text-[10px]"
                    />
                </div>
                <div className="relative group">
                    <select
                        aria-label="Filter by rarity"
                        value={rarity}
                        onChange={(event) => setRarity(event.target.value)}
                        className="h-9 pl-3 pr-8 bg-[#0a0a0c] border border-white/10 rounded-md text-[10px] font-black text-white uppercase tracking-widest outline-none focus:border-brand-accent transition-all appearance-none cursor-pointer"
                    >
                        <option value="">ALL CLASSIFICATIONS</option>
                        {rarityOptions.map(({ value, label }) => (
                            <option key={value} value={value}>{label.toUpperCase()}</option>
                        ))}
                    </select>
                    <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-700 pointer-events-none group-focus-within:text-brand-accent transition-colors" />
                </div>
            </div>
        </div>

        {error && (items?.length || 0) === 0 ? (
          <ErrorState message={error} onAction={refresh} />
        ) : (items?.length || 0) > 0 || (loading && page > 1) ? (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-3">
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
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-3">
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
           <div className="flex justify-center py-8">
              <Loader2 className="animate-spin text-brand-accent/30" size={24} />
           </div>
        )}
      </section>
    </div>
  );
};
