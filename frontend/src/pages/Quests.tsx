import React from 'react';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { ProgressBar } from '../components/ui/ProgressBar';
import { apiFetch } from '../api/client';
import { CheckCircle2, Circle, Loader2, Sparkles, Swords, Zap } from 'lucide-react';
import { formatNumber } from '../utils';
import { useUser } from '../context/UserContext';

const QuestItem = ({ quest, onComplete, completing }) => (
  <div key={quest.id} className={`glass-panel p-6 rounded-[2.5rem] border transition-all ${quest.claimed ? 'border-brand-accent/20 bg-brand-accent/[0.02]' : 'border-white/5'}`}>
      <div className="flex justify-between items-start mb-5">
          <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xl">{quest.icon}</span>
                <h3 className="text-sm font-black text-white uppercase italic tracking-tight">{quest.name}</h3>
              </div>
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{quest.description}</p>
          </div>
          <div className="flex flex-col items-end">
              <span className="text-[13px] font-black text-brand-accent">⧫ {formatNumber(quest.reward_shards)}</span>
              <span className="text-[7px] font-black text-slate-600 uppercase tracking-widest">Shards</span>
              <span className="text-[10px] font-bold text-slate-400 mt-1">+{quest.reward_xp} XP</span>
          </div>
      </div>

      <div className="flex items-center gap-4">
          <div className="flex-1">
              <div className="flex justify-between text-[8px] font-black uppercase tracking-widest text-slate-600 mb-1.5">
                  <span>Progress</span>
                  <span>{quest.progress}/{quest.target}</span>
              </div>
              <div className="h-1.5 bg-black/40 rounded-full overflow-hidden">
                  <div
                      className={`h-full transition-all duration-1000 ${quest.claimed ? 'bg-brand-accent' : 'bg-brand-accent/50'}`}
                      style={{ width: `${Math.min(100, (quest.progress / quest.target) * 100)}%` }}
                  />
              </div>
          </div>
          
          {quest.claimed ? (
              <div className="w-10 h-10 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center text-brand-accent">
                  <CheckCircle2 size={20} />
              </div>
          ) : (
              <button
                  onClick={() => onComplete(quest.id)}
                  disabled={quest.progress < quest.target || completing === quest.id}
                  className={`w-10 h-10 rounded-2xl flex items-center justify-center transition-all ${
                      quest.progress >= quest.target
                      ? 'bg-brand-accent text-brand-midnight shadow-lg shadow-brand-accent/30 active:scale-95'
                      : 'bg-white/5 text-slate-700'
                  }`}
                >
                  {completing === quest.id ? <Loader2 size={18} className="animate-spin" /> : <Zap size={18} />}
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
            addToast(`QUEST SECURED: +${res.reward_xp} XP & +${res.reward_shards} Shards`, 'success');
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
            triggerRefresh();
            fetchQuests();
        } catch (err) {
            addToast(err.message, 'error');
        } finally {
            setCompleting(null);
        }
    };

    if (loading && !questsData) return (
        <div className="px-6 pb-12 pt-4 space-y-4">
            {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-32 bg-white/[0.03] rounded-3xl animate-pulse" />)}
        </div>
    );

    const allQuests = [
        ...(questsData?.daily || []),
        ...(questsData?.weekly || [])
    ];

    return (
        <div className="pb-32 pt-6">
            <header className="px-6 mb-8">
                <h1 className="text-3xl font-black italic uppercase tracking-tighter text-white">Directives</h1>
                <p className="text-[10px] font-bold text-brand-accent uppercase tracking-[0.4em] mt-1">Complete tasks to earn rewards</p>
            </header>

            <div className="px-4 space-y-4">
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
                    <div className="glass-panel p-12 rounded-[3rem] border border-white/5 text-center">
                        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">No active directives found.</p>
                    </div>
                )}
            </div>
        </div>
    );
};
