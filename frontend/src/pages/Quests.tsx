import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { apiFetch, getErrorMessage } from '../api/client';
import { CheckCircle2, ClipboardList, Gift, Target, Zap, Sparkles, Trophy, ChevronRight, Lock } from 'lucide-react';
import { formatNumber } from '../utils';
import { useUser } from '../context/UserContext';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { motion, AnimatePresence } from 'framer-motion';

interface Quest {
    id: string;
    name: string;
    description: string;
    icon: string;
    reward_xp: number;
    reward_shards: number;
    progress: number;
    target: number;
    claimed: boolean;
    locked?: boolean;
}

interface QuestItemProps {
    quest: Quest;
    onComplete: (questId: string) => void;
    completing: string | null;
}

const QuestItem = ({ quest, onComplete, completing }: QuestItemProps) => {
  const isComplete = quest.progress >= quest.target;
  const progressPercent = Math.min(100, (quest.progress / Math.max(quest.target, 1)) * 100);

  return (
    <motion.div layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Card variant="tactical" className={cn(
            "p-5 group relative overflow-hidden transition-all duration-500",
            quest.locked && 'opacity-40 grayscale',
            quest.claimed && 'border-success/20 bg-success/[0.02]'
        )}>
            <div className="flex justify-between items-start mb-5 gap-4">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2.5 mb-1.5">
                        <div className={cn(
                            "w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border transition-colors duration-300",
                            isComplete ? "bg-success/10 border-success/20 text-success" : "bg-brand-midnight border-white/[0.05] text-brand-accent"
                        )}>
                        <Target size={16} strokeWidth={2.5} />
                        </div>
                        <h3 className="text-sm font-black text-white tracking-tight uppercase truncate drop-shadow-sm">{quest.name}</h3>
                    </div>
                    <p className="text-[10px] text-neutral-500 font-bold uppercase tracking-widest line-clamp-1 pl-1">{quest.description}</p>
                </div>
                <div className="flex flex-col items-end shrink-0 pt-1">
                    <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/[0.02] border border-white/[0.05]">
                        <span className="text-xs font-black text-white tabular-nums font-mono leading-none">{formatNumber(quest.reward_shards)}</span>
                        <span className="text-[8px] font-black text-amber-500 uppercase tracking-widest leading-none">SHARDS</span>
                    </div>
                    <div className="flex items-center gap-1 mt-1.5 px-1">
                        <span className="text-[9px] font-black text-neutral-600 tabular-nums font-mono">+{quest.reward_xp}</span>
                        <span className="text-[8px] font-black text-neutral-800 uppercase tracking-tighter">XP</span>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-5">
                <div className="flex-1">
                    <div className="flex justify-between text-[9px] font-black text-neutral-700 uppercase tracking-[0.25em] mb-2 px-1">
                        <span>MISSION_PROGRESS</span>
                        <span className="tabular-nums font-mono text-white/40">{quest.progress} <span className="opacity-30">/</span> {quest.target}</span>
                    </div>
                    <div className="h-2 bg-black/60 rounded-full overflow-hidden border border-white/[0.03] p-[1px]">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${progressPercent}%` }}
                            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
                            className={cn(
                                'h-full rounded-full relative shadow-[0_0_10px_rgba(0,0,0,0.5)]',
                                quest.claimed ? 'bg-success shadow-emerald-500/20' : 'bg-brand-accent shadow-brand-accent/20'
                            )}
                        >
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent w-full animate-[shimmer_2s_infinite]" />
                        </motion.div>
                    </div>
                </div>

                <div className="shrink-0 pt-4">
                    {quest.claimed ? (
                        <div className="w-10 h-10 rounded-xl bg-success/10 border border-success/20 flex items-center justify-center text-success shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                            <CheckCircle2 size={20} strokeWidth={3} />
                        </div>
                    ) : (
                        <Button
                            variant={isComplete ? "tactical" : "secondary"}
                            size="sm"
                            onClick={() => onComplete(quest.id)}
                            disabled={quest.locked || !isComplete || completing === quest.id}
                            className="h-10 px-6 rounded-xl font-black text-[10px] tracking-widest shadow-lg"
                            isLoading={completing === quest.id}
                        >
                            {isComplete ? 'SECURE REWARD' : <Lock size={16} />}
                        </Button>
                    )}
                </div>
            </div>
        </Card>
    </motion.div>
  );
};

interface QuestsResponse {
    daily: Quest[];
    weekly: Quest[];
    pass: Quest[];
    pass_type: string;
}

export const Quests = () => {
    const { data: questsData, loading, error, execute: fetchQuests } = useApi<QuestsResponse>('/quests');
    const { addToast } = useToast();
    const { triggerRefresh } = useUser();
    const [completing, setCompleting] = useState<string | null>(null);

    const handleComplete = async (questId: string) => {
        setCompleting(questId);
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
        try {
            const res = await apiFetch(`/quests/claim/${questId}`, { method: 'POST' });
            addToast(`Mission complete! +${res.reward_shards} Shards secured.`, 'success');
            triggerRefresh();
            fetchQuests();
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
        } finally {
            setCompleting(null);
        }
    };

    if (loading && !questsData) return (
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-6">
            <Skeleton className="h-10 w-48 rounded-lg" />
            <Skeleton className="h-4 w-64 rounded-lg opacity-50 mb-8" />
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-2xl" />)}
        </div>
    );

    if (error && !questsData) return (
        <div className="px-5 pb-32 pt-8 max-w-2xl mx-auto">
            <ErrorState message={error} onAction={fetchQuests} />
        </div>
    );

    const renderQuestSection = (title: string, quests: Quest[]) => (
        <section className="space-y-5">
            <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                    <h2 className="text-[11px] font-black text-neutral-600 uppercase tracking-[0.3em]">{title}</h2>
                    <div className="h-1 w-1 rounded-full bg-neutral-800" />
                </div>
                <Badge variant="tactical" size="xs" className="opacity-40 font-mono">
                    {quests.filter(q => q.claimed).length}<span className="mx-1 opacity-40">/</span>{quests.length} COMPLETED
                </Badge>
            </div>
            {quests.length > 0 ? (
                <div className="space-y-3">
                    <AnimatePresence mode="popLayout">
                        {quests.map((quest) => (
                            <QuestItem
                                key={quest.id}
                                quest={quest}
                                onComplete={handleComplete}
                                completing={completing}
                            />
                        ))}
                    </AnimatePresence>
                </div>
            ) : (
                <Card variant="tactical" className="py-12 border-dashed border-white/[0.08] bg-white/[0.01] text-center flex flex-col items-center justify-center space-y-3">
                    <div className="w-12 h-12 rounded-full border border-white/5 flex items-center justify-center opacity-20">
                        <Trophy size={20} />
                    </div>
                    <p className="text-[9px] font-black text-neutral-700 uppercase tracking-[0.4em]">Section Empty</p>
                </Card>
            )}
        </section>
    );

    return (
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-12">
            <header className="space-y-2">
                <div className="flex items-center gap-4">
                   <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                        <ClipboardList size={26} className="text-brand-accent" />
                   </div>
                   <div className="flex flex-col gap-1">
                      <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Missions</h1>
                      <div className="flex items-center gap-2">
                         <Sparkles size={11} className="text-brand-accent animate-pulse" />
                         <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                            OPERATIONAL OBJECTIVES & BOUNTIES
                         </p>
                      </div>
                   </div>
                </div>
            </header>

            <div className="space-y-12">
                {renderQuestSection('DAILY OPERATIONS', questsData?.daily || [])}
                {renderQuestSection('STRATEGIC WEEKLY', questsData?.weekly || [])}
                {renderQuestSection('WAIFU PASS CLEARANCE', questsData?.pass || [])}
            </div>
        </div>
    );
};
