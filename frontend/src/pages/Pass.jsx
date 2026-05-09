import React from 'react';
import { motion } from 'framer-motion';
import { Award, Lock, Sparkles, ChevronRight, Loader2, CheckCircle2 } from 'lucide-react';
import { apiFetch } from '../api';
import { useUser } from '../context/UserContext';
import { useApi, useToast } from '../components/UI';


export const Pass = () => {
  const { user, refreshUser } = useUser();
  const { addToast } = useToast();
  const { data: passData, loading: passLoading, execute: fetchPassData } = useApi('/pass_data');
  const [claiming, setClaiming] = React.useState(null);
  const [upgrading, setUpgrading] = React.useState(false);

  const handleClaim = async (level) => {
    setClaiming(level);
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
    try {
      const res = await apiFetch(`/claim_level/${level}`, { method: 'POST' });
      if (res.status === 'success') {
        addToast(`CLAIMED: ${res.shards} SHARDS & ${res.eggs} EGGS`, 'success');
        await fetchPassData();
        await refreshUser();
      }
    } catch (err) {
      addToast(err.message || 'Claim failed', 'error');
    } finally {
      setClaiming(null);
    }
  };

  const handleUpgrade = async (tier) => {
    setUpgrading(true);
    try {
      const res = await apiFetch(`/shop/upgrade_pass/${tier}`, { method: 'POST' });
      if (res.status === 'success') {
        addToast(`${tier.toUpperCase()} PROTOCOL ACTIVATED`, 'success');
        await fetchPassData();
        await refreshUser();
      }
    } catch (err) {
      addToast(err.message || 'Upgrade failed', 'error');
    } finally {
      setUpgrading(false);
    }
  };

  if (passLoading || !passData) return (
    <div className="flex items-center justify-center min-h-[60vh]"><Loader2 className="animate-spin text-brand-accent" /></div>
  );

  const milestones = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
  const userLevel = passData.level || 0;
  const claimedLevels = passData.claimed_levels || [];

  return (
    <div className="pb-8 pt-6 px-4 uppercase tracking-[0.2em] font-black">
      <header className="mb-10 px-2 flex justify-between items-end">
        <div>
           <div className="flex items-center space-x-2 text-brand-accent mb-1">
             <Sparkles size={16} />
             <span className="text-[10px]">Neural Protocol</span>
           </div>
           <h1 className="text-[clamp(1.25rem,5vw,1.75rem)] tracking-tight">{passData.season_name || 'Season 1'} Pass</h1>
        </div>
        <div className="bg-brand-midnight border border-white/5 px-3 py-1.5 rounded-xl">
           <p className="text-[8px] text-slate-500 mb-0.5">MATRIX LEVEL</p>
           <p className="text-lg font-black text-brand-neon leading-none">{userLevel}</p>
        </div>
      </header>

      <div className="space-y-6 relative ml-4">
        <div className="absolute left-6 top-4 bottom-4 w-0.5 bg-white/5" />
        
        {milestones.map((lvl) => {
          const isReached = userLevel >= lvl;
          const isClaimed = Array.isArray(claimedLevels) ? claimedLevels.includes(lvl) : false;
          const track = passData.tracks?.[lvl];
          if (!track) return null;
          const reward = track[passData.pass_type] ?? track['free'];
          if (!reward) return null;
          const rewardLabel = reward.type === 'shards' ? `${reward.amount} Shards` : `${reward.tier === 2 ? 'Rare' : 'Common'} Egg`;

          return (
            <motion.div
              key={lvl}
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="flex items-center space-x-3 group"
            >
              <div className={`relative z-10 w-12 h-12 rounded-2xl flex items-center justify-center border-2 transition-all ${
                isReached ? 'border-brand-neon bg-brand-neon/10 text-brand-neon shadow-lg shadow-brand-neon/20' : 'border-white/10 bg-white/5 text-slate-700'
              }`}>
                <span className="text-xs font-black">{lvl}</span>
              </div>

              <div className={`flex-1 glass-panel p-4 rounded-2xl border transition-all flex items-center justify-between ${isReached ? 'border-white/10' : 'border-white/5 opacity-50'}`}>
                <div className="text-left">
                  <p className="text-[12px] tracking-tight text-white">{rewardLabel}</p>
                  <div className="flex items-center space-x-1.5 mt-0.5">
                     <Award size={10} className={isReached ? "text-brand-neon" : "text-slate-600"} />
                     <span className="text-[8px] text-slate-500 font-bold uppercase">{reward.type} REWARD</span>
                  </div>
                </div>
                
                {isClaimed ? (
                  <CheckCircle2 size={18} className="text-brand-neon" />
                ) : isReached ? (
                  <button 
                    onClick={() => handleClaim(lvl)}
                    disabled={claiming === lvl}
                    className="bg-brand-neon text-brand-midnight text-[9px] font-black px-3 py-1.5 rounded-lg active:scale-95 transition-all"
                  >
                    {claiming === lvl ? <Loader2 size={12} className="animate-spin" /> : 'CLAIM'}
                  </button>
                ) : (
                  <Lock size={16} className="text-slate-700" />
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
      
      <div className="mt-12 p-6 glass-panel rounded-3xl border border-brand-neon/20 bg-brand-neon/[0.02] text-center">
         <p className="text-[10px] text-slate-500 mb-2 uppercase tracking-widest">
           {passData.pass_type === 'elite' ? 'ELITE STATUS ACTIVE' : passData.pass_type === 'premium' ? 'PREMIUM STATUS ACTIVE' : 'UPGRADE FOR BETTER REWARDS'}
         </p>
         
         {passData.pass_type === 'free' ? (
           <button 
             onClick={() => handleUpgrade('premium')}
             disabled={upgrading}
             className="w-full py-4 rounded-2xl bg-brand-neon text-brand-midnight text-[11px] font-black tracking-[0.3em] flex items-center justify-center space-x-2 active:scale-95 transition-all shadow-lg shadow-brand-neon/20"
           >
              {upgrading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
              <span>ACTIVATE PREMIUM (⧫ 500)</span>
           </button>
         ) : passData.pass_type === 'premium' ? (
           <button 
             onClick={() => handleUpgrade('elite')}
             disabled={upgrading}
             className="w-full py-4 rounded-2xl bg-brand-accent text-white text-[11px] font-black tracking-[0.3em] flex items-center justify-center space-x-2 active:scale-95 transition-all shadow-lg"
           >
              {upgrading ? <Loader2 size={16} className="animate-spin" /> : <Award size={16} />}
              <span>UPGRADE TO ELITE (⧫ 1500)</span>
           </button>
         ) : (
           <div className="w-full py-4 rounded-2xl bg-white/5 border border-white/10 text-brand-neon text-[11px] font-black tracking-[0.3em]">
             NEXUS OVERLORD STATUS
           </div>
         )}
      </div>
    </div>
  );
};
