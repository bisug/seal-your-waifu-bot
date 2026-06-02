import React from 'react';
import { motion } from 'framer-motion';
import { Award, Lock, Sparkles, Loader2, CheckCircle2 } from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useUser } from '../context/UserContext';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { cn } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';

const EGG_TIER_LABELS: Record<number, string> = {
  1: 'Gold',
  2: 'Void',
  3: 'Rare',
  4: 'Legendary',
  5: 'Celestial',
};

export const Pass = () => {
  const { refreshUser } = useUser();
  const { addToast } = useToast();
  const { data: passData, loading: passLoading, error, execute: fetchPassData } = useApi<any>('/pass_data');
  const { data: passShopData } = useApi<any>('/shop/battlepass');
  const [claiming, setClaiming] = React.useState<number | null>(null);
  const [upgrading, setUpgrading] = React.useState(false);
  const passPrices = passShopData?.prices || {};
  const getTierPrice = (tier: string) => passPrices[tier] ?? (tier === 'premium' ? 500 : 1500);

  const handleClaim = async (level: number) => {
    setClaiming(level);
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
    try {
      const res = await apiFetch(`/claim_level/${level}`, { method: 'POST' });
      if (res.status === 'success' || res.status === 'already_claimed') {
        addToast(
          res.status === 'already_claimed' ? 'Reward already claimed' : `Claimed: ${res.shards} Shards & ${res.eggs} Eggs`,
          'success'
        );
        await fetchPassData();
        await refreshUser();
      }
    } catch (err: any) {
      addToast(getErrorMessage(err), 'error');
    } finally {
      setClaiming(null);
    }
  };

  const handleUpgrade = async (tier: string) => {
    window.Telegram?.WebApp?.showConfirm(
      `Upgrade to ${tier.toUpperCase()} for ${getTierPrice(tier)} Zenith?`,
      async (confirmed: boolean) => {
        if (!confirmed) return;
        setUpgrading(true);
        try {
          const res = await apiFetch(`/shop/upgrade_pass/${tier}`, { method: 'POST' });
          if (res.status === 'success') {
            addToast(`${tier.charAt(0).toUpperCase() + tier.slice(1)} pass activated`, 'success');
            await fetchPassData();
            await refreshUser();
          }
        } catch (err: any) {
          addToast(getErrorMessage(err), 'error');
        } finally {
          setUpgrading(false);
        }
      }
    );
  };

  if (error && !passData) return (
    <div className="px-4 py-8 max-w-2xl mx-auto">
      <ErrorState message={error} onAction={fetchPassData} />
    </div>
  );

  if (passLoading || !passData) return (
    <div className="flex items-center justify-center min-h-[60vh]"><Loader2 className="animate-spin text-neutral-600 w-8 h-8" /></div>
  );

  const milestones = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
  const userLevel = passData.level || 0;
  const claimedLevels = passData.claimed_levels || [];

  return (
    <div className="pb-20 pt-4 px-4 max-w-2xl mx-auto">
      <header className="mb-8 flex justify-between items-end border-b border-white/5 pb-4">
        <div>
           <div className="flex items-center space-x-2 text-brand-accent mb-1.5">
             <Sparkles size={16} />
             <span className="text-xs font-semibold tracking-wider uppercase">Pass Status</span>
           </div>
           <h1 className="text-xl font-bold text-white tracking-tight">{passData.season_name || 'Season 1'} Pass</h1>
        </div>
        <div className="bg-brand-deep border border-white/5 px-4 py-2.5 rounded-xl text-center min-w-[80px] shadow-sm">
           <p className="text-xs font-medium text-neutral-500 mb-1">Level</p>
           <p className="text-2xl font-bold text-brand-accent tabular-nums leading-none">{userLevel}</p>
        </div>
      </header>

      <div className="space-y-4 relative ml-4 border-l-2 border-brand-deep pl-8">
        {milestones.map((lvl) => {
          const isReached = userLevel >= lvl;
          const isClaimed = Array.isArray(claimedLevels) ? claimedLevels.includes(lvl) : false;
          const track = passData.tracks?.[lvl];
          if (!track) return null;
          const reward = track[passData.pass_type] ?? track['free'];
          if (!reward) return null;
          const rewardLabel = reward.type === 'shards'
            ? `${reward.amount} Shards`
            : `${EGG_TIER_LABELS[Number(reward.tier)] ?? `Tier ${reward.tier}`} Egg`;

          return (
            <motion.div
              key={lvl}
              initial={{ opacity: 0, x: 10 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="flex items-center space-x-4 relative"
            >
              <div className={cn(
                "absolute -left-[49px] z-10 w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all text-xs font-bold",
                isReached ? 'border-brand-accent bg-brand-midnight text-brand-accent shadow-[0_0_15px_rgba(59,130,246,0.3)]' : 'border-brand-deep bg-brand-midnight text-neutral-600'
              )}>
                {lvl}
              </div>

              <div className={cn(
                "flex-1 p-4 rounded-xl border transition-all flex items-center justify-between shadow-sm",
                isReached ? 'bg-brand-deep border-white/5' : 'bg-brand-midnight border-white/5 opacity-60'
              )}>
                <div className="text-left">
                  <p className="text-sm font-bold text-white mb-1">{rewardLabel}</p>
                  <div className="flex items-center space-x-1.5">
                     <Award size={14} className={isReached ? "text-brand-accent" : "text-neutral-500"} />
                     <span className="text-xs text-neutral-400 font-medium capitalize">{reward.type}</span>
                  </div>
                </div>
                
                {isClaimed ? (
                  <CheckCircle2 size={20} className="text-emerald-500" strokeWidth={2.5} />
                ) : isReached ? (
                  <button 
                    onClick={() => handleClaim(lvl)}
                    disabled={claiming === lvl}
                    className="bg-white text-brand-midnight text-xs font-bold px-4 py-2 rounded-lg hover:bg-neutral-200 active:scale-95 transition-all shadow-sm min-w-[70px] flex justify-center"
                  >
                    {claiming === lvl ? <Loader2 size={16} className="animate-spin" /> : 'Claim'}
                  </button>
                ) : (
                  <div className="w-8 h-8 rounded-lg bg-black/20 flex items-center justify-center text-neutral-600">
                    <Lock size={16} />
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
      
      <div className="mt-12 p-6 rounded-xl border border-dashed border-white/10 bg-brand-deep text-center shadow-sm">
         <p className="text-xs font-semibold text-neutral-500 mb-4 uppercase tracking-wider">
           {passData.pass_type === 'elite' ? 'Elite pass active' : passData.pass_type === 'premium' ? 'Premium pass active' : 'Upgrade available'}
         </p>
         
         {passData.pass_type === 'free' ? (
           <button 
             onClick={() => handleUpgrade('premium')}
             disabled={upgrading}
             className="w-full py-3.5 rounded-lg bg-brand-accent text-white text-sm font-bold flex items-center justify-center space-x-2 hover:bg-brand-accent-secondary active:scale-[0.98] transition-all shadow-sm"
           >
              {upgrading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
              <span>Activate Premium ({getTierPrice('premium')} Zenith)</span>
           </button>
         ) : passData.pass_type === 'premium' ? (
           <button 
             onClick={() => handleUpgrade('elite')}
             disabled={upgrading}
             className="w-full py-3.5 rounded-lg bg-white text-brand-midnight text-sm font-bold flex items-center justify-center space-x-2 hover:bg-neutral-200 active:scale-[0.98] transition-all shadow-sm"
           >
              {upgrading ? <Loader2 size={18} className="animate-spin" /> : <Award size={18} />}
              <span>Upgrade to Elite ({getTierPrice('elite')} Zenith)</span>
           </button>
         ) : (
           <div className="w-full py-3.5 rounded-lg bg-brand-accent/10 border border-brand-accent/20 text-brand-accent text-sm font-bold tracking-wide">
             Elite pass active
           </div>
         )}
      </div>
    </div>
  );
};
