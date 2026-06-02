import React from 'react';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { apiFetch, getErrorMessage } from '../api/client';
import { CheckCircle2, Loader2, Target, Zap } from 'lucide-react';
import { formatNumber } from '../utils';
import { useUser } from '../context/UserContext';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';

const QuestItem = ({ quest, onComplete, completing }) => (
  <div key={quest.id} className={cn(
    "p-4 rounded-xl border transition-all shadow-sm",
    quest.locked
      ? 'border-white/5 bg-brand-deep opacity-60'
      :
    quest.claimed
      ? 'border-emerald-500/20 bg-emerald-500/5'
      : 'border-white/5 bg-brand-deep'
  )}>
      <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="w-8 h-8 rounded-lg bg-brand-midnight border border-white/5 flex items-center justify-center text-brand-accent shrink-0">
                  <Target size={16} />
                </span>
                <h3 className="text-base font-bold text-white tracking-tight">{quest.name}</h3>
              </div>
              <p className="text-sm text-neutral-400 font-medium">{quest.description}</p>
          </div>
          <div className="flex flex-col items-end">
              <span className="text-base font-bold text-brand-accent tabular-nums">{formatNumber(quest.reward_shards)}</span>
              <span className="text-xs font-medium text-neutral-500">Shards</span>
          </div>
      </div>

      <div className="flex items-center gap-4">
          <div className="flex-1">
              <div className="flex justify-between text-xs font-medium text-neutral-400 mb-2">
                  <span>Progress</span>
                  <span className="tabular-nums font-semibold">{quest.progress}/{quest.target}</span>
              </div>
              <div className="h-2 bg-brand-midnight rounded-full overflow-hidden border border-white/5">
                  <div
                      className={`h-full transition-all duration-500 ${quest.claimed ? 'bg-emerald-500' : 'bg-brand-accent'}`}
                      style={{ width: `${Math.min(100, (quest.progress / Math.max(quest.target, 1)) * 100)}%` }}
                  />
              </div>
          </div>
          
          {quest.claimed ? (
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 shrink-0">
                  <CheckCircle2 size={20} strokeWidth={2.5} />
              </div>
          ) : (
              <button
                  onClick={() => onComplete(quest.id)}
                  disabled={quest.locked || quest.progress < quest.target || completing === quest.id}
                  className={cn(
                      "h-10 min-w-10 rounded-lg flex items-center justify-center transition-all shrink-0",
                      !quest.locked && quest.progress >= quest.target
                      ? 'bg-white text-brand-midnight hover:bg-neutral-200 active:scale-95 shadow-sm px-3 gap-1.5'
                      : 'bg-brand-midnight text-neutral-600 border border-white/5'
                  )}
                >
                  {completing === quest.id ? <Loader2 size={18} className="animate-spin" /> : !quest.locked && quest.progress >= quest.target ? (
                    <>
                      <Zap size={16} strokeWidth={2.5} />
                      <span className="text-xs font-bold">Claim</span>
                    </>
                  ) : <Zap size={18} strokeWidth={2.5} />}
              </button>
          )}
      </div>
  </div>
);

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
    const [completing, setCompleting] = React.useState(null);

    const handleComplete = async (questId) => {
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
        <div className="px-4 pb-12 pt-6 space-y-3 max-w-2xl mx-auto">
            {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-32 bg-brand-deep rounded-xl animate-pulse border border-white/5" />)}
        </div>
    );

    if (error && !questsData) return (
        <div className="px-4 pb-12 pt-6 max-w-2xl mx-auto">
            <ErrorState message={error} onAction={fetchQuests} />
        </div>
    );

    const renderQuestSection = (title: string, quests: Quest[]) => (
        <section className="space-y-3">
            <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-neutral-300">{title}</h2>
                <span className="text-xs font-semibold text-neutral-500">{quests.filter(q => q.claimed).length}/{quests.length} claimed</span>
            </div>
            {quests.length > 0 ? (
                quests.map((quest) => (
                    <QuestItem
                        key={quest.id}
                        quest={quest}
                        onComplete={handleComplete}
                        completing={completing}
                    />
                ))
            ) : (
                <div className="p-6 rounded-xl border border-white/5 border-dashed text-center bg-brand-deep shadow-sm">
                    <p className="text-sm font-medium text-neutral-500">No {title.toLowerCase()} available.</p>
                </div>
            )}
        </section>
    );

    return (
        <div className="pb-20 pt-4 max-w-2xl mx-auto">
            <header className="px-4 mb-6 border-b border-white/5 pb-4">
                <h1 className="text-xl font-bold text-white tracking-tight mb-1">Tasks</h1>
                <p className="text-sm font-medium text-neutral-400">Complete objectives to earn currency</p>
            </header>

            <div className="px-4 space-y-8">
                {renderQuestSection('Daily tasks', questsData?.daily || [])}
                {renderQuestSection('Weekly tasks', questsData?.weekly || [])}
                {renderQuestSection('Pass missions', questsData?.pass || [])}
            </div>
        </div>
    );
};
