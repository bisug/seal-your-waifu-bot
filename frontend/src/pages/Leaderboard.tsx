import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { BookOpen, Brain, ChartNoAxesColumnIncreasing, Coins, Gem, TrendingUp, Trophy } from 'lucide-react';
import { formatNumber } from '../utils';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';
import { Avatar } from '../components/Avatar';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Skeleton } from '../components/ui/Skeleton';

interface LeaderboardUser {
    id: number | string;
    rank?: number;
    first_name?: string;
    last_name?: string;
    full_name?: string;
    username?: string;
    avatar?: string | null;
    value: number;
}

const getDisplayName = (user: LeaderboardUser, index: number) => {
    const name = (user.full_name || user.first_name || '').trim();
    if (name && name.toLowerCase() !== 'user') return name;
    if (user.username) return user.username;
    return `COLLECTOR ${String(user.id || index + 1).slice(-4).toUpperCase()}`;
};

const getInitials = (name: string) => {
    const parts = name.replace(/^@/, '').split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'U';
    return parts.slice(0, 2).map(part => part[0]).join('').toUpperCase();
};

export const Leaderboard = () => {
    const [metric, setMetric] = useState('harem');
    const { data, loading, error, execute: fetchLeaderboard } = useApi<LeaderboardUser[]>(`/leaderboard?metric=${metric}`, {}, [metric]);

    const METRICS = [
        { id: 'harem', label: 'Archive', icon: BookOpen },
        { id: 'shards', label: 'Shards', icon: Coins },
        { id: 'zenith', label: 'Zenith', icon: Gem },
        { id: 'level', label: 'Level', icon: TrendingUp },
        { id: 'guesses', label: 'Intel', icon: Brain },
    ];
    const activeMetric = METRICS.find(m => m.id === metric);

    return (
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8 select-none">
            <header className="space-y-1">
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                        <Trophy className="text-amber-500" size={22} />
                   </div>
                   <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Global Ranking</h1>
                </div>
                <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">
                    The elite leaderboard of the seal's top collectors.
                </p>
            </header>

            <div className="flex gap-2 overflow-x-auto no-scrollbar pb-2 -mx-1 px-1">
                {METRICS.map(m => (
                    <button
                        key={m.id}
                        onClick={() => setMetric(m.id)}
                        className={cn(
                            "px-5 py-2.5 rounded-xl flex items-center gap-2 border transition-all whitespace-nowrap text-[10px] font-black uppercase tracking-widest",
                            metric === m.id
                            ? 'bg-white text-brand-midnight border-white shadow-[0_5px_15px_rgba(255,255,255,0.2)]'
                            : 'bg-brand-deep border-white/5 text-neutral-500 hover:text-white hover:border-white/10'
                        )}
                    >
                        <m.icon size={14} strokeWidth={3} />
                        <span>{m.label}</span>
                    </button>
                ))}
            </div>

            <div className="space-y-3">
                {error && !data ? (
                    <ErrorState message={error} onAction={fetchLeaderboard} />
                ) : loading ? (
                    Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-16 w-full rounded-2xl" />)
                ) : data && data.length > 0 ? (
                    data?.map((user, i) => {
                        const displayName = getDisplayName(user, i);
                        const rank = user.rank || i + 1;
                        const isTopThree = rank <= 3;

                        return (
                        <Card key={user.id} className={cn(
                            "p-3 flex items-center justify-between group",
                            rank === 1 ? "border-amber-500/30 bg-amber-500/5 shadow-[0_0_20px_rgba(245,158,11,0.05)]" :
                            rank === 2 ? "border-neutral-300/30 bg-neutral-300/5" :
                            rank === 3 ? "border-orange-400/30 bg-orange-400/5" : ""
                        )}>
                            <div className="flex items-center gap-4 min-w-0">
                                <div className={cn(
                                    "w-10 h-10 rounded-xl flex items-center justify-center text-xs font-black shrink-0 border transition-all duration-500 group-hover:scale-110",
                                    rank === 1 ? 'bg-amber-500/20 text-amber-500 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.3)]' :
                                    rank === 2 ? 'bg-neutral-300/20 text-neutral-300 border-neutral-300/30' :
                                    rank === 3 ? 'bg-orange-400/20 text-orange-400 border-orange-400/30' :
                                    'bg-brand-surface text-neutral-500 border-white/5'
                                )}>
                                    {rank}
                                </div>
                                <div className="flex items-center gap-3 min-w-0">
                                    <Avatar
                                        src={user.avatar}
                                        alt={displayName}
                                        fallbackText={getInitials(displayName)}
                                        className="w-11 h-11 rounded-xl bg-brand-surface border border-white/5"
                                    />
                                    <div className="min-w-0">
                                        <p className="text-sm font-black text-white uppercase tracking-tight truncate pr-2">
                                            {displayName}
                                        </p>
                                        {user.username && (
                                            <p className="text-[10px] font-bold text-neutral-500 truncate uppercase tracking-widest">@{user.username}</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div className="text-right shrink-0 pl-4 space-y-0.5">
                                <div className="flex items-center justify-end gap-1.5">
                                    <span className="text-base font-black text-white tabular-nums">{formatNumber(user.value)}</span>
                                    {isTopThree && activeMetric && <activeMetric.icon size={12} className={cn(
                                        rank === 1 ? 'text-amber-500' : rank === 2 ? 'text-neutral-300' : 'text-orange-400'
                                    )} />}
                                </div>
                                <p className="text-[9px] font-black text-neutral-600 uppercase tracking-widest">{activeMetric?.label || metric}</p>
                            </div>
                        </Card>
                        );
                    })
                ) : (
                    <Card className="py-20 border-dashed bg-brand-deep/30 text-center flex flex-col items-center">
                        <ChartNoAxesColumnIncreasing size={40} className="text-neutral-800 mb-4" />
                        <p className="text-[10px] font-black text-neutral-600 uppercase tracking-widest">No ranking data detected</p>
                    </Card>
                )}
            </div>
        </div>
    );
};
