import React from 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { Award, Lock, CheckCircle2 } from 'lucide-react';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';

interface Achievement {
    id: string;
    name: string;
    description: string;
    icon: string;
    reward_xp: number;
    unlocked: boolean;
}

export const Achievements = () => {
    const { data: achievements, loading, error, execute: fetchAchievements } = useApi<Achievement[]>('/achievements/list');

    if (loading && !achievements) return (
        <div className="px-4 py-8 space-y-3">
             <div className="h-6 w-40 bg-zinc-900 rounded-md mb-6 animate-pulse border border-white/5" />
             {[1,2,3,4,5].map(i => (
                <Skeleton key={i} className="h-20 rounded-lg" />
             ))}
        </div>
    );

    if (error && !achievements) return (
        <div className="px-4 py-8">
            <ErrorState message={error} onAction={fetchAchievements} />
        </div>
    );

    const sortedAchievements = [...(achievements || [])].sort((a, b) => {
        if (a.unlocked === b.unlocked) return 0;
        return a.unlocked ? -1 : 1;
    });

    return (
        <div className="px-4 py-8 pb-20">
            <header className="mb-8">
                <h1 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
                    <Award className="text-brand-accent" size={20} />
                    Achievements
                </h1>
                <p className="text-xs font-medium text-zinc-500 mt-1">Unlock milestones to earn experience</p>
            </header>

            <div className="space-y-2">
                {sortedAchievements.map((ach) => (
                    <div
                        key={ach.id}
                        className={cn(
                            "p-4 rounded-lg border transition-all duration-300 flex items-center gap-4",
                            ach.unlocked
                                ? "bg-zinc-900 border-emerald-900/30"
                                : "bg-zinc-900/50 border-white/5 opacity-60"
                        )}
                    >
                        <div className={cn(
                            "w-12 h-12 rounded-md flex items-center justify-center text-xl border shrink-0",
                            ach.unlocked
                                ? "bg-emerald-500/10 border-emerald-500/20"
                                : "bg-zinc-950 border-white/5 grayscale"
                        )}>
                            {ach.icon}
                        </div>

                        <div className="flex-1 min-w-0">
                            <h3 className={cn(
                                "text-sm font-bold mb-0.5",
                                ach.unlocked ? "text-zinc-100" : "text-zinc-500"
                            )}>
                                {ach.name}
                            </h3>
                            <p className="text-xs text-zinc-500 font-medium leading-tight line-clamp-2">
                                {ach.description}
                            </p>
                        </div>

                        <div className="shrink-0 flex flex-col items-end gap-2">
                            {ach.unlocked ? (
                                <CheckCircle2 size={16} className="text-emerald-500" />
                            ) : (
                                <Lock size={14} className="text-zinc-700" />
                            )}
                            <span className={cn(
                                "text-[10px] font-bold px-1.5 py-0.5 rounded tabular-nums",
                                ach.unlocked ? "bg-emerald-500/10 text-emerald-500" : "bg-zinc-950 text-zinc-600"
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
