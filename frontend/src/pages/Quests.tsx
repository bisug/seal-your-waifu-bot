import { useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { apiFetch, getErrorMessage } from '../api/client';
import { CheckCircle2, ClipboardList, Gift, Loader2, Target, Trophy, Zap } from 'lucide-react';
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
  <Card key={quest.id} className={cn(
    "p-4 group relative overflow-hidden",
    quest.locked ? 'opacity-60 grayscale' : quest.claimed ? 'border-emerald-500/30 bg-emerald-500/5' : ''
  )}>
      <div className="flex justify-between items-start mb-4 gap-4">
          <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-lg bg-brand-surface border border-white/5 flex items-center justify-center text-brand-accent shrink-0">
                  <Target size={16} />
                </div>
                <h3 className="text-sm font-black text-white tracking-tight uppercase truncate">{quest.name}</h3>
              </div>
              <p className="text-[11px] text-neutral-500 font-bold uppercase tracking-wider line-clamp-1">{quest.description}</p>
          </div>
          <div className="flex flex-col items-end shrink-0">
              <div className="flex items-center gap-1">
                  <span className="text-sm font-black text-white tabular-nums">{formatNumber(quest.reward_shards)}</span>
                  <Badge variant="warning" size="xs" className="px-1 py-0">SHARDS</Badge>
              </div>
              <div className="flex items-center gap-1 mt-1">
                  <span className="text-[10px] font-black text-neutral-500 tabular-nums">+{quest.reward_xp}</span>
                  <span className="text-[8px] font-black text-neutral-600">XP</span>
              </div>
          </div>
      </div>

      <div className="flex items-center gap-4">
          <div className="flex-1">
              <div className="flex justify-between text-[9px] font-black text-neutral-500 uppercase tracking-widest mb-1.5 px-0.5">
                  <span>Progress</span>
                  <span className="tabular-nums">{quest.progress} / {quest.target}</span>
              </div>
              <div className="h-1.5 bg-brand-surface rounded-full overflow-hidden border border-white/5">
                  <div
                      className={`h-full transition-all duration-700 ${quest.claimed ? 'bg-emerald-500' : 'bg-brand-accent'}`}
                      style={{ width: `${Math.min(100, (quest.progress / Math.max(quest.target, 1)) * 100)}%` }}
                  />
              </div>
          </div>
          
          <div className="shrink-0">
            {quest.claimed ? (
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500">
                    <CheckCircle2 size={20} strokeWidth={3} />
                </div>
            ) : (
                <Button
                    variant={quest.progress >= quest.target ? "primary" : "secondary"}
                    size="sm"
                    onClick={() => onComplete(quest.id)}
                    disabled={quest.locked || quest.progress < quest.target || completing === quest.id}
                    className="h-10 px-4 rounded-xl font-black text-[10px] uppercase tracking-widest"
                    isLoading={completing === quest.id}
                  >
                    {quest.progress >= quest.target ? 'Claim' : <Gift size={16} />}
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
            addToast(`Quest completed! +${res.reward_shards} Shards`, 'success');
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
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-4">
            <Skeleton className="h-8 w-48 rounded-lg" />
            {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32 rounded-2xl" />)}
        </div>
    );

    if (error && !questsData) return (
        <div className="px-4 pb-12 pt-6 max-w-2xl mx-auto">
            <ErrorState message={error} onAction={fetchQuests} />
        </div>
    );

    const renderQuestSection = (title: string, quests: Quest[]) => (
        <section className="space-y-4">
            <div className="flex items-center justify-between px-1">
                <h2 className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em]">{title}</h2>
                <Badge variant="secondary" size="xs" className="rounded-lg font-black tracking-widest">
                    {quests.filter(q => q.claimed).length} / {quests.length} COMPLETE
                </Badge>
            </div>
            {quests.length > 0 ? (
                <div className="space-y-3">
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
                <Card className="p-8 border-dashed bg-brand-deep/30 text-center flex flex-col items-center">
                    <p className="text-[10px] font-black text-neutral-600 uppercase tracking-widest">No {title.toLowerCase()} available</p>
                </Card>
            )}
        </section>
    );

    return (
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8">
            <header className="space-y-1">
                <div className="flex items-center gap-3">
                   <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                        <ClipboardList className="text-brand-accent" size={22} />
                   </div>
                   <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Daily Tasks</h1>
                </div>
                <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">
                    Complete tactical objectives to secure rewards and XP.
                </p>
            </header>

            <div className="space-y-10">
                {renderQuestSection('Operational Daily', questsData?.daily || [])}
                {renderQuestSection('Strategic Weekly', questsData?.weekly || [])}
                {renderQuestSection('Pass Objectives', questsData?.pass || [])}
            </div>
        </div>
    );
};
