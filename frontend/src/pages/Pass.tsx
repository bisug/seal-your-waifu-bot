import { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Crown, Gift, Loader2, Lock, Star, Ticket, TicketCheck, TicketPlus, Zap } from 'lucide-react';
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

const EGG_TIER_LABELS: Record<number, string> = {
  1: 'Gold',
  2: 'Void',
  3: 'Rare',
  4: 'Legendary',
  5: 'Celestial',
};

const TIER_ORDER = ['free', 'premium', 'elite'];
const TIER_ICON = {
  free: Ticket,
  premium: Star,
  elite: Crown,
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
  if (invert) return `${Math.round((1 - value) * 100)}% FASTER`;
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
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
    try {
      const res = await apiFetch(`/claim_level/${level}`, { method: 'POST' });
      if (res.status === 'success' || res.status === 'already_claimed') {
        addToast(
          res.status === 'already_claimed' ? 'Reward already collected' : `Collected rewards for Level ${level}`,
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
      addToast(res.message || 'Bank claimed', 'success');
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
          addToast(`${tier.toUpperCase()} PASS ACTIVATED`, 'success');
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
    <div className="px-4 py-12 max-w-2xl mx-auto">
      <ErrorState message={error} onAction={fetchPassData} />
    </div>
  );

  if (passLoading || !passData) return (
    <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-6">
        <div className="flex justify-between items-center">
            <Skeleton className="h-8 w-48 rounded-lg" />
            <Skeleton className="h-12 w-20 rounded-xl" />
        </div>
        <Skeleton className="h-4 w-full rounded-full" />
        <div className="grid grid-cols-3 gap-3">
            {[1,2,3].map(i => <Skeleton key={i} className="h-24 rounded-2xl" />)}
        </div>
        <Skeleton className="h-40 rounded-2xl" />
    </div>
  );

  const userLevel = Math.min(Number(passData.level || 0), Number(passData.max_level || 100));
  const maxLevel = Number(passData.max_level || 100);
  const claimedLevels = Array.isArray(passData.claimed_levels) ? passData.claimed_levels : [];
  const milestones = Array.isArray(passData.milestones) ? passData.milestones : [5, 10, 20, 25, 30, 40, 50, 60, 75, 80, 90, 100];
  const currentTier = passData.pass_type || 'free';
  const bank = bankSummary(passData.pass_bank);
  const nextTier = currentTier === 'free' ? 'premium' : currentTier === 'premium' ? 'elite' : null;
  const progressPercent = Math.min(100, Math.round((userLevel / Math.max(maxLevel, 1)) * 100));
  const nextBenefits = nextTier ? passData.benefits?.[nextTier] : null;

  return (
    <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8">
      <header className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                    <TicketCheck className="text-brand-accent" size={22} />
                </div>
                <h1 className="text-2xl font-black text-white tracking-tighter uppercase truncate max-w-[200px]">{passData.season_name || 'SEASON PASS'}</h1>
            </div>
            <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest px-1">OPERATIONAL SEASON 01</p>
          </div>
          <Card className="px-4 py-2 border-brand-accent/20 bg-brand-accent/5">
            <p className="text-[9px] font-black text-brand-accent uppercase tracking-widest text-center">LEVEL</p>
            <p className="text-2xl font-black text-white tabular-nums leading-none text-center">{userLevel}</p>
          </Card>
        </div>

        <div className="space-y-2">
            <ProgressBar current={userLevel} total={maxLevel} label="SEASON PROGRESS" color="bg-brand-accent" compact />
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
              className={cn(
                'p-4 flex flex-col items-center justify-center text-center space-y-2 transition-all',
                active ? 'border-brand-accent/50 bg-brand-accent/10 shadow-[0_0_20px_rgba(59,130,246,0.1)]' : unlocked ? 'border-emerald-500/20' : 'opacity-40'
              )}
            >
              <Icon size={20} className={active ? 'text-brand-accent' : unlocked ? 'text-emerald-500' : 'text-neutral-500'} />
              <p className="text-[10px] font-black text-white uppercase tracking-widest">{tier}</p>
              <Badge variant={unlocked ? "success" : "secondary"} size="xs" className="rounded-lg py-0">
                {unlocked ? 'ACTIVE' : `${passData.prices?.[tier] ?? 0}★`}
              </Badge>
            </Card>
          );
        })}
      </section>

      {nextTier && (
        <Card className="p-6 space-y-6 bg-gradient-to-br from-brand-deep to-brand-surface border-white/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-3 opacity-10">
              <Crown size={80} className="rotate-12" />
          </div>

          <div className="flex items-start justify-between gap-4 relative z-10">
            <div className="space-y-1">
              <Badge variant="primary" icon={Zap} className="rounded-lg px-2 py-0.5 text-[9px] font-black tracking-widest mb-1 uppercase">Recommended</Badge>
              <h2 className="text-xl font-black text-white uppercase tracking-tight">{nextTier} UPGRADE</h2>
              <p className="text-[11px] font-bold text-neutral-400 uppercase tracking-widest">
                {passData.tiers?.[nextTier]?.summary || 'UNLOCK PREMIUM REWARDS & BOOSTS'}
              </p>
            </div>
            <div className="flex flex-col items-end">
                <span className="text-xl font-black text-white tabular-nums">{passData.upgrade_prices?.[nextTier]}</span>
                <span className="text-[10px] font-black text-neutral-500 uppercase tracking-widest">STARS</span>
            </div>
          </div>

          {nextBenefits && (
            <div className="grid grid-cols-2 gap-3 relative z-10">
              <Card className="bg-brand-midnight p-3 space-y-1">
                <p className="text-[9px] font-black text-neutral-600 uppercase tracking-widest">Shard Harvest</p>
                <p className="text-xs font-black text-white uppercase">{percentBonus(nextBenefits.hunt_multiplier)}</p>
              </Card>
              <Card className="bg-brand-midnight p-3 space-y-1">
                <p className="text-[9px] font-black text-neutral-600 uppercase tracking-widest">Egg Discovery</p>
                <p className="text-xs font-black text-white uppercase">{percentBonus(nextBenefits.egg_drop_multiplier)}</p>
              </Card>
              <Card className="bg-brand-midnight p-3 space-y-1">
                <p className="text-[9px] font-black text-neutral-600 uppercase tracking-widest">Cycle Speed</p>
                <p className="text-xs font-black text-white uppercase">{percentBonus(nextBenefits.incubation_multiplier, true)}</p>
              </Card>
              <Card className="bg-brand-midnight p-3 space-y-1">
                <p className="text-[9px] font-black text-neutral-600 uppercase tracking-widest">Active Units</p>
                <p className="text-xs font-black text-white uppercase">{nextBenefits.incubation_slots} SLOTS</p>
              </Card>
            </div>
          )}

          <Button
            onClick={() => handleUpgrade(nextTier)}
            isLoading={upgrading === nextTier}
            className="w-full py-6 rounded-2xl uppercase tracking-[0.2em] text-[11px] font-black shadow-[0_10px_30px_rgba(59,130,246,0.3)] relative z-10"
          >
            ACTIVATE {nextTier.toUpperCase()} ACCESS
          </Button>
        </Card>
      )}

      {currentTier !== 'free' && bank.hasValue && (
        <Card className="p-4 border-amber-500/20 bg-amber-500/5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500">
                    <Gift size={24} />
                </div>
                <div>
                    <h2 className="text-sm font-black text-amber-500 uppercase tracking-widest">Accumulated Bank</h2>
                    <p className="text-[10px] font-bold text-amber-200/60 uppercase tracking-wider mt-0.5">
                        {formatNumber(bank.shards)} SHARDS {bank.eggs ? `• ${bank.eggs} EGGS` : ''}
                    </p>
                </div>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={handleClaimBank}
              isLoading={claimingBank}
              className="bg-amber-500 hover:bg-amber-600 text-white rounded-xl px-6 font-black uppercase text-[10px] tracking-widest"
            >
              Claim
            </Button>
        </Card>
      )}

      <section className="space-y-6">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em]">Deployment Milestones</h2>
          <Badge variant="secondary" size="xs" className="rounded-lg font-black tracking-widest">
            {claimedLevels.length} / {maxLevel} SECURED
          </Badge>
        </div>

        <div className="space-y-4">
            {milestones.map((lvl: number, index: number) => {
            const track = passData.tracks?.[lvl];
            if (!track) return null;
            const isReached = userLevel >= lvl;
            const isClaimed = claimedLevels.includes(lvl);

            return (
                <Card
                key={lvl}
                className={cn(
                    'p-5 space-y-5 transition-all duration-300',
                    isReached ? 'border-white/10' : 'opacity-50 grayscale'
                )}
                >
                <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <div className={cn(
                            'w-12 h-12 rounded-2xl flex flex-col items-center justify-center border transition-all duration-500',
                            isReached ? 'border-brand-accent/40 text-brand-accent bg-brand-accent/5' : 'border-white/5 text-neutral-600'
                        )}>
                            <span className="text-[8px] font-black uppercase opacity-60">LVL</span>
                            <span className="text-lg font-black tabular-nums leading-none">{lvl}</span>
                        </div>
                        <div>
                            <p className="text-sm font-black text-white uppercase tracking-tight">Milestone {lvl}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                                {isClaimed ? (
                                    <Badge variant="success" size="xs" className="rounded-lg px-1 py-0 uppercase">Secured</Badge>
                                ) : isReached ? (
                                    <Badge variant="primary" size="xs" className="rounded-lg px-1 py-0 uppercase">Available</Badge>
                                ) : (
                                    <Badge variant="secondary" size="xs" className="rounded-lg px-1 py-0 uppercase">Locked</Badge>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="shrink-0">
                        {isClaimed ? (
                        <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                            <CheckCircle2 size={22} strokeWidth={3} />
                        </div>
                        ) : isReached ? (
                        <Button
                            onClick={() => handleClaim(lvl)}
                            isLoading={claiming === lvl}
                            className="rounded-xl px-6 py-2.5 text-[10px] font-black uppercase tracking-widest"
                        >
                            Claim
                        </Button>
                        ) : (
                        <div className="w-10 h-10 rounded-xl bg-brand-surface border border-white/5 flex items-center justify-center text-neutral-700">
                            <Lock size={18} />
                        </div>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-2">
                    {TIER_ORDER.map((tier) => {
                    const unlocked = TIER_ORDER.indexOf(currentTier) >= TIER_ORDER.indexOf(tier);
                    const Icon = TIER_ICON[tier as keyof typeof TIER_ICON];
                    return (
                        <div key={tier} className={cn(
                            "flex items-center justify-between gap-4 px-4 py-3 rounded-xl border transition-all",
                            unlocked ? "bg-white/[0.02] border-white/5" : "bg-black/20 border-transparent opacity-40"
                        )}>
                        <div className="flex items-center gap-3 min-w-0">
                            <Icon size={14} className={unlocked ? 'text-brand-accent' : 'text-neutral-700'} />
                            <span className="text-[10px] font-black text-neutral-500 uppercase tracking-widest">{tier}</span>
                        </div>
                        <span className={cn('text-[11px] font-black text-right tracking-tight truncate ml-4', unlocked ? 'text-white' : 'text-neutral-700')}>
                            {formatReward(track, tier)}
                        </span>
                        </div>
                    );
                    })}
                </div>
                </Card>
            );
            })}
        </div>
      </section>
    </div>
  );
};
