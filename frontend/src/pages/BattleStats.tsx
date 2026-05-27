import React from 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { Swords, Activity } from 'lucide-react';

export const BattleStats = () => {
    const { data: stats, loading } = useApi('/battle/stats');

    if (loading) return (
        <div className="px-6 pb-12 pt-4 space-y-4">
            <Skeleton className="h-64 rounded-[3rem]" />
        </div>
    );

    return (
        <div className="px-6 pb-12 pt-4">
            <div className="flex items-center space-x-3 mb-8">
                <Swords className="text-brand-accent" size={24} />
                <h1 className="text-2xl font-black uppercase tracking-tighter italic">Combat Log</h1>
            </div>

            <div className="glass-panel p-8 rounded-[3rem] border border-white/5 text-center flex flex-col items-center">
                 <Activity size={48} className="text-slate-800 mb-6" />
                 <h2 className="text-lg font-black text-white uppercase tracking-widest mb-2">Passive Phase</h2>
                 <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-relaxed">
                     No combat data detected for current session.
                 </p>
            </div>
        </div>
    );
};
