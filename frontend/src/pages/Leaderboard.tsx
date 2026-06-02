import React from 'react';
import { useApi } from '../hooks/useApi';
import { CardSkeleton } from '../components/ui/Skeleton';
import { Trophy, Shield, Activity, Users, Zap, Swords } from 'lucide-react';
import { formatNumber } from '../utils';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';

export const Leaderboard = () => {
    const [metric, setMetric] = React.useState('harem');
    const { data, loading, error, execute: fetchLeaderboard } = useApi<any[]>(`/leaderboard?metric=${metric}`, {}, [metric]);

    const METRICS = [
        { id: 'harem', label: 'Collection', icon: Users },
        { id: 'shards', label: 'Shards', icon: Zap },
        { id: 'zenith', label: 'Zenith', icon: Activity },
        { id: 'level', label: 'Level', icon: Shield },
        { id: 'guesses', label: 'Guesses', icon: Swords },
    ];
    const activeMetric = METRICS.find(m => m.id === metric);

    return (
        <div className="pb-20 pt-4 max-w-2xl mx-auto">
            <header className="px-4 mb-6 flex justify-between items-center border-b border-white/5 pb-4">
                <h1 className="text-xl font-bold text-white tracking-tight">Leaderboards</h1>
                <Trophy className="text-amber-500" size={24} />
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
                    data?.map((user, i) => (
                        <div key={user.id} className="bg-brand-deep p-3 rounded-xl border border-white/5 flex items-center justify-between shadow-sm">
                            <div className="flex items-center space-x-3">
                                <div className={cn(
                                    "w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0",
                                    i === 0 ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20' :
                                    i === 1 ? 'bg-neutral-300/10 text-neutral-300 border border-neutral-300/20' :
                                    i === 2 ? 'bg-orange-400/10 text-orange-400 border border-orange-400/20' :
                                    'bg-brand-midnight text-neutral-500 border border-white/5'
                                )}>
                                    {i + 1}
                                </div>
                                <div className="flex items-center space-x-3 min-w-0">
                                    <div className="w-10 h-10 rounded-lg bg-brand-midnight overflow-hidden border border-white/10 shrink-0">
                                        <img src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} alt="" className="w-full h-full object-cover" />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-sm font-bold text-white truncate pr-2">
                                            {user.full_name || user.first_name || 'User'}
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
                    ))
                ) : (
                    <div className="p-10 rounded-xl border border-white/5 border-dashed text-center bg-brand-deep">
                        <p className="text-sm font-medium text-neutral-500">No leaderboard data yet.</p>
                    </div>
                )}
            </div>
        </div>
    );
};
