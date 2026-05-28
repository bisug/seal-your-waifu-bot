import React from 'react';
import { useApi } from '../hooks/useApi';
import { CardSkeleton } from '../components/ui/Skeleton';
import { Trophy, Shield, Activity, Users, Zap, Swords } from 'lucide-react';
import { formatNumber } from '../utils';
import { cn } from '../utils';

export const Leaderboard = () => {
    const [metric, setMetric] = React.useState('harem');
    const { data, loading } = useApi<any[]>(`/leaderboard?metric=${metric}`, {}, [metric]);

    const METRICS = [
        { id: 'harem', label: 'Harem', icon: Users },
        { id: 'shards', label: 'Shards', icon: Zap },
        { id: 'zenith', label: 'Zenith', icon: Activity },
        { id: 'level', label: 'Level', icon: Shield },
        { id: 'guesses', label: 'Combat', icon: Swords },
    ];

    return (
        <div className="pb-32 pt-6">
            <header className="px-4 mb-6 flex justify-between items-center">
                <h1 className="text-xl font-bold text-zinc-100">Leaderboards</h1>
                <Trophy className="text-amber-500" size={20} />
            </header>

            <div className="px-4 mb-6">
                <div className="flex space-x-2 overflow-x-auto no-scrollbar py-1">
                    {METRICS.map(m => (
                        <button
                            key={m.id}
                            onClick={() => setMetric(m.id)}
                            className={cn(
                                "px-4 py-2 rounded-md flex items-center space-x-2 border transition-all whitespace-nowrap text-xs font-medium",
                                metric === m.id
                                ? 'bg-zinc-100 text-zinc-950 border-zinc-100 shadow-sm'
                                : 'bg-zinc-900 border-white/5 text-zinc-500 hover:text-zinc-300 hover:border-zinc-700'
                            )}
                        >
                            <m.icon size={14} strokeWidth={2.5} />
                            <span>{m.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="px-4 space-y-2">
                {loading ? (
                    Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-14 bg-zinc-900 rounded-lg animate-pulse border border-white/5" />)
                ) : (
                    data?.map((user, i) => (
                        <div key={user.id} className="bg-zinc-900/50 p-3 rounded-lg border border-white/5 flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                                <div className={cn(
                                    "w-7 h-7 rounded-md flex items-center justify-center text-[10px] font-bold",
                                    i === 0 ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20' :
                                    i === 1 ? 'bg-zinc-300/10 text-zinc-300 border border-zinc-300/20' :
                                    i === 2 ? 'bg-orange-400/10 text-orange-400 border border-orange-400/20' :
                                    'bg-zinc-950 text-zinc-600 border border-white/5'
                                )}>
                                    {i + 1}
                                </div>
                                <div className="flex items-center space-x-3">
                                    <div className="w-9 h-9 rounded-md bg-zinc-800 overflow-hidden border border-white/10 shrink-0">
                                        <img src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} alt="" className="w-full h-full object-cover grayscale-[0.2]" />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="text-xs font-bold text-zinc-100 truncate max-w-[120px]">
                                            {user.full_name || user.first_name || 'User'}
                                        </p>
                                        {user.username && (
                                            <p className="text-[10px] font-medium text-zinc-500 truncate">@{user.username}</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                            <div className="text-right shrink-0">
                                <p className="text-sm font-bold text-zinc-100 tabular-nums">{formatNumber(user.value)}</p>
                                <p className="text-[10px] font-medium text-zinc-600 uppercase tracking-tight">{metric}</p>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
