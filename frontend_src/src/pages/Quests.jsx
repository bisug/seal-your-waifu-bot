import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { apiFetch } from '../api';
import { useUser } from '../context/UserContext';
import { CheckCircle2, Shield, Loader2, Sparkles, Target } from 'lucide-react';
import { ProgressBar, useApi } from '../components/UI';
import { useMainButton } from '../hooks/useMainButton';

export const Quests = () => {
  const { refreshUser } = useUser();
  const [claiming, setClaiming] = useState(null);
  const { show: showMain, hide: hideMain, setProgress: setMainProgress } = useMainButton();
  
  const { data: quests, loading, execute: fetchQuests } = useApi('/quests', { 
    initialData: { daily: [], weekly: [] } 
  });

  const claimQuest = async (questId) => {
    setClaiming(questId);
    setMainProgress(true);
    try {
      const res = await apiFetch(`/quests/claim/${questId}`, { method: 'POST' });
      if (res.success) {
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
        fetchQuests();
        refreshUser();
      }
    } catch (err) {
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
      window.Telegram?.WebApp?.showAlert(err.message);
    } finally {
      setClaiming(null);
      setMainProgress(false);
    }
  };

  const claimableQuest = useMemo(() => {
    const all = [...quests.daily, ...quests.weekly];
    return all.find(q => q.progress >= q.target && !q.claimed);
  }, [quests]);

  useEffect(() => {
    if (claimableQuest && !claiming) {
      showMain(`CLAIM: ${claimableQuest.name}`, () => claimQuest(claimableQuest.id));
    } else {
      hideMain();
    }
  }, [claimableQuest, claiming]);

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
          
          <div className="flex justify-between items-center">
             <span className="text-[11px] font-bold text-slate-500 uppercase tracking-tighter">
               {quest.progress} / {quest.target} COMPLETED
             </span>
             
             {isClaimed ? (
               <div className="flex items-center space-x-1 text-brand-neon">
                  <CheckCircle2 size={14} />
                  <span className="text-[11px] font-black uppercase">CLAIMED</span>
               </div>
             ) : isCompleted ? (
                <div className="flex items-center space-x-1 text-brand-neon animate-pulse">
                  <Sparkles size={14} />
                  <span className="text-[11px] font-black uppercase">READY TO CLAIM</span>
                </div>
             ) : (
               <div className="flex items-center space-x-1 text-slate-600">
                  <Target size={14} />
                  <span className="text-[11px] font-black uppercase tracking-widest">IN PROGRESS</span>
               </div>
             )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="pb-32 pt-6 px-4">
      <header className="mb-8 px-2">
        <div className="flex items-center space-x-2 text-brand-neon mb-1 text-[11px]">
          <Sparkles size={16} />
          <span className="font-black uppercase tracking-[0.3em]">Neural Objectives</span>
        </div>
        <h1 className="text-2xl font-black uppercase tracking-tight">Active Quests</h1>
      </header>

      {loading && !quests.daily.length ? (
        <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-neon" /></div>
      ) : (
        <div className="space-y-8">
          <section>
            <h2 className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4 px-2">Daily Assignments</h2>
            <div className="space-y-3">
              {quests.daily.map(q => <QuestItem key={q.id} quest={q} />)}
            </div>
          </section>

          <section>
            <h2 className="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4 px-2">Weekly Challenges</h2>
            <div className="space-y-3">
              {quests.weekly.map(q => <QuestItem key={q.id} quest={q} />)}
            </div>
          </section>
        </div>
      )}
    </div>
  );
};
