import React from 'react';
import { useApi } from '../hooks/useApi';
import { CardSkeleton } from '../components/ui/Skeleton';
import { BookOpen, Brain, ChartNoAxesColumnIncreasing, Coins, Gem, TrendingUp } from 'lucide-react';
import { formatNumber } from '../utils';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';
import { Avatar } from '../components/Avatar';

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
    return `Collector ${String(user.id || index + 1).slice(-4)}`;
};

const getInitials = (name: string) => {
    const parts = name.replace(/^@/, '').split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'U';
    return parts.slice(0, 2).map(part => part[0]).join('').toUpperCase();
};

export const Leaderboard = () => {
    const [metric, setMetric] = React.useState('harem');
    const { data, loading, error, execute: fetchLeaderboard } = useApi<LeaderboardUser[]>(`/leaderboard?metric=${metric}`, {}, [metric]);

    const METRICS = [
        { id: 'harem', label: 'Collection', icon: BookOpen },
        { id: 'shards', label: 'Shards', icon: Coins },
        { id: 'zenith', label: 'Zenith', icon: Gem },
        { id: 'level', label: 'Level', icon: TrendingUp },
        { id: 'guesses', label: 'Guesses', icon: Brain },
    ];
    const activeMetric = METRICS.find(m => m.id === metric);

    return (
        <div className="pb-20 pt-4 max-w-2xl mx-auto">
            <header className="px-4 mb-6 flex justify-between items-center border-b border-white/5 pb-4">
                <h1 className="text-xl font-bold text-white tracking-tight">Leaderboards</h1>
                <ChartNoAxesColumnIncreasing className="text-amber-500" size={24} />
            </header>

            <div className="px-4 mb-6">
                <div className="flex space-x-2 overflow-x-auto no-scrollbar py-1">
                    {METRICS.map(m => (
                        <button
                            key={m.id}
                            onClick={() => setMetric(m.id)}
                            className={cn(
                                "px-4 py-2 rounded-lg flex items-center space-x-2 border transition-all whitespace-nowrap text-sm font-semibold",
                                metric === m.id
                                ? 'bg-white text-brand-midnight border-white shadow-sm'
                                : 'bg-brand-deep border-white/5 text-neutral-400 hover:text-neutral-200 hover:border-white/10'
                            )}
                        >
                            <m.icon size={16} strokeWidth={2.5} />
                            <span>{m.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="px-4 space-y-2">
                {error && !data ? (
                    <ErrorState message={error} onAction={fetchLeaderboard} />
                ) : loading ? (
                    Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-16 bg-brand-deep rounded-xl animate-pulse border border-white/5" />)
                ) : data && data.length > 0 ? (
                    data?.map((user, i) => {
                        const displayName = getDisplayName(user, i);
                        const rank = user.rank || i + 1;

                        return (
                        <div key={user.id} className="bg-brand-deep p-3 rounded-xl border border-white/5 flex items-center justify-between shadow-sm">
                            <div className="flex items-center space-x-3">
                                <div className={cn(
                                    "w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0",
                                    rank === 1 ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20' :
                                    rank === 2 ? 'bg-neutral-300/10 text-neutral-300 border border-neutral-300/20' :
                                    rank === 3 ? 'bg-orange-400/10 text-orange-400 border border-orange-400/20' :
                                    'bg-brand-midnight text-neutral-500 border border-white/5'
                                )}>
                                    {rank}
                                </div>
                                <div className="flex items-center space-x-3 min-w-0">
                                    <Avatar
                                        src={user.avatar}
                                        alt={displayName}
                                        fallbackText={getInitials(displayName)}
                                        className="w-10 h-10 rounded-lg bg-brand-midnight border border-white/10"
                                    />
                                    <div className="min-w-0">
                                        <p className="text-sm font-bold text-white truncate pr-2">
                                            {displayName}
                                        </p>
                                        {user.username && (
                                            <p className="text-xs font-medium text-neutral-500 truncate">@{user.username}</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div className="text-right shrink-0 pl-2">
                                <p className="text-base font-bold text-white tabular-nums">{formatNumber(user.value)}</p>
                                <p className="text-xs font-medium text-neutral-500">{activeMetric?.label || metric}</p>
                            </div>
                        </div>
                        );
                    })
                ) : (
                    <div className="p-10 rounded-xl border border-white/5 border-dashed text-center bg-brand-deep">
                        <p className="text-sm font-medium text-neutral-500">No leaderboard data yet.</p>
                    </div>
                )}
            </div>
        </div>
    );
};
