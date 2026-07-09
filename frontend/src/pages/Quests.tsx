import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { apiFetch, getErrorMessage } from '../api/client';
import { CheckCircle2, ClipboardList, Gift, Loader2, Target, Trophy, Zap, Sparkles } from 'lucide-react';
import { formatNumber } from '../utils';
import { useUser } from '../context/UserContext';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';

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

const QuestItem = ({ quest, onComplete, completing }: QuestItemProps) => (
  <Card variant="tactical" key={quest.id} className={cn(
    "p-4 group relative overflow-hidden",
    quest.locked ? 'opacity-60 grayscale' : quest.claimed ? 'border-emerald-500/20 bg-emerald-500/[0.02]' : ''
  )}>
      <div className="flex justify-between items-start mb-4 gap-4">
          <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-md bg-white/[0.02] border border-white/[0.05] flex items-center justify-center text-brand-accent shrink-0">
                  <Sparkles size={14} />
                </div>
                <h3 className="text-[13px] font-black text-white tracking-tight uppercase truncate">{quest.name}</h3>
              </div>
              <p className="text-[9px] text-neutral-600 font-bold uppercase tracking-widest line-clamp-1">{quest.description}</p>
          </div>
          <div className="flex flex-col items-end shrink-0">
              <div className="flex items-center gap-1">
                  <span className="text-xs font-black text-white tabular-nums font-mono">{formatNumber(quest.reward_shards)}</span>
                  <Badge variant="warning" size="xs" className="px-1 py-0 border-none bg-amber-500/10">SHARDS</Badge>
              </div>
              <div className="flex items-center gap-1 mt-1">
                  <span className="text-[9px] font-black text-neutral-600 tabular-nums font-mono">+{quest.reward_xp}</span>
                  <span className="text-[8px] font-black text-neutral-800">XP</span>
              </div>
          </div>
      </div>

      <div className="flex items-center gap-4">
          <div className="flex-1">
              <div className="flex justify-between text-[8px] font-black text-neutral-700 uppercase tracking-[0.2em] mb-1.5 px-0.5">
                  <span>PROGRESS</span>
                  <span className="tabular-nums font-mono">{quest.progress} / {quest.target}</span>
              </div>
              <div className="h-1 bg-black/40 rounded-full overflow-hidden border border-white/5">
                  <div
                      className={`h-full transition-all duration-700 ${quest.claimed ? 'bg-emerald-500' : 'bg-brand-accent'}`}
                      style={{ width: `${Math.min(100, (quest.progress / Math.max(quest.target, 1)) * 100)}%` }}
                  />
              </div>
          </div>
          
          <div className="shrink-0">
            {quest.claimed ? (
                <div className="w-8 h-8 rounded-md bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500">
                    <CheckCircle2 size={16} strokeWidth={3} />
                </div>
            ) : (
                <Button
                    variant={quest.progress >= quest.target ? "tactical" : "secondary"}
                    size="sm"
                    onClick={() => onComplete(quest.id)}
                    disabled={quest.locked || quest.progress < quest.target || completing === quest.id}
                    className="h-8 px-3"
                    isLoading={completing === quest.id}
                  >
                    {quest.progress >= quest.target ? 'CLAIM' : <Gift size={14} />}
                </Button>
            )}
          </div>
      </div>
  </Card>
);

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
        try {
            const res = await apiFetch(`/quests/claim/${questId}`, { method: 'POST' });
            addToast(`Mission complete! +${res.reward_shards} Shards`, 'success');
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
            triggerRefresh();
            fetchQuests();
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
        } finally {
            setCompleting(null);
        }
    };

    if (loading && !questsData) return (
        <div className="pb-24 pt-4 max-w-2xl mx-auto adaptive-px space-y-4">
            <Skeleton className="h-6 w-40 rounded-md" />
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-lg" />)}
        </div>
    );

    if (error && !questsData) return (
        <div className="px-4 pb-12 pt-4 max-w-2xl mx-auto">
            <ErrorState message={error} onAction={fetchQuests} />
        </div>
    );

    const renderQuestSection = (title: string, quests: Quest[]) => (
        <section className="space-y-3">
            <div className="flex items-center justify-between px-1">
                <h2 className="text-[9px] font-black text-neutral-700 uppercase tracking-[0.3em]">{title}</h2>
                <Badge variant="tactical" size="xs" className="opacity-60">
                    {quests.filter(q => q.claimed).length} / {quests.length} COMPLETED
                </Badge>
            </div>
            {quests.length > 0 ? (
                <div className="space-y-2">
                    {quests.map((quest) => (
                        <QuestItem
                            key={quest.id}
                            quest={quest}
                            onComplete={handleComplete}
                            completing={completing}
                        />
                    ))}
                </div>
            ) : (
                <Card variant="tactical" className="p-6 border-dashed border-white/5 bg-transparent text-center flex flex-col items-center">
                    <p className="text-[8px] font-black text-neutral-800 uppercase tracking-[0.3em]">No {title.toLowerCase()} available</p>
                </Card>
            )}
        </section>
    );

    return (
        <div className="pb-24 pt-4 max-w-2xl mx-auto adaptive-px space-y-6">
            <header className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                   <div className="w-9 h-9 rounded-md bg-brand-accent/5 border border-brand-accent/20 flex items-center justify-center text-brand-accent">
                        <ClipboardList size={20} />
                   </div>
                   <h1 className="text-lg font-black text-white tracking-tighter uppercase">Daily Missions</h1>
                </div>
                <p className="text-[10px] font-bold text-neutral-600 uppercase tracking-widest leading-relaxed">
                    COMPLETE OBJECTIVES TO SECURE ASSETS AND XP.
                </p>
            </header>

            <div className="space-y-8">
                {renderQuestSection('Operational Daily', questsData?.daily || [])}
                {renderQuestSection('Strategic Weekly', questsData?.weekly || [])}
                {renderQuestSection('Waifu Pass Objectives', questsData?.pass || [])}
            </div>
        </div>
    );
};
