import React from 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { UserPlus, Copy, CheckCircle2, Send, Gem, Gift } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { useToast } from '../components/ui/Toast';

interface Referral {
    referred_id: number;
    referred_name: string;
    rewarded: boolean;
}

interface ReferralStats {
    invited_count: number;
    tracked_count: number;
    earned_shards: number;
    referrer_reward_shards: number;
    referrer_reward_xp: number;
    referred_reward_shards: number;
    referred_pet_level: number;
}

const formatNumber = (value: number | undefined) => (value ?? 0).toLocaleString();

export const Referrals = () => {
    const { user } = useUser();
    const { addToast } = useToast();
    const { data: referrals, loading, error } = useApi<Referral[]>('/social/referrals', { initialData: [] });
    const { data: stats } = useApi<ReferralStats>('/social/referrals/stats');
    const botUsername = (import.meta.env.VITE_BOT_USERNAME || 'Seal_Your_WaifuBot').replace(/^@/, '');
    const referralLink = user?.id ? `https://t.me/${botUsername}?start=ref_${user.id}` : '';
    const referralCount = stats?.invited_count ?? referrals?.length ?? 0;
    const trackedCount = stats?.tracked_count ?? referrals?.length ?? 0;
    const earnedShards = stats?.earned_shards ?? referralCount * 500;
    const referrerRewardShards = stats?.referrer_reward_shards ?? 500;
    const referrerRewardXp = stats?.referrer_reward_xp ?? 50;
    const referredRewardShards = stats?.referred_reward_shards ?? 1500;
    const referredPetLevel = stats?.referred_pet_level ?? 10;

    const copyToClipboard = async () => {
        if (!referralLink) {
            addToast('Referral link is not ready yet.', 'error');
            return;
        }

        try {
            await navigator.clipboard.writeText(referralLink);
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
            addToast('Referral link copied.', 'success');
        } catch {
            addToast('Could not copy the link. Select and copy it manually.', 'error');
        }
    };

    const shareReferral = () => {
        if (!referralLink) {
            addToast('Referral link is not ready yet.', 'error');
            return;
        }

        const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent('Join me on Seal Bot and claim your welcome bonus.')}`;
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
        if (window.Telegram?.WebApp?.openTelegramLink) {
            window.Telegram.WebApp.openTelegramLink(shareUrl);
        } else {
            window.open(shareUrl, '_blank', 'noopener,noreferrer');
        }
    };

    if (loading && !referrals?.length) return (
        <div className="px-6 pb-12 pt-4 max-w-2xl mx-auto">
            <Skeleton className="h-64 rounded-lg" />
        </div>
    );

    return (
        <div className="px-6 pb-12 pt-4 max-w-2xl mx-auto">
            <div className="flex items-center space-x-3 mb-8">
                <UserPlus className="text-brand-accent" size={24} />
                <div>
                    <h1 className="text-xl font-bold text-white tracking-tight">Referrals</h1>
                    <p className="text-sm font-medium text-neutral-400">Invite friends and track who joined.</p>
                </div>
            </div>

            <section className="bg-brand-deep p-5 rounded-lg border border-white/5 text-center flex flex-col items-center shadow-sm">
                  <p className="text-xs text-neutral-500 font-semibold uppercase tracking-wider mb-3">Your invite link</p>
                  <div className="bg-black/30 border border-white/5 p-4 rounded-lg w-full mb-5 break-all select-text">
                     <code className="text-xs font-mono text-brand-accent">{referralLink || 'Preparing your link...'}</code>
                  </div>
                  <div className="grid grid-cols-2 gap-3 w-full">
                    <button
                        onClick={copyToClipboard}
                        disabled={!referralLink}
                        className="h-11 bg-brand-accent text-white text-sm font-bold rounded-lg active:scale-95 transition-all shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        <Copy size={16} />
                        <span>Copy</span>
                    </button>
                    <button
                        onClick={shareReferral}
                        disabled={!referralLink}
                        className="h-11 bg-white/10 text-white text-sm font-bold rounded-lg active:scale-95 transition-all border border-white/10 flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        <Send size={16} />
                        <span>Share</span>
                    </button>
                  </div>
            </section>

            <section className="mt-4 grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-white/5 bg-brand-deep p-4 min-h-[92px]">
                    <div className="flex items-center gap-2 text-brand-accent mb-3">
                        <UserPlus size={16} />
                        <span className="text-xs font-semibold uppercase text-neutral-500">Joined</span>
                    </div>
                    <p className="text-2xl font-bold text-white tabular-nums leading-none">{formatNumber(referralCount)}</p>
                    {trackedCount !== referralCount && (
                        <p className="mt-2 text-xs font-medium text-neutral-500">{formatNumber(trackedCount)} visible in history</p>
                    )}
                </div>
                <div className="rounded-lg border border-white/5 bg-brand-deep p-4 min-h-[92px]">
                    <div className="flex items-center gap-2 text-brand-accent mb-3">
                        <Gem size={16} />
                        <span className="text-xs font-semibold uppercase text-neutral-500">Earned</span>
                    </div>
                    <p className="text-2xl font-bold text-white tabular-nums leading-none">{formatNumber(earnedShards)}</p>
                    <p className="mt-2 text-xs font-medium text-neutral-500">Shards</p>
                </div>
            </section>

            <section className="mt-4 rounded-lg border border-white/5 bg-brand-deep p-4">
                <div className="flex items-center gap-2 text-brand-accent mb-3">
                    <Gift size={16} />
                    <h2 className="text-sm font-bold text-white">Referral rewards</h2>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <div className="rounded-lg bg-brand-midnight border border-white/5 px-3 py-2">
                        <p className="text-xs font-medium text-neutral-500 mb-1">You receive</p>
                        <p className="text-sm font-bold text-white">{formatNumber(referrerRewardShards)} Shards + {formatNumber(referrerRewardXp)} XP</p>
                    </div>
                    <div className="rounded-lg bg-brand-midnight border border-white/5 px-3 py-2">
                        <p className="text-xs font-medium text-neutral-500 mb-1">Friend receives</p>
                        <p className="text-sm font-bold text-white">{formatNumber(referredRewardShards)} Shards + Level {referredPetLevel} Pet</p>
                    </div>
                </div>
            </section>

            <section className="mt-4 bg-brand-deep p-5 rounded-lg border border-white/5 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-bold text-white">Joined friends</h2>
                    <span className="text-sm font-bold text-brand-accent tabular-nums">{formatNumber(trackedCount)}</span>
                </div>

                {error ? (
                    <p className="text-sm text-neutral-500">Referral history could not be loaded right now.</p>
                ) : trackedCount > 0 ? (
                    <div className="space-y-2">
                        {referrals!.map(referral => (
                            <div key={referral.referred_id} className="flex items-center justify-between rounded-lg bg-brand-midnight px-3 py-2 border border-white/5">
                                <span className="text-sm font-medium text-neutral-200 truncate pr-3">{referral.referred_name}</span>
                                {referral.rewarded && (
                                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-500">
                                        <CheckCircle2 size={14} />
                                        Rewarded
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-sm text-neutral-500">No friends have joined from your link yet.</p>
                )}
            </section>
        </div>
    );
};
