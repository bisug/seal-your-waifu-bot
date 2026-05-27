import React from 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { Award, Lock, CheckCircle2 } from 'lucide-react';
import { cn } from '../utils';

interface Achievement {
    id: string;
    name: string;
    description: string;
    icon: string;
    reward_xp: number;
    unlocked: boolean;
}

export const Achievements = () => {
    const { data: achievements, loading } = useApi<Achievement[]>('/achievements/list');

    if (loading && !achievements) return (
        <div className="px-6 py-8 space-y-4">
             <div className="h-8 w-48 bg-white/5 rounded-lg mb-6 animate-pulse" />
             {[1,2,3,4,5].map(i => (
                <Skeleton key={i} className="h-24 rounded-2xl" />
             ))}
        </div>
    );

    const sortedAchievements = [...(achievements || [])].sort((a, b) => {
        if (a.unlocked === b.unlocked) return 0;
        return a.unlocked ? -1 : 1;
    });

    return (
        <div className="px-6 py-8 pb-20">
            <header className="mb-8">
                <h1 className="text-2xl font-black italic uppercase tracking-tighter text-white flex items-center gap-3">
                    <Award className="text-brand-accent" size={24} />
                    Achievement Hall
                </h1>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.3em] mt-1">Proof of your legendary journey</p>
            </header>

            <div className="space-y-3">
                {sortedAchievements.map((ach) => (
                    <div
                        key={ach.id}
                        className={cn(
                            "glass-panel p-4 rounded-2xl border transition-all duration-300 flex items-center gap-4",
                            ach.unlocked
                                ? "bg-brand-accent/5 border-brand-accent/20"
                                : "bg-white/5 border-white/5 opacity-60"
                        )}
                    >
                        <div className={cn(
                            "w-12 h-12 rounded-xl flex items-center justify-center text-xl shadow-inner border",
                            ach.unlocked
                                ? "bg-brand-accent/10 border-brand-accent/20 text-brand-accent"
                                : "bg-black/20 border-white/5 text-slate-600"
                        )}>
                            {ach.icon}
                        </div>

                        <div className="flex-1 min-w-0">
                            <h3 className={cn(
                                "text-xs font-black uppercase tracking-wider mb-0.5",
                                ach.unlocked ? "text-white" : "text-slate-400"
                            )}>
                                {ach.name}
                            </h3>
                            <p className="text-[10px] text-slate-500 font-medium leading-tight line-clamp-2">
                                {ach.description}
                            </p>
                        </div>

                        <div className="shrink-0 flex flex-col items-end gap-1">
                            {ach.unlocked ? (
                                <CheckCircle2 size={16} className="text-brand-accent" />
                            ) : (
                                <Lock size={14} className="text-slate-700" />
                            )}
                            <span className={cn(
                                "text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-tighter",
                                ach.unlocked ? "bg-brand-accent/20 text-brand-accent" : "bg-white/5 text-slate-600"
                            )}>
                                +{ach.reward_xp} XP
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
