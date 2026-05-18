import React from 'react';
import { useApi } from '../hooks/useApi';
import { CardSkeleton } from '../components/ui/Skeleton';
import { Trophy, Shield, Activity, Users, Zap, Swords } from 'lucide-react';
import { formatNumber } from '../utils';

export const Leaderboard = () => {
    const [metric, setMetric] = React.useState('harem');
    const { data, loading } = useApi(`/leaderboard?metric=${metric}`, {}, [metric]);

    const METRICS = [
        { id: 'harem', label: 'Harem', icon: Users },
        { id: 'shards', label: 'Shards', icon: Zap },
        { id: 'zenith', label: 'Zenith', icon: Activity },
        { id: 'level', label: 'Level', icon: Shield },
        { id: 'guesses', label: 'Combat', icon: Swords },
    ];

    return (
        <div className="pb-32 pt-6">
            <header className="px-6 mb-8 flex justify-between items-center">
                <h1 className="text-3xl font-black italic uppercase tracking-tighter text-white">Rankings</h1>
                <Trophy className="text-brand-accent" size={24} />
            </header>

            <div className="px-4 mb-8">
                <div className="flex space-x-2 overflow-x-auto no-scrollbar scroll-fade-mask py-1">
                    {METRICS.map(m => (
                        <button
                            key={m.id}
                            onClick={() => setMetric(m.id)}
                            className={`px-5 py-3 rounded-2xl flex items-center space-x-2 border transition-all whitespace-nowrap ${
                                metric === m.id
                                ? 'bg-brand-accent text-brand-midnight border-brand-accent shadow-lg shadow-brand-accent/20 scale-105'
                                : 'bg-white/5 border-white/5 text-slate-500'
                            }`}
                        >
                            <m.icon size={14} />
                            <span className="text-[10px] font-black uppercase tracking-widest">{m.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="px-4 space-y-2.5">
                {loading ? (
                    Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-16 bg-white/[0.03] rounded-2xl animate-pulse" />)
                ) : (
                    data?.map((user, i) => (
                        <div key={user.id} className="glass-panel p-4 rounded-2xl border border-white/5 flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-black italic ${i < 3 ? 'bg-brand-accent text-brand-midnight shadow-lg' : 'bg-white/5 text-slate-600'}`}>
                                    {i + 1}
                                </div>
                                <div className="flex items-center space-x-3">
                                    <div className="w-10 h-10 rounded-xl bg-slate-800 overflow-hidden border border-white/10">
                                        <img src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} alt="" className="w-full h-full object-cover" />
                                    </div>
                                    <div>
                                        <p className="text-[12px] font-black text-white leading-none mb-1">{user.first_name}</p>
                                        <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest">@{user.username || 'matrix_user'}</p>
                                    </div>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="text-[13px] font-black text-brand-accent">{formatNumber(user.score)}</p>
                                <p className="text-[8px] font-bold text-slate-600 uppercase tracking-widest">{metric}</p>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
