import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { apiFetch } from '../api';
import { useUser } from '../context/UserContext';
import { toast } from 'react-hot-toast';
import { CheckCircle2, Shield, Loader2, Sparkles, Target } from 'lucide-react';
import { ProgressBar, useApi } from '../components/UI';
import { formatNumber } from '../utils';

export const Quests = () => {
  const { refreshUser } = useUser();
  const [claiming, setClaiming] = useState(null);
  
  const { data: quests, loading, execute: fetchQuests } = useApi('/quests', { 
    initialData: { daily: [], weekly: [] } 
  });

  const claimQuest = async (questId) => {
    setClaiming(questId);
    try {
      const allQuests = [...(quests?.daily || []), ...(quests?.weekly || [])];
      const questInfo = allQuests.find(q => q.id === questId);
      const rewardXp = questInfo?.reward_xp || 0;
      
      const res = await apiFetch(`/quests/claim/${questId}`, { method: 'POST' });
      if (res.success) {
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
        toast.success(`Reward: +${rewardXp} XP`);
        fetchQuests();
        refreshUser();
      }
    } catch (err) {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
      toast.error(err.message || 'Failed to claim');
    } finally {
      setClaiming(null);
    }
  };

  const claimableQuest = useMemo(() => {
    const daily = Array.isArray(quests?.daily) ? quests.daily : [];
    const weekly = Array.isArray(quests?.weekly) ? quests.weekly : [];
    const all = [...daily, ...weekly];
    return all.find(q => q.progress >= q.target && !q.claimed);
  }, [quests]);

  const QuestItem = ({ quest }) => {
    const isCompleted = quest.progress >= quest.target;
    const isClaimed = quest.claimed;

    return (
      <div className={`glass-panel p-5 rounded-2xl border transition-all ${
        isClaimed ? 'border-brand-neon/10 opacity-60' : 
        isCompleted ? 'border-brand-neon shadow-[0_0_20px_rgba(0,255,255,0.1)]' : 
        'border-white/5'
      }`}>
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1 text-left">
            <h3 className="text-[11px] font-black uppercase tracking-widest mb-1">{quest.name}</h3>
            <p className="text-[11px] text-slate-500 font-bold uppercase">{quest.description}</p>
          </div>
          <div className="flex items-center space-x-1.5 bg-brand-neon/10 px-2 py-0.5 rounded-lg border border-brand-neon/20">
             <Shield size={12} className="text-brand-neon" />
             <span className="text-[11px] font-black text-brand-neon">+{quest.reward_xp} XP</span>
          </div>
        </div>

        <div className="space-y-4">
          <ProgressBar current={quest.progress} total={quest.target} />
          
          <div className="flex justify-between items-center bg-white/5 p-3 rounded-xl border border-white/5">
             <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
               {formatNumber(quest.progress)} / {formatNumber(quest.target)} COMPLETE
             </span>
             
             {isClaimed ? (
               <div className="flex items-center space-x-1.5 text-slate-600 opacity-60">
                  <CheckCircle2 size={12} />
                  <span className="text-[10px] font-black uppercase">CLAIMED</span>
               </div>
             ) : isCompleted ? (
                <motion.button 
                  whileTap={{ scale: 0.95 }}
                  onClick={() => claimQuest(quest.id)}
                  disabled={claiming === quest.id}
                  className="flex items-center space-x-2 bg-brand-neon px-4 py-2 rounded-lg text-brand-midnight text-[10px] font-black uppercase tracking-widest shadow-lg shadow-brand-neon/20 hover:scale-105 transition-all"
                >
                  {claiming === quest.id ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                  <span>{claiming === quest.id ? 'CLAIMING...' : 'CLAIM REWARD'}</span>
                </motion.button>
             ) : (
                <div className="flex items-center space-x-1.5 text-slate-700">
                  <Target size={12} />
                  <span className="text-[10px] font-black uppercase tracking-[0.2em]">ACTIVE</span>
                </div>
             )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="pb-8 pt-6 px-4">
      <header className="mb-8 px-2">
        <div className="flex items-center space-x-2 text-brand-neon mb-1 text-[11px]">
          <Sparkles size={16} />
          <span className="font-black uppercase tracking-[0.3em]">Harem Quests</span>
        </div>
        <h1 className="text-2xl font-black uppercase tracking-tight">Active Quests</h1>
      </header>

      {loading && !(quests?.daily?.length) ? (
        <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-neon" /></div>
      ) : (
      <div className="space-y-8">
          <section>
            <h2 className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4 px-2">Daily Quests</h2>
            <div className="space-y-3">
              {(quests?.daily || []).map(q => <QuestItem key={q.id} quest={q} />)}
            </div>
          </section>

          <section>
            <h2 className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4 px-2">Weekly Challenges</h2>
            <div className="space-y-3">
              {(quests?.weekly || []).map(q => <QuestItem key={q.id} quest={q} />)}
            </div>
          </section>
        </div>
      )}
    </div>
  );
};
