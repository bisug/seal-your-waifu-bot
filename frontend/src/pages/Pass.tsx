import { useCallback, useState } from 'react';
import { CheckCircle2, Crown, Gift, Lock, Star, Ticket, TicketCheck, Zap, Heart, ArrowRight, ShieldCheck, Trophy, Target } from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useUser } from '../context/UserContext';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { cn, formatNumber } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';
import { Skeleton } from '../components/ui/Skeleton';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { ProgressBar } from '../components/ui/ProgressBar';
import { motion, AnimatePresence } from 'framer-motion';

const EGG_TIER_LABELS: Record<number, string> = {
  1: 'Common',
  2: 'Uncommon',
  3: 'Rare',
  4: 'Epic',
  5: 'Legendary',
};

const TIER_ORDER = ['free', 'premium', 'elite'];
const TIER_ICON = {
  free: Ticket,
  premium: Star,
  elite: Heart,
};

function formatReward(track: any, tier: string) {
  const reward = track?.[tier] ?? track?.free;
  if (!reward) return 'No reward';
  const extra = Number(track?.[`${tier}_extra_amount`] || 0);
  const base = reward.type === 'shards'
    ? `${formatNumber(reward.amount)} SHARDS`
    : `${(EGG_TIER_LABELS[Number(reward.tier)] ?? `Tier ${reward.tier}`).toUpperCase()} EGG`;
  return extra > 0 ? `${base} + ${formatNumber(extra)} SHARDS` : base;
}

function bankSummary(bank: Record<string, number> = {}) {
  const shards = Number(bank.shards || 0);
  const eggs = Object.entries(bank)
    .filter(([key]) => key.startsWith('eggs_t'))
    .reduce((sum, [, value]) => sum + Number(value || 0), 0);
  return { shards, eggs, hasValue: shards > 0 || eggs > 0 };
}

function percentBonus(multiplier: number | undefined, invert = false) {
  const value = Number(multiplier || 1);
  if (invert) return `${Math.round((1 - value) * 100)}% SPEED`;
  return `+${Math.round((value - 1) * 100)}%`;
}

export const Pass = () => {
  const { refreshUser } = useUser();
  const { addToast } = useToast();
  const { data: passData, loading: passLoading, error, execute: fetchPassData } = useApi<any>('/pass_data');
  const [claiming, setClaiming] = useState<number | null>(null);
  const [claimingBank, setClaimingBank] = useState(false);
  const [upgrading, setUpgrading] = useState<string | null>(null);

  const refreshAll = useCallback(async () => {
    await fetchPassData();
    await refreshUser();
  }, [fetchPassData, refreshUser]);

  const handleClaim = async (level: number) => {
    setClaiming(level);
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
    try {
      const res = await apiFetch(`/claim_level/${level}`, { method: 'POST' });
      if (res.status === 'success' || res.status === 'already_claimed') {
        addToast(
          res.status === 'already_claimed' ? 'Security check: Reward already claimed' : `Success: Level ${level} rewards secured`,
          'success'
        );
        await refreshAll();
      }
    } catch (err: any) {
      addToast(getErrorMessage(err), 'error');
    } finally {
      setClaiming(null);
    }
  };

  const handleClaimBank = async () => {
    setClaimingBank(true);
    try {
      const res = await apiFetch('/claim_bank', { method: 'POST' });
      addToast(res.message || 'Vault emptied. Rewards secured.', 'success');
      await refreshAll();
    } catch (err: any) {
      addToast(getErrorMessage(err), 'error');
    } finally {
      setClaimingBank(false);
    }
  };

  const handleUpgrade = async (tier: string) => {
    const tg = window.Telegram?.WebApp;
    if (!tg?.openInvoice) {
      addToast('Open this inside Telegram to pay with Stars.', 'error');
      return;
    }

    setUpgrading(tier);
    try {
      const invoice = await apiFetch(`/shop/pass_invoice/${tier}`, { method: 'POST' });
      tg.openInvoice(invoice.invoice_url, async (status: string) => {
        if (status === 'paid') {
          addToast(`${tier.toUpperCase()} CLEARANCE ACTIVATED`, 'success');
          window.setTimeout(refreshAll, 1200);
        } else if (status === 'cancelled') {
          addToast('Payment cancelled', 'error');
        } else if (status === 'failed') {
          addToast('Payment failed', 'error');
        }
        setUpgrading(null);
      });
    } catch (err: any) {
      addToast(getErrorMessage(err), 'error');
      setUpgrading(null);
    }
  };

  if (error && !passData) return (
    <div className="px-5 py-20 max-w-2xl mx-auto">
      <ErrorState message={error} onAction={fetchPassData} />
    </div>
  );

  if (passLoading || !passData) return (
    <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-8">
        <div className="flex justify-between items-center">
            <Skeleton className="h-10 w-48 rounded-lg" />
            <Skeleton className="h-12 w-20 rounded-2xl" />
        </div>
        <Skeleton className="h-3 w-full rounded-full" />
        <div className="grid grid-cols-3 gap-4">
            {[1,2,3].map(i => <Skeleton key={i} className="h-24 rounded-2xl" />)}
        </div>
        <Skeleton className="h-64 rounded-[32px]" />
    </div>
  );

  const userLevel = Math.min(Number(passData.level || 0), Number(passData.max_level || 100));
  const maxLevel = Number(passData.max_level || 100);
  const claimedLevels = Array.isArray(passData.claimed_levels) ? passData.claimed_levels : [];
  const milestones = Array.isArray(passData.milestones) ? passData.milestones : [5, 10, 20, 25, 30, 40, 50, 60, 75, 80, 90, 100];
  const currentTier = passData.pass_type || 'free';
  const bank = bankSummary(passData.pass_bank);
  const nextTier = currentTier === 'free' ? 'premium' : currentTier === 'premium' ? 'elite' : null;
  const nextBenefits = nextTier ? passData.benefits?.[nextTier] : null;

  return (
    <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-10">
      <header className="space-y-6">
        <div className="flex items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                    <TicketCheck size={26} className="text-brand-accent" />
                </div>
                <div className="flex flex-col gap-1">
                   <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none truncate max-w-[180px]">
                      {passData.season_name || 'WAIFU PASS'}
                   </h1>
                   <div className="flex items-center gap-2">
                      <Target size={11} className="text-neutral-600" />
                      <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                        STRATEGIC PROGRESSION LOG
                      </p>
                   </div>
                </div>
            </div>
          </div>
          <Card variant="accent" className="px-5 py-3 border-brand-accent/30 bg-brand-accent/10 shadow-lg">
            <p className="text-[8px] font-black text-brand-accent uppercase tracking-[0.3em] text-center mb-1">LVL</p>
            <p className="text-2xl font-black text-white tabular-nums leading-none text-center font-mono">{userLevel}</p>
          </Card>
        </div>

        <div className="px-1">
            <ProgressBar
               current={userLevel}
               total={maxLevel}
               label="GLOBAL CLEARANCE PROGRESS"
               variant="default"
            />
        </div>
      </header>

      <section className="grid grid-cols-3 gap-3">
        {TIER_ORDER.map((tier) => {
          const Icon = TIER_ICON[tier as keyof typeof TIER_ICON];
          const active = currentTier === tier;
          const unlocked = TIER_ORDER.indexOf(currentTier) >= TIER_ORDER.indexOf(tier);
          return (
            <Card
              key={tier}
              variant="tactical"
              className={cn(
                'p-4 flex flex-col items-center justify-center text-center space-y-2 transition-all duration-500',
                active ? 'border-brand-accent/40 bg-brand-accent/[0.04] shadow-[0_0_20px_rgba(59,130,246,0.05)]' : unlocked ? 'border-success/20 bg-success/[0.02]' : 'opacity-30 grayscale border-white/[0.03]'
              )}
            >
              <div className={cn(
                  "p-2 rounded-xl transition-all duration-500",
                  active ? "bg-brand-accent/20" : unlocked ? "bg-success/10" : "bg-white/[0.02]"
              )}>
                 <Icon size={18} className={active ? 'text-brand-accent' : unlocked ? 'text-success' : 'text-neutral-700'} fill={(tier === 'elite' || tier === 'premium') && unlocked ? 'currentColor' : 'none'} />
              </div>
              <p className="text-[9px] font-black text-white uppercase tracking-widest leading-none">{tier}</p>
              <Badge variant={unlocked ? "success" : "tactical"} size="xs" className="border-none py-1 px-1.5 opacity-80 text-[8px] leading-none">
                {unlocked ? 'SECURED' : `${passData.prices?.[tier] ?? 0} STARS`}
              </Badge>
            </Card>
          );
        })}
      </section>

      {nextTier && (
        <Card variant="tactical" className="p-8 space-y-8 bg-gradient-to-br from-[#0c0c0e] to-brand-midnight border-white/[0.06] rounded-[32px] relative overflow-hidden group shadow-2xl">
          <div className="absolute top-0 right-0 p-6 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity duration-700">
              <ShieldCheck size={120} className="rotate-12" />
          </div>

          <div className="flex items-start justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <Badge variant="primary" icon={Zap} size="xs" className="rounded-md px-2 py-1 text-[9px] font-black tracking-widest mb-2 uppercase border-brand-accent/30 shadow-[0_0_10px_rgba(59,130,246,0.2)] animate-pulse">RECOMMENDED</Badge>
              <h2 className="text-2xl font-black text-white uppercase tracking-tighter drop-shadow-md">{nextTier.toUpperCase()} CLEARANCE</h2>
              <p className="text-[11px] font-bold text-neutral-500 uppercase tracking-[0.1em] leading-relaxed max-w-[240px]">
                {passData.tiers?.[nextTier]?.summary || 'UNRESTRICTED ACCESS TO PREMIUM ASSETS & BUFFS.'}
              </p>
            </div>
            <div className="flex flex-col items-end pt-2">
                <span className="text-2xl font-black text-white tabular-nums font-mono drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]">
                   {passData.upgrade_prices?.[nextTier]}
                </span>
                <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.2em] mt-1">STARS</span>
            </div>
          </div>

          {nextBenefits && (
            <div className="grid grid-cols-2 gap-3 relative z-10">
              {[
                  { label: 'CREDIT YIELD', value: percentBonus(nextBenefits.hunt_multiplier), icon: Zap, color: 'text-warning' },
                  { label: 'DROP LUCK', value: percentBonus(nextBenefits.egg_drop_multiplier), icon: Star, color: 'text-brand-accent' },
                  { label: 'SYNC SPEED', value: percentBonus(nextBenefits.incubation_multiplier, true), icon: Target, color: 'text-success' },
                  { label: 'ACTIVE SLOTS', value: `${nextBenefits.incubation_slots} UNITS`, icon: ShieldCheck, color: 'text-epic' },
              ].map((benefit, i) => (
                <div key={i} className="bg-black/40 p-4 rounded-2xl space-y-2 border border-white/[0.04] hover:border-white/[0.1] transition-colors group/benefit">
                   <div className="flex items-center gap-2">
                      <benefit.icon size={12} className={cn("transition-transform group-hover/benefit:scale-110", benefit.color)} />
                      <p className="text-[8px] font-black text-neutral-600 uppercase tracking-widest">{benefit.label}</p>
                   </div>
                   <p className="text-xs font-black text-white uppercase font-mono leading-none">{benefit.value}</p>
                </div>
              ))}
            </div>
          )}

          <Button
            onClick={() => handleUpgrade(nextTier)}
            isLoading={upgrading === nextTier}
            variant="tactical"
            className="w-full h-14 rounded-2xl uppercase tracking-[0.3em] text-[11px] font-black relative z-10 shadow-xl active:scale-[0.98]"
          >
            ACTIVATE CLEARANCE
          </Button>
        </Card>
      )}

      {currentTier !== 'free' && bank.hasValue && (
        <Card variant="accent" className="p-5 border-warning/30 bg-warning/[0.03] flex items-center justify-between gap-6 rounded-[24px] shadow-lg animate-in">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-warning/10 border border-warning/20 flex items-center justify-center text-warning shadow-[0_0_15px_rgba(245,158,11,0.15)]">
                    <Gift size={24} />
                </div>
                <div>
                    <h2 className="text-sm font-black text-warning uppercase tracking-[0.15em] leading-none mb-1.5">REWARD VAULT</h2>
                    <p className="text-[10px] font-bold text-warning/50 uppercase tracking-widest font-mono leading-none">
                        {formatNumber(bank.shards)} SHARDS {bank.eggs ? `+ ${bank.eggs} EGGS` : ''}
                    </p>
                </div>
            </div>
            <Button
              variant="tactical"
              size="sm"
              onClick={handleClaimBank}
              isLoading={claimingBank}
              className="bg-warning text-black hover:bg-white border-none px-6 font-black uppercase text-[10px] tracking-widest h-10 rounded-xl"
            >
              CLAIM
            </Button>
        </Card>
      )}

      <section className="space-y-6">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2.5">
             <h2 className="text-[11px] font-black text-neutral-600 uppercase tracking-[0.3em]">PIPELINE LOG</h2>
             <div className="h-1 w-1 rounded-full bg-neutral-800" />
          </div>
          <Badge variant="tactical" size="xs" className="opacity-40 font-mono tracking-tighter uppercase">
            {claimedLevels.length}<span className="mx-1 opacity-30">/</span>{maxLevel} SECURED
          </Badge>
        </div>

        <div className="space-y-4">
            <AnimatePresence mode="popLayout">
            {milestones.map((lvl: number) => {
            const track = passData.tracks?.[lvl];
            if (!track) return null;
            const isReached = userLevel >= lvl;
            const isClaimed = claimedLevels.includes(lvl);

            return (
                <motion.div layout key={lvl} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                    <Card
                        variant="tactical"
                        className={cn(
                            'p-6 space-y-6 transition-all duration-500 overflow-hidden relative',
                            isReached ? 'border-white/[0.08] bg-white/[0.01]' : 'opacity-30 grayscale border-transparent'
                        )}
                    >
                    {isReached && !isClaimed && (
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-brand-accent/40 to-transparent animate-shimmer" />
                    )}

                    <div className="flex items-center justify-between gap-6 relative z-10">
                        <div className="flex items-center gap-4">
                            <div className={cn(
                                'w-12 h-12 rounded-2xl flex flex-col items-center justify-center border transition-all duration-700 shadow-sm',
                                isReached ? 'border-brand-accent/40 text-brand-accent bg-brand-accent/5' : 'border-white/[0.05] text-neutral-800 bg-black/20'
                            )}>
                                <span className="text-[8px] font-black uppercase opacity-40 leading-none mb-1">LVL</span>
                                <span className="text-xl font-black tabular-nums leading-none font-mono">{lvl}</span>
                            </div>
                            <div>
                                <p className="text-sm font-black text-white uppercase tracking-tight mb-1">Milestone {lvl}</p>
                                <div className="flex items-center gap-2">
                                    {isClaimed ? (
                                        <Badge variant="success" size="xs" className="border-none py-0.5 px-2 uppercase font-black tracking-widest bg-success/10 text-success rounded-md">SECURED</Badge>
                                    ) : isReached ? (
                                        <Badge variant="primary" size="xs" className="border-none py-0.5 px-2 uppercase font-black tracking-widest bg-brand-accent/10 text-brand-accent rounded-md">AVAILABLE</Badge>
                                    ) : (
                                        <Badge variant="tactical" size="xs" className="border-none py-0.5 px-2 uppercase font-black tracking-widest opacity-40 rounded-md">ENCRYPTED</Badge>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="shrink-0">
                            {isClaimed ? (
                            <div className="w-10 h-10 rounded-2xl bg-success/10 border border-success/20 flex items-center justify-center text-success shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                                <CheckCircle2 size={20} strokeWidth={3} />
                            </div>
                            ) : isReached ? (
                            <Button
                                onClick={() => handleClaim(lvl)}
                                isLoading={claiming === lvl}
                                variant="tactical"
                                className="h-10 px-6 text-[10px] font-black uppercase tracking-[0.2em] rounded-xl shadow-lg active:scale-95"
                            >
                                CLAIM
                            </Button>
                            ) : (
                            <div className="w-10 h-10 rounded-2xl bg-black/40 border border-white/[0.03] flex items-center justify-center text-neutral-800">
                                <Lock size={18} />
                            </div>
                            )}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 gap-2 relative z-10">
                        {TIER_ORDER.map((tier) => {
                        const unlocked = TIER_ORDER.indexOf(currentTier) >= TIER_ORDER.indexOf(tier);
                        const Icon = TIER_ICON[tier as keyof typeof TIER_ICON];
                        return (
                            <div key={tier} className={cn(
                                "flex items-center justify-between gap-4 px-4 py-3 rounded-xl border transition-all duration-300",
                                unlocked ? "bg-white/[0.02] border-white/[0.05] hover:bg-white/[0.04]" : "bg-black/60 border-transparent opacity-30"
                            )}>
                            <div className="flex items-center gap-3 min-w-0">
                                <Icon size={14} className={unlocked ? (tier === 'elite' ? 'text-epic' : tier === 'premium' ? 'text-brand-accent' : 'text-neutral-400') : 'text-neutral-800'} fill={(tier === 'elite' || tier === 'premium') && unlocked ? 'currentColor' : 'none'} />
                                <span className="text-[9px] font-black text-neutral-500 uppercase tracking-widest leading-none">{tier}</span>
                            </div>
                            <span className={cn('text-[11px] font-black text-right tracking-tight truncate ml-4 font-mono uppercase leading-none', unlocked ? 'text-white/90' : 'text-neutral-800')}>
                                {formatReward(track, tier)}
                            </span>
                            </div>
                        );
                        })}
                    </div>
                    </Card>
                </motion.div>
            );
            })}
            </AnimatePresence>
        </div>
      </section>
    </div>
  );
};
