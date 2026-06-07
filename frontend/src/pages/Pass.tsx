import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Crown, Gift, Loader2, Lock, Star, Ticket, TicketCheck, TicketPlus } from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useUser } from '../context/UserContext';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { cn, formatNumber } from '../utils';
import { ErrorState } from '../components/ui/ErrorState';

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
    ? `${formatNumber(reward.amount)} Shards`
    : `${EGG_TIER_LABELS[Number(reward.tier)] ?? `Tier ${reward.tier}`} Egg`;
  return extra > 0 ? `${base} + ${formatNumber(extra)} Shards` : base;
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
  if (invert) return `${Math.round((1 - value) * 100)}% faster`;
  return `+${Math.round((value - 1) * 100)}%`;
}

export const Pass = () => {
  const { refreshUser } = useUser();
  const { addToast } = useToast();
  const { data: passData, loading: passLoading, error, execute: fetchPassData } = useApi<any>('/pass_data');
  const [claiming, setClaiming] = React.useState<number | null>(null);
  const [claimingBank, setClaimingBank] = React.useState(false);
  const [upgrading, setUpgrading] = React.useState<string | null>(null);

  const refreshAll = React.useCallback(async () => {
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
          res.status === 'already_claimed' ? 'Reward already collected' : `Collected ${formatNumber(res.shards)} Shards and ${res.eggs} Eggs`,
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
          addToast(`${tier.charAt(0).toUpperCase() + tier.slice(1)} pass payment received`, 'success');
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
    <div className="px-4 py-8 max-w-2xl mx-auto">
      <ErrorState message={error} onAction={fetchPassData} />
    </div>
  );

  if (passLoading || !passData) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Loader2 className="animate-spin text-neutral-600 w-8 h-8" />
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
    <div className="pb-20 pt-4 px-4 max-w-2xl mx-auto space-y-6">
      <header className="border-b border-white/5 pb-5">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-brand-accent mb-1.5">
              <TicketCheck size={16} />
              <span className="text-xs font-semibold uppercase">Battle Pass</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight truncate">{passData.season_name || 'Season Pass'}</h1>
          </div>
          <div className="bg-brand-deep border border-white/5 px-4 py-2.5 rounded-lg text-center min-w-[84px]">
            <p className="text-xs font-medium text-neutral-500 mb-1">Level</p>
            <p className="text-2xl font-bold text-brand-accent tabular-nums leading-none">{userLevel}</p>
          </div>
        </div>

        <div className="mt-5">
          <div className="flex items-center justify-between text-xs font-semibold text-neutral-400 mb-2">
            <span className="capitalize">{currentTier} tier</span>
            <span>{progressPercent}%</span>
          </div>
          <div className="h-2.5 bg-brand-deep rounded-full border border-white/5 overflow-hidden">
            <div className="h-full bg-brand-accent transition-all duration-500" style={{ width: `${progressPercent}%` }} />
          </div>
        </div>
      </header>

      <section className="grid grid-cols-3 gap-2">
        {TIER_ORDER.map((tier) => {
          const Icon = TIER_ICON[tier as keyof typeof TIER_ICON];
          const active = currentTier === tier;
          const unlocked = TIER_ORDER.indexOf(currentTier) >= TIER_ORDER.indexOf(tier);
          return (
            <div
              key={tier}
              className={cn(
                'rounded-lg border p-3 min-h-[92px] bg-brand-deep',
                active ? 'border-brand-accent/60' : unlocked ? 'border-emerald-500/20' : 'border-white/5'
              )}
            >
              <Icon size={18} className={active ? 'text-brand-accent' : unlocked ? 'text-emerald-500' : 'text-neutral-600'} />
              <p className="mt-2 text-sm font-bold text-white capitalize">{tier}</p>
              <p className="mt-0.5 text-xs font-medium text-neutral-500">
                {unlocked ? 'Active' : `${passData.prices?.[tier] ?? 0} Stars`}
              </p>
            </div>
          );
        })}
      </section>

      {nextTier && (
        <section className="rounded-lg border border-white/5 bg-brand-deep p-4">
          <div className="flex items-start justify-between gap-3 mb-4">
            <div>
              <h2 className="text-sm font-bold text-white capitalize">{nextTier} upgrade</h2>
              <p className="text-xs font-medium text-neutral-400 mt-1">
                {passData.tiers?.[nextTier]?.summary || 'Unlock paid seasonal rewards'}
              </p>
            </div>
            <span className="text-sm font-bold text-brand-accent whitespace-nowrap">{passData.upgrade_prices?.[nextTier]} Stars</span>
          </div>
          {nextBenefits && (
            <div className="grid grid-cols-2 gap-2 mb-4">
              <div className="rounded-lg bg-brand-midnight border border-white/5 px-3 py-2">
                <p className="text-[10px] font-semibold text-neutral-500">Hunt</p>
                <p className="text-xs font-bold text-white">{percentBonus(nextBenefits.hunt_multiplier)} Shards</p>
              </div>
              <div className="rounded-lg bg-brand-midnight border border-white/5 px-3 py-2">
                <p className="text-[10px] font-semibold text-neutral-500">Eggs</p>
                <p className="text-xs font-bold text-white">{percentBonus(nextBenefits.egg_drop_multiplier)} Drops</p>
              </div>
              <div className="rounded-lg bg-brand-midnight border border-white/5 px-3 py-2">
                <p className="text-[10px] font-semibold text-neutral-500">Incubation</p>
                <p className="text-xs font-bold text-white">{percentBonus(nextBenefits.incubation_multiplier, true)}</p>
              </div>
              <div className="rounded-lg bg-brand-midnight border border-white/5 px-3 py-2">
                <p className="text-[10px] font-semibold text-neutral-500">Slots</p>
                <p className="text-xs font-bold text-white">{nextBenefits.incubation_slots} Incubators</p>
              </div>
            </div>
          )}
          <button
            onClick={() => handleUpgrade(nextTier)}
            disabled={upgrading !== null}
            className="w-full h-12 rounded-lg bg-brand-accent text-white text-sm font-bold flex items-center justify-center gap-2 active:scale-[0.98] transition-all"
          >
            {upgrading === nextTier ? <Loader2 size={18} className="animate-spin" /> : <TicketPlus size={18} />}
            <span>{upgrading === nextTier ? 'Opening invoice' : `Buy ${nextTier} pass`}</span>
          </button>
        </section>
      )}

      {currentTier !== 'free' && bank.hasValue && (
        <section className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-amber-200">
                <Gift size={18} />
                <h2 className="text-sm font-bold">Paid reward bank</h2>
              </div>
              <p className="text-xs font-medium text-amber-100/80 mt-1">
                {formatNumber(bank.shards)} Shards{bank.eggs ? ` + ${bank.eggs} Eggs` : ''}
              </p>
            </div>
            <button
              onClick={handleClaimBank}
              disabled={claimingBank}
              className="h-10 px-4 rounded-lg bg-white text-brand-midnight text-xs font-bold flex items-center justify-center min-w-[82px]"
            >
              {claimingBank ? <Loader2 size={16} className="animate-spin" /> : 'Claim'}
            </button>
          </div>
        </section>
      )}

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-neutral-300">Season rewards</h2>
          <span className="text-xs font-semibold text-neutral-500">{claimedLevels.length}/{maxLevel} collected</span>
        </div>

        {milestones.map((lvl: number, index: number) => {
          const track = passData.tracks?.[lvl];
          if (!track) return null;
          const isReached = userLevel >= lvl;
          const isClaimed = claimedLevels.includes(lvl);

          return (
            <motion.div
              key={lvl}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(index * 0.02, 0.16) }}
              viewport={{ once: true }}
              className={cn(
                'rounded-lg border bg-brand-deep p-4',
                isReached ? 'border-white/10' : 'border-white/5 opacity-70'
              )}
            >
              <div className="flex items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    'w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold border',
                    isReached ? 'border-brand-accent/40 text-brand-accent bg-brand-midnight' : 'border-white/5 text-neutral-600 bg-brand-midnight'
                  )}>
                    {lvl}
                  </span>
                  <div>
                    <p className="text-sm font-bold text-white">Level {lvl}</p>
                    <p className="text-xs font-medium text-neutral-500">{isClaimed ? 'Collected' : isReached ? 'Unlocked' : 'Locked'}</p>
                  </div>
                </div>

                {isClaimed ? (
                  <CheckCircle2 size={21} className="text-emerald-500" strokeWidth={2.5} />
                ) : isReached ? (
                  <button
                    onClick={() => handleClaim(lvl)}
                    disabled={claiming === lvl}
                    className="h-10 px-4 rounded-lg bg-white text-brand-midnight text-xs font-bold flex items-center justify-center min-w-[76px]"
                  >
                    {claiming === lvl ? <Loader2 size={16} className="animate-spin" /> : 'Claim'}
                  </button>
                ) : (
                  <div className="w-9 h-9 rounded-lg bg-brand-midnight border border-white/5 flex items-center justify-center text-neutral-600">
                    <Lock size={16} />
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 gap-2">
                {TIER_ORDER.map((tier) => {
                  const unlocked = TIER_ORDER.indexOf(currentTier) >= TIER_ORDER.indexOf(tier);
                  const Icon = TIER_ICON[tier as keyof typeof TIER_ICON];
                  return (
                    <div key={tier} className="flex items-center justify-between gap-3 rounded-lg bg-brand-midnight border border-white/5 px-3 py-2 min-h-[44px]">
                      <div className="flex items-center gap-2 min-w-0">
                        <Icon size={14} className={unlocked ? 'text-brand-accent' : 'text-neutral-600'} />
                        <span className="text-xs font-semibold text-neutral-400 capitalize w-16">{tier}</span>
                      </div>
                      <span className={cn('text-xs font-bold text-right', unlocked ? 'text-white' : 'text-neutral-600')}>
                        {formatReward(track, tier)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          );
        })}
      </section>
    </div>
  );
};
