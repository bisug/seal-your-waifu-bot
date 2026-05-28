import React from 'react';
import { motion } from 'framer-motion';
import { Award, Lock, Sparkles, Loader2, CheckCircle2 } from 'lucide-react';
import { apiFetch } from '../api/client';
import { useUser } from '../context/UserContext';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { cn } from '../utils';


export const Pass = () => {
  const { refreshUser } = useUser();
  const { addToast } = useToast();
  const { data: passData, loading: passLoading, execute: fetchPassData } = useApi<any>('/pass_data');
  const [claiming, setClaiming] = React.useState<number | null>(null);
  const [upgrading, setUpgrading] = React.useState(false);

  const handleClaim = async (level: number) => {
    setClaiming(level);
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
    try {
      const res = await apiFetch(`/claim_level/${level}`, { method: 'POST' });
      if (res.status === 'success') {
        addToast(`Claimed: ${res.shards} Shards & ${res.eggs} Eggs`, 'success');
        await fetchPassData();
        await refreshUser();
      }
    } catch (err: any) {
      addToast(err.message || 'Claim failed', 'error');
    } finally {
      setClaiming(null);
    }
  };

  const handleUpgrade = async (tier: string) => {
    window.Telegram?.WebApp?.showConfirm(
      `Upgrade to ${tier.toUpperCase()} for ${tier === 'premium' ? '500' : '1500'} Zenith?`,
      async (confirmed: boolean) => {
        if (!confirmed) return;
        setUpgrading(true);
        try {
          const res = await apiFetch(`/shop/upgrade_pass/${tier}`, { method: 'POST' });
          if (res.status === 'success') {
            addToast(`${tier.charAt(0).toUpperCase() + tier.slice(1)} Protocol Activated`, 'success');
            await fetchPassData();
            await refreshUser();
          }
        } catch (err: any) {
          addToast(err.message || 'Upgrade failed', 'error');
        } finally {
          setUpgrading(false);
        }
      }
    );
  };

  if (passLoading || !passData) return (
    <div className="flex items-center justify-center min-h-[60vh]"><Loader2 className="animate-spin text-zinc-800" /></div>
  );

  const milestones = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
  const userLevel = passData.level || 0;
  const claimedLevels = passData.claimed_levels || [];

  return (
    <div className="pb-8 pt-6 px-4">
      <header className="mb-10 flex justify-between items-end">
        <div>
           <div className="flex items-center space-x-2 text-brand-accent mb-1">
             <Sparkles size={14} />
             <span className="text-[10px] font-bold uppercase tracking-wider">Protocol Status</span>
           </div>
           <h1 className="text-xl font-bold text-zinc-100">{passData.season_name || 'Season 1'} Pass</h1>
        </div>
        <div className="bg-zinc-900 border border-white/5 px-3 py-2 rounded-lg text-right min-w-[80px]">
           <p className="text-[10px] font-medium text-zinc-500 mb-0.5 uppercase tracking-tight">Level</p>
           <p className="text-xl font-bold text-brand-accent tabular-nums leading-none">{userLevel}</p>
        </div>
      </header>

      <div className="space-y-4 relative ml-4 border-l border-zinc-900 pl-8">
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
              initial={{ opacity: 0, x: 10 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="flex items-center space-x-3 relative"
            >
              <div className={cn(
                "absolute -left-[45px] z-10 w-8 h-8 rounded-full flex items-center justify-center border transition-all text-[10px] font-bold",
                isReached ? 'border-brand-accent bg-zinc-950 text-brand-accent' : 'border-zinc-900 bg-zinc-950 text-zinc-600'
              )}>
                {lvl}
              </div>

              <div className={cn(
                "flex-1 p-4 rounded-lg border transition-all flex items-center justify-between",
                isReached ? 'bg-zinc-900/80 border-white/5' : 'bg-zinc-900/40 border-white/5 opacity-50'
              )}>
                <div className="text-left">
                  <p className="text-sm font-bold text-zinc-100">{rewardLabel}</p>
                  <div className="flex items-center space-x-1.5 mt-1">
                     <Award size={12} className={isReached ? "text-brand-accent" : "text-zinc-600"} />
                     <span className="text-[10px] text-zinc-500 font-medium uppercase tracking-tight">{reward.type}</span>
                  </div>
                </div>
                
                {isClaimed ? (
                  <CheckCircle2 size={18} className="text-emerald-500" />
                ) : isReached ? (
                  <button 
                    onClick={() => handleClaim(lvl)}
                    disabled={claiming === lvl}
                    className="bg-zinc-100 text-zinc-950 text-xs font-bold px-4 py-1.5 rounded hover:bg-white active:scale-95 transition-all"
                  >
                    {claiming === lvl ? <Loader2 size={12} className="animate-spin" /> : 'Claim'}
                  </button>
                ) : (
                  <Lock size={16} className="text-zinc-800" />
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
      
      <div className="mt-12 p-6 rounded-lg border border-dashed border-zinc-800 bg-zinc-900/20 text-center">
         <p className="text-[10px] font-bold text-zinc-600 mb-4 uppercase tracking-widest">
           {passData.pass_type === 'elite' ? 'Elite Protocol Active' : passData.pass_type === 'premium' ? 'Premium Protocol Active' : 'Protocol Upgrade Available'}
         </p>
         
         {passData.pass_type === 'free' ? (
           <button 
             onClick={() => handleUpgrade('premium')}
             disabled={upgrading}
             className="w-full py-3.5 rounded-md bg-brand-accent text-white text-xs font-bold flex items-center justify-center space-x-2 active:scale-[0.98] transition-all shadow-sm"
           >
              {upgrading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
              <span>Activate Premium (500 Zenith)</span>
           </button>
         ) : passData.pass_type === 'premium' ? (
           <button 
             onClick={() => handleUpgrade('elite')}
             disabled={upgrading}
             className="w-full py-3.5 rounded-md bg-zinc-100 text-zinc-950 text-xs font-bold flex items-center justify-center space-x-2 active:scale-[0.98] transition-all shadow-sm"
           >
              {upgrading ? <Loader2 size={16} className="animate-spin" /> : <Award size={16} />}
              <span>Upgrade to Elite (1500 Zenith)</span>
           </button>
         ) : (
           <div className="w-full py-3.5 rounded-md border border-brand-accent/20 text-brand-accent text-xs font-bold uppercase tracking-wider">
             Elite status confirmed
           </div>
         )}
      </div>
    </div>
  );
};
