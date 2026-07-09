import 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { BadgeCheck, Lock, CheckCircle2, Trophy, Loader2, Target, ShieldCheck, Sparkles, Activity } from 'lucide-react';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';

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
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-10">
             <div className="flex items-center gap-4">
                <Skeleton className="w-12 h-12 rounded-2xl" />
                <div className="space-y-2">
                    <Skeleton className="h-8 w-48 rounded-lg" />
                    <Skeleton className="h-4 w-64 rounded-lg opacity-50" />
                </div>
             </div>
             <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-24 rounded-2xl" />
                <Skeleton className="h-24 rounded-2xl" />
             </div>
             <div className="space-y-3">
                {[1,2,3,4,5,6].map(i => (
                    <Skeleton key={i} className="h-24 rounded-2xl" />
                ))}
             </div>
        </div>
    );

    if (error && !achievements) return (
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px">
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
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-10 select-none">
            <header className="space-y-8">
                <div className="space-y-2">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                            <BadgeCheck className="text-brand-accent" size={26} />
                        </div>
                        <div className="flex flex-col gap-1">
                           <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Milestones</h1>
                           <div className="flex items-center gap-2">
                              <Target size={11} className="text-neutral-600" />
                              <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                                OPERATIONAL ACHIEVEMENTS & CLEARANCE
                              </p>
                           </div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <Card variant="tactical" className="p-5 flex flex-col justify-between border-white/[0.04] bg-white/[0.01]">
                        <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.25em] mb-3">Sync Progress</span>
                        <div className="flex items-baseline gap-3">
                            <span className="text-3xl font-black text-white tabular-nums leading-none font-mono drop-shadow-md">{progressPercent}%</span>
                            <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest tabular-nums opacity-60 font-mono">{unlockedCount} / {totalCount}</span>
                        </div>
                        <div className="mt-4 h-1 bg-white/[0.03] rounded-full overflow-hidden">
                           <motion.div initial={{ width: 0 }} animate={{ width: `${progressPercent}%` }} transition={{ duration: 1.5, ease: "easeOut" }} className="h-full bg-brand-accent shadow-[0_0_10px_rgba(59,130,246,0.3)]" />
                        </div>
                    </Card>
                    <Card variant="tactical" className="p-5 flex flex-col justify-between border-brand-accent/20 bg-brand-accent/[0.02]">
                        <span className="text-[9px] font-black text-brand-accent/60 uppercase tracking-[0.25em] mb-3">Security Level</span>
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-brand-accent/10 flex items-center justify-center shadow-inner">
                               <Activity size={20} className="text-brand-accent" />
                            </div>
                            <div className="flex flex-col">
                               <span className="text-xs font-black text-white uppercase tracking-tight leading-none mb-1">PROTO_v2.4</span>
                               <span className="text-[9px] font-black text-brand-accent uppercase tracking-widest leading-none">ACTIVE SYNC</span>
                            </div>
                        </div>
                        <div className="mt-4 flex items-center gap-1.5">
                            <div className="w-1 h-1 rounded-full bg-success shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                            <span className="text-[8px] font-black text-success/60 uppercase tracking-widest">AUTHORIZED ACCESS</span>
                        </div>
                    </Card>
                </div>
            </header>

            <div className="space-y-3">
                <AnimatePresence mode="popLayout">
                    {sortedAchievements.map((ach) => (
                        <motion.div layout key={ach.id} initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}>
                            <Card
                                variant="tactical"
                                className={cn(
                                    "p-5 flex items-center gap-5 transition-all duration-500 border-white/[0.04]",
                                    !ach.unlocked ? "opacity-30 grayscale bg-white/[0.01] border-transparent" : "bg-white/[0.02] hover:border-brand-accent/20 hover:bg-white/[0.03]"
                                )}
                            >
                                <div className="relative">
                                    <div className={cn(
                                        "w-16 h-16 rounded-2xl flex items-center justify-center border shrink-0 transition-all duration-700 relative z-10 group-hover:scale-105 shadow-xl",
                                        ach.unlocked
                                            ? "bg-brand-accent/10 border-brand-accent/30 shadow-[0_0_20px_rgba(59,130,246,0.1)]"
                                            : "bg-brand-midnight border-white/[0.05]"
                                    )}>
                                        {ach.unlocked ? (
                                            <Trophy size={28} className="text-brand-accent drop-shadow-md" />
                                        ) : (
                                            <Lock size={22} className="text-neutral-800" />
                                        )}
                                    </div>
                                    {ach.unlocked && (
                                        <div className="absolute -inset-2 bg-brand-accent/10 blur-xl rounded-full opacity-20 group-hover:opacity-40 transition-opacity" />
                                    )}
                                </div>

                                <div className="flex-1 min-w-0 space-y-2">
                                    <div className="flex items-center gap-3">
                                        <h3 className={cn(
                                            "text-sm font-black uppercase tracking-tight truncate leading-none",
                                            ach.unlocked ? "text-white" : "text-neutral-600"
                                        )}>
                                            {ach.name}
                                        </h3>
                                        {ach.unlocked && (
                                            <Badge variant="success" size="xs" className="rounded-md px-2 py-0.5 border-none font-black tracking-widest text-[8px] bg-success/10 text-success">
                                                CLEAR
                                            </Badge>
                                        )}
                                    </div>
                                    <p className={cn(
                                        "text-[11px] font-bold uppercase tracking-widest leading-snug line-clamp-2",
                                        ach.unlocked ? "text-neutral-500" : "text-neutral-700"
                                    )}>
                                        {ach.description}
                                    </p>
                                </div>

                                <div className="shrink-0 flex flex-col items-end gap-3 pl-4 border-l border-white/[0.03]">
                                    <div className={cn(
                                        "flex items-center gap-2 px-3 py-1.5 rounded-xl border text-[10px] font-black tabular-nums transition-all font-mono leading-none",
                                        ach.unlocked
                                            ? "bg-brand-accent/10 border-brand-accent/20 text-brand-accent shadow-[0_0_10px_rgba(59,130,246,0.1)]"
                                            : "bg-brand-midnight border-white/[0.05] text-neutral-800"
                                    )}>
                                        +{ach.reward_xp} XP
                                    </div>
                                    {ach.unlocked ? (
                                        <div className="w-6 h-6 rounded-lg bg-success/10 flex items-center justify-center text-success border border-success/20">
                                            <CheckCircle2 size={14} strokeWidth={3} />
                                        </div>
                                    ) : (
                                        <div className="w-6 h-6 rounded-lg bg-white/[0.02] flex items-center justify-center text-neutral-900 border border-white/[0.03]">
                                            <ShieldCheck size={14} strokeWidth={2} />
                                        </div>
                                    )}
                                </div>
                            </Card>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {loading && achievements && (
                 <div className="flex justify-center py-12">
                    <div className="relative">
                       <Loader2 size={32} className="animate-spin text-brand-accent/40" />
                       <div className="absolute inset-0 bg-brand-accent/10 blur-2xl rounded-full" />
                    </div>
                 </div>
            )}

            <div className="flex items-center justify-center gap-3 opacity-20 py-4">
               <Sparkles size={12} className="text-brand-accent" />
               <span className="text-[9px] font-black uppercase tracking-[0.4em] text-white">Records Synced</span>
            </div>
        </div>
    );
};
