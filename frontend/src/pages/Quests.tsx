import React from 'react';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { ProgressBar } from '../components/ui/ProgressBar';
import { apiFetch } from '../api/client';
import { CheckCircle2, Circle, Loader2, Sparkles, Swords, Zap } from 'lucide-react';
import { formatNumber } from '../utils';
import { useUser } from '../context/UserContext';
import { cn } from '../utils';

const QuestItem = ({ quest, onComplete, completing }) => (
  <div key={quest.id} className={cn(
    "p-4 rounded-lg border transition-all",
    quest.claimed
      ? 'border-emerald-900/30 bg-emerald-950/10'
      : 'border-white/5 bg-zinc-900/50'
  )}>
      <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-base">{quest.icon}</span>
                <h3 className="text-sm font-bold text-zinc-100">{quest.name}</h3>
              </div>
              <p className="text-xs text-zinc-500 font-medium">{quest.description}</p>
          </div>
          <div className="flex flex-col items-end">
              <span className="text-sm font-bold text-brand-accent tabular-nums">{formatNumber(quest.reward_shards)}</span>
              <span className="text-[10px] font-medium text-zinc-600 uppercase tracking-tight">Shards</span>
          </div>
      </div>

      <div className="flex items-center gap-4">
          <div className="flex-1">
              <div className="flex justify-between text-[10px] font-medium text-zinc-500 mb-1.5">
                  <span>Progress</span>
                  <span className="tabular-nums">{quest.progress}/{quest.target}</span>
              </div>
              <div className="h-1.5 bg-zinc-950 rounded-full overflow-hidden border border-white/5">
                  <div
                      className={`h-full transition-all duration-500 ${quest.claimed ? 'bg-emerald-500' : 'bg-brand-accent'}`}
                      style={{ width: `${Math.min(100, (quest.progress / quest.target) * 100)}%` }}
                  />
              </div>
          </div>
          
          {quest.claimed ? (
              <div className="w-9 h-9 rounded-md bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500">
                  <CheckCircle2 size={18} />
              </div>
          ) : (
              <button
                  onClick={() => onComplete(quest.id)}
                  disabled={quest.progress < quest.target || completing === quest.id}
                  className={cn(
                      "w-9 h-9 rounded-md flex items-center justify-center transition-all",
                      quest.progress >= quest.target
                      ? 'bg-zinc-100 text-zinc-950 hover:bg-white active:scale-95'
                      : 'bg-zinc-900 text-zinc-700 border border-white/5'
                  )}
                >
                  {completing === quest.id ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
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
}

interface QuestsResponse {
    daily: Quest[];
    weekly: Quest[];
}

export const Quests = () => {
    const { data: questsData, loading, execute: fetchQuests } = useApi<QuestsResponse>('/quests');
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
            addToast(err.message, 'error');
        } finally {
            setCompleting(null);
        }
    };

    if (loading && !questsData) return (
        <div className="px-4 pb-12 pt-6 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-28 bg-zinc-900 rounded-lg animate-pulse border border-white/5" />)}
        </div>
    );

    const allQuests = [
        ...(questsData?.daily || []),
        ...(questsData?.weekly || [])
    ];

    return (
        <div className="pb-32 pt-6">
            <header className="px-4 mb-6">
                <h1 className="text-xl font-bold text-zinc-100">Tasks</h1>
                <p className="text-xs font-medium text-zinc-500">Complete objectives to earn currency</p>
            </header>

            <div className="px-4 space-y-3">
                {allQuests.length > 0 ? (
                    allQuests.map((quest) => (
                        <QuestItem
                            key={quest.id}
                            quest={quest}
                            onComplete={handleComplete}
                            completing={completing}
                        />
                    ))
                ) : !loading && (
                    <div className="p-12 rounded-lg border border-white/5 border-dashed text-center bg-zinc-900/20">
                        <p className="text-xs font-medium text-zinc-500">No active tasks available.</p>
                    </div>
                )}
            </div>
        </div>
    );
};
