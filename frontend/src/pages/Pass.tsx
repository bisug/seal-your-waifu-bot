import { useCallback, useState } from 'react';
import { CheckCircle2, Crown, Gift, Loader2, Lock, Star, Ticket, TicketCheck, TicketPlus, Zap, Heart } from 'lucide-react';
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
          res.status === 'already_claimed' ? 'Reward already secured' : `Collected rewards for Level ${level}`,
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
      addToast(res.message || 'Bank contents secured', 'success');
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
    <div className="pb-24 pt-4 max-w-2xl mx-auto adaptive-px space-y-4">
        <div className="flex justify-between items-center">
            <Skeleton className="h-6 w-40 rounded-md" />
            <Skeleton className="h-10 w-16 rounded-lg" />
        </div>
        <Skeleton className="h-2 w-full rounded-full" />
        <div className="grid grid-cols-3 gap-2.5">
            {[1,2,3].map(i => <Skeleton key={i} className="h-20 rounded-lg" />)}
        </div>
        <Skeleton className="h-32 rounded-lg" />
    </div>
  );

  const userLevel = Math.min(Number(passData.level || 0), Number(passData.max_level || 100));
  const maxLevel = Number(passData.max_level || 100);
  const claimedLevels = Array.isArray(passData.claimed_levels) ? passData.claimed_levels : [];
  const milestones = Array.isArray(passData.milestones) ? passData.milestones : [5, 10, 20, 25, 30, 40, 50, 60, 75, 80, 90, 100];
  const currentTier = passData.pass_type || 'free';
  const bank = bankSummary(passData.pass_bank);
  const nextTier = currentTier === 'free' ? 'premium' : currentTier === 'premium' ? 'elite' : null;
  const _progressPercent = Math.min(100, Math.round((userLevel / Math.max(maxLevel, 1)) * 100));
  const nextBenefits = nextTier ? passData.benefits?.[nextTier] : null;

  return (
    <div className="pb-24 pt-4 max-w-2xl mx-auto adaptive-px space-y-6">
      <header className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-md bg-brand-accent/5 border border-brand-accent/20 flex items-center justify-center text-brand-accent">
                    <TicketCheck size={20} />
                </div>
                <h1 className="text-lg font-black text-white tracking-tighter uppercase truncate max-w-[180px]">{passData.season_name || 'WAIFU PASS'}</h1>
            </div>
            <p className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.2em] px-0.5">SEASONAL PROGRESSION</p>
          </div>
          <Card variant="tactical" className="px-3 py-1.5 border-brand-accent/20 bg-brand-accent/5">
            <p className="text-[8px] font-black text-brand-accent uppercase tracking-widest text-center">TIER</p>
            <p className="text-xl font-black text-white tabular-nums leading-none text-center font-mono">{userLevel}</p>
          </Card>
        </div>

        <div className="space-y-1.5">
            <ProgressBar current={userLevel} total={maxLevel} label="WAIFU PROGRESS" color="bg-brand-accent" compact />
        </div>
      </header>

      <section className="grid grid-cols-3 gap-2.5">
        {TIER_ORDER.map((tier) => {
          const Icon = TIER_ICON[tier as keyof typeof TIER_ICON];
          const active = currentTier === tier;
          const unlocked = TIER_ORDER.indexOf(currentTier) >= TIER_ORDER.indexOf(tier);
          return (
            <Card
              key={tier}
              variant="tactical"
              className={cn(
                'p-3 flex flex-col items-center justify-center text-center space-y-1.5 transition-all',
                active ? 'border-brand-accent/40 bg-brand-accent/[0.03]' : unlocked ? 'border-emerald-500/20' : 'opacity-40 grayscale'
              )}
            >
              <Icon size={16} className={active ? 'text-brand-accent' : unlocked ? 'text-emerald-500' : 'text-neutral-700'} fill={tier === 'elite' && unlocked ? 'currentColor' : 'none'} />
              <p className="text-[9px] font-black text-white uppercase tracking-widest">{tier}</p>
              <Badge variant={unlocked ? "success" : "tactical"} size="xs" className="border-none py-0 px-1 opacity-80">
                {unlocked ? 'SECURED' : `${passData.prices?.[tier] ?? 0}★`}
              </Badge>
            </Card>
          );
        })}
      </section>

      {nextTier && (
        <Card variant="tactical" className="p-5 space-y-5 bg-gradient-to-br from-[#0c0c0e] to-brand-midnight border-white/[0.05] relative overflow-hidden">
          <div className="absolute top-0 right-0 p-3 opacity-[0.03]">
              <Heart size={80} className="rotate-12" fill="currentColor" />
          </div>

          <div className="flex items-start justify-between gap-4 relative z-10">
            <div className="space-y-1">
              <Badge variant="primary" icon={Zap} size="xs" className="rounded-sm px-1.5 py-0 text-[8px] font-black tracking-widest mb-1 uppercase">Recommended</Badge>
              <h2 className="text-lg font-black text-white uppercase tracking-tight">{nextTier} ACCESS</h2>
              <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest leading-relaxed max-w-[200px]">
                {passData.tiers?.[nextTier]?.summary || 'SECURE EXCLUSIVE REWARDS & BUFFS'}
              </p>
            </div>
            <div className="flex flex-col items-end">
                <span className="text-lg font-black text-white tabular-nums font-mono">{passData.upgrade_prices?.[nextTier]}</span>
                <span className="text-[8px] font-black text-neutral-600 uppercase tracking-widest">STARS</span>
            </div>
          </div>

          {nextBenefits && (
            <div className="grid grid-cols-2 gap-2 relative z-10">
              <Card variant="tactical" className="bg-black/20 p-2.5 space-y-1 border-white/[0.03]">
                <p className="text-[8px] font-black text-neutral-700 uppercase tracking-widest">Shard Rate</p>
                <p className="text-[10px] font-black text-white uppercase font-mono">{percentBonus(nextBenefits.hunt_multiplier)}</p>
              </Card>
              <Card variant="tactical" className="bg-black/20 p-2.5 space-y-1 border-white/[0.03]">
                <p className="text-[8px] font-black text-neutral-700 uppercase tracking-widest">Drop Luck</p>
                <p className="text-[10px] font-black text-white uppercase font-mono">{percentBonus(nextBenefits.egg_drop_multiplier)}</p>
              </Card>
              <Card variant="tactical" className="bg-black/20 p-2.5 space-y-1 border-white/[0.03]">
                <p className="text-[8px] font-black text-neutral-700 uppercase tracking-widest">Sync Speed</p>
                <p className="text-[10px] font-black text-white uppercase font-mono">{percentBonus(nextBenefits.incubation_multiplier, true)}</p>
              </Card>
              <Card variant="tactical" className="bg-black/20 p-2.5 space-y-1 border-white/[0.03]">
                <p className="text-[8px] font-black text-neutral-700 uppercase tracking-widest">Hatch Slots</p>
                <p className="text-[10px] font-black text-white uppercase font-mono">{nextBenefits.incubation_slots} ACTIVE</p>
              </Card>
            </div>
          )}

          <Button
            onClick={() => handleUpgrade(nextTier)}
            isLoading={upgrading === nextTier}
            variant="tactical"
            className="w-full py-5 rounded-md uppercase tracking-[0.2em] text-[10px] font-black relative z-10"
          >
            ACTIVATE {nextTier.toUpperCase()} PROTOCOL
          </Button>
        </Card>
      )}

      {currentTier !== 'free' && bank.hasValue && (
        <Card variant="tactical" className="p-3.5 border-amber-500/20 bg-amber-500/[0.02] flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500">
                    <Gift size={20} />
                </div>
                <div>
                    <h2 className="text-xs font-black text-amber-500 uppercase tracking-widest">REWARD VAULT</h2>
                    <p className="text-[9px] font-bold text-amber-500/40 uppercase tracking-widest mt-0.5 font-mono">
                        {formatNumber(bank.shards)} SHARDS {bank.eggs ? `+ ${bank.eggs} EGGS` : ''}
                    </p>
                </div>
            </div>
            <Button
              variant="tactical"
              size="sm"
              onClick={handleClaimBank}
              isLoading={claimingBank}
              className="bg-amber-500 text-black hover:bg-amber-400 border-none px-5 font-black uppercase text-[9px] tracking-widest h-8"
            >
              CLAIM
            </Button>
        </Card>
      )}

      <section className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-[9px] font-black text-neutral-700 uppercase tracking-[0.3em]">REWARD PIPELINE</h2>
          <Badge variant="tactical" size="xs" className="opacity-60">
            {claimedLevels.length} / {maxLevel} SECURED
          </Badge>
        </div>

        <div className="space-y-3">
            {milestones.map((lvl: number) => {
            const track = passData.tracks?.[lvl];
            if (!track) return null;
            const isReached = userLevel >= lvl;
            const isClaimed = claimedLevels.includes(lvl);

            return (
                <Card
                variant="tactical"
                key={lvl}
                className={cn(
                    'p-4 space-y-4 transition-all duration-300',
                    isReached ? 'border-white/[0.08]' : 'opacity-40 grayscale'
                )}
                >
                <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            'w-10 h-10 rounded-md flex flex-col items-center justify-center border transition-all duration-500',
                            isReached ? 'border-brand-accent/40 text-brand-accent bg-brand-accent/5' : 'border-white/[0.05] text-neutral-700'
                        )}>
                            <span className="text-[7px] font-black uppercase opacity-60">LVL</span>
                            <span className="text-base font-black tabular-nums leading-none font-mono">{lvl}</span>
                        </div>
                        <div>
                            <p className="text-xs font-black text-white uppercase tracking-tight">Milestone {lvl}</p>
                            <div className="flex items-center gap-1.5 mt-0.5">
                                {isClaimed ? (
                                    <Badge variant="success" size="xs" className="border-none py-0 px-1 uppercase opacity-90">Secured</Badge>
                                ) : isReached ? (
                                    <Badge variant="primary" size="xs" className="border-none py-0 px-1 uppercase opacity-90">Available</Badge>
                                ) : (
                                    <Badge variant="tactical" size="xs" className="border-none py-0 px-1 uppercase opacity-60">Locked</Badge>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="shrink-0">
                        {isClaimed ? (
                        <div className="w-8 h-8 rounded-md bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                            <CheckCircle2 size={18} strokeWidth={3} />
                        </div>
                        ) : isReached ? (
                        <Button
                            onClick={() => handleClaim(lvl)}
                            isLoading={claiming === lvl}
                            variant="tactical"
                            className="h-8 px-4 text-[9px] font-black uppercase tracking-widest"
                        >
                            CLAIM
                        </Button>
                        ) : (
                        <div className="w-8 h-8 rounded-md bg-[#0a0a0c] border border-white/[0.03] flex items-center justify-center text-neutral-800">
                            <Lock size={14} />
                        </div>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-1.5">
                    {TIER_ORDER.map((tier) => {
                    const unlocked = TIER_ORDER.indexOf(currentTier) >= TIER_ORDER.indexOf(tier);
                    const Icon = TIER_ICON[tier as keyof typeof TIER_ICON];
                    return (
                        <div key={tier} className={cn(
                            "flex items-center justify-between gap-4 px-3 py-2 rounded-md border transition-all",
                            unlocked ? "bg-white/[0.01] border-white/[0.03]" : "bg-black/40 border-transparent opacity-40"
                        )}>
                        <div className="flex items-center gap-2.5 min-w-0">
                            <Icon size={12} className={unlocked ? 'text-brand-accent' : 'text-neutral-800'} fill={tier === 'elite' && unlocked ? 'currentColor' : 'none'} />
                            <span className="text-[8px] font-black text-neutral-600 uppercase tracking-widest">{tier}</span>
                        </div>
                        <span className={cn('text-[10px] font-black text-right tracking-tight truncate ml-4 font-mono uppercase', unlocked ? 'text-white' : 'text-neutral-800')}>
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
