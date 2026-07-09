import 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { BadgeCheck, Lock, CheckCircle2, Trophy, Loader2 } from 'lucide-react';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

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
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8">
             <div className="flex items-center gap-3">
                <Skeleton className="w-10 h-10 rounded-xl" />
                <div className="space-y-2">
                    <Skeleton className="h-6 w-40" />
                    <Skeleton className="h-3 w-60" />
                </div>
             </div>
             <div className="space-y-3">
                {[1,2,3,4,5,6].map(i => (
                    <Skeleton key={i} className="h-20 rounded-2xl" />
                ))}
             </div>
        </div>
    );

    if (error && !achievements) return (
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px">
            <ErrorState message={error} onAction={fetchAchievements} />
        </div>
    );

    const sortedAchievements = [...(achievements || [])].sort((a, b) => {
        if (a.unlocked === b.unlocked) return 0;
        return a.unlocked ? -1 : 1;
    });

    const unlockedCount = achievements?.filter(a => a.unlocked).length || 0;
    const totalCount = achievements?.length || 0;
    const progressPercent = totalCount > 0 ? Math.round((unlockedCount / totalCount) * 100) : 0;

    return (
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8 select-none">
            <header className="space-y-6">
                <div className="space-y-1">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                            <BadgeCheck className="text-brand-accent" size={22} />
                        </div>
                        <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Milestones</h1>
                    </div>
                    <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">
                        Documented operational achievements and combat merits.
                    </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    <Card className="p-4 flex flex-col justify-between">
                        <span className="text-[10px] font-black text-neutral-500 uppercase tracking-widest mb-1">Completion</span>
                        <div className="flex items-baseline gap-2">
                            <span className="text-2xl font-black text-white tabular-nums">{progressPercent}%</span>
                            <span className="text-[10px] font-bold text-neutral-600 uppercase tracking-tighter">{unlockedCount} / {totalCount}</span>
                        </div>
                    </Card>
                    <Card className="p-4 flex flex-col justify-between border-brand-accent/10">
                        <span className="text-[10px] font-black text-neutral-500 uppercase tracking-widest mb-1">Active Status</span>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-brand-accent animate-pulse" />
                            <span className="text-sm font-black text-brand-accent uppercase tracking-tight">Sync Active</span>
                        </div>
                    </Card>
                </div>
            </header>

            <div className="space-y-3">
                {sortedAchievements.map((ach) => (
                    <Card
                        key={ach.id}
                        className={cn(
                            "p-4 flex items-center gap-4 transition-all duration-300",
                            !ach.unlocked && "opacity-50 grayscale bg-brand-midnight/50"
                        )}
                    >
                        <div className={cn(
                            "w-14 h-14 rounded-2xl flex items-center justify-center border shrink-0",
                            ach.unlocked
                                ? "bg-brand-accent/10 border-brand-accent/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                                : "bg-brand-surface border-white/5"
                        )}>
                            {ach.unlocked ? (
                                <Trophy size={24} className="text-brand-accent" />
                            ) : (
                                <Lock size={20} className="text-neutral-700" />
                            )}
                        </div>

                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-0.5">
                                <h3 className={cn(
                                    "text-sm font-black uppercase tracking-tight truncate",
                                    ach.unlocked ? "text-white" : "text-neutral-500"
                                )}>
                                    {ach.name}
                                </h3>
                                {ach.unlocked && <Badge variant="success" size="xs" className="rounded-md">SECURED</Badge>}
                            </div>
                            <p className="text-xs text-neutral-500 font-bold uppercase tracking-tight leading-snug line-clamp-2">
                                {ach.description}
                            </p>
                        </div>

                        <div className="shrink-0 flex flex-col items-end gap-2">
                            <div className={cn(
                                "flex items-center gap-1 px-2 py-1 rounded-lg border text-[10px] font-black tabular-nums transition-colors",
                                ach.unlocked
                                    ? "bg-brand-accent/5 border-brand-accent/20 text-brand-accent"
                                    : "bg-brand-midnight border-white/5 text-neutral-700"
                            )}>
                                +{ach.reward_xp} XP
                            </div>
                            {ach.unlocked && <CheckCircle2 size={16} className="text-emerald-500" />}
                        </div>
                    </Card>
                ))}
            </div>

            {loading && achievements && (
                 <div className="flex justify-center py-8">
                    <Loader2 size={24} className="animate-spin text-brand-accent/20" />
                 </div>
            )}
        </div>
    );
};
