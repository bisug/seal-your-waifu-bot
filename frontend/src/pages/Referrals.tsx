import 'react';
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

import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

export const Referrals = () => {
    const { user } = useUser();
    const { addToast } = useToast();
    const { data: referrals, loading, error } = useApi<Referral[]>('/social/referrals', { initialData: [] });
    const { data: stats } = useApi<ReferralStats>('/social/referrals/stats');
    const botUsername = (import.meta.env.VITE_BOT_USERNAME || 'SealYourWaifuBot').replace(/^@/, '');
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

        const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent('Join me on SEAL YOUR WAIFU and claim your welcome bonus.')}`;
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
        if (window.Telegram?.WebApp?.openTelegramLink) {
            window.Telegram.WebApp.openTelegramLink(shareUrl);
        } else {
            window.open(shareUrl, '_blank', 'noopener,noreferrer');
        }
    };

    if (loading && !referrals?.length) return (
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8">
            <Skeleton className="h-40 rounded-2xl" />
            <div className="grid grid-cols-2 gap-3">
                <Skeleton className="h-24 rounded-2xl" />
                <Skeleton className="h-24 rounded-2xl" />
            </div>
            <Skeleton className="h-64 rounded-2xl" />
        </div>
    );

    return (
        <div className="pb-24 pt-6 max-w-2xl mx-auto adaptive-px space-y-8 select-none">
            <header className="space-y-6">
                <div className="space-y-1">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center">
                            <UserPlus className="text-brand-accent" size={22} />
                        </div>
                        <h1 className="text-2xl font-black text-white tracking-tighter uppercase">Invite Friends</h1>
                    </div>
                    <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">
                        Expand the seal network and secure mutual rewards.
                    </p>
                </div>

                <Card className="p-6 flex flex-col items-center text-center space-y-6 bg-gradient-to-br from-brand-deep to-brand-surface">
                    <div className="space-y-1">
                        <p className="text-[10px] font-black text-neutral-500 uppercase tracking-[0.2em]">Personal Deployment Link</p>
                        <div className="px-4 py-3 bg-brand-midnight border border-white/5 rounded-xl font-mono text-[10px] text-brand-accent break-all max-w-full select-all">
                            {referralLink || 'INITIALIZING PROTOCOL...'}
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3 w-full">
                        <Button
                            variant="primary"
                            onClick={shareReferral}
                            disabled={!referralLink}
                            className="py-6 rounded-2xl font-black uppercase text-[11px] tracking-widest"
                        >
                            <Send size={16} className="mr-2" /> Share
                        </Button>
                        <Button
                            variant="secondary"
                            onClick={copyToClipboard}
                            disabled={!referralLink}
                            className="py-6 rounded-2xl font-black uppercase text-[11px] tracking-widest border-white/5"
                        >
                            <Copy size={16} className="mr-2" /> Copy
                        </Button>
                    </div>
                </Card>
            </header>

            <section className="grid grid-cols-2 gap-4">
                <Card className="p-4 flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-[10px] font-black text-neutral-500 uppercase tracking-widest">Successful Syncs</span>
                        <UserPlus size={16} className="text-brand-accent" />
                    </div>
                    <div className="text-3xl font-black text-white tabular-nums">{formatNumber(referralCount)}</div>
                </Card>

                <Card className="p-4 flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-[10px] font-black text-neutral-500 uppercase tracking-widest">Credits Earned</span>
                        <Gem size={16} className="text-brand-accent" />
                    </div>
                    <div className="flex items-baseline gap-1">
                        <span className="text-3xl font-black text-white tabular-nums">{formatNumber(earnedShards)}</span>
                        <span className="text-[10px] font-black text-neutral-500 uppercase">SHARDS</span>
                    </div>
                </Card>
            </section>

            <section className="space-y-4">
                <h2 className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] px-1">Mutual Benefits</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <Card className="p-4 border-brand-accent/10 bg-brand-accent/5">
                        <p className="text-[9px] font-black text-brand-accent uppercase tracking-widest mb-2">Deployer Reward</p>
                        <p className="text-sm font-black text-white uppercase">{formatNumber(referrerRewardShards)} SHARDS + {formatNumber(referrerRewardXp)} XP</p>
                    </Card>
                    <Card className="p-4 border-emerald-500/10 bg-emerald-500/5">
                        <p className="text-[9px] font-black text-emerald-500 uppercase tracking-widest mb-2">Recruit Reward</p>
                        <p className="text-sm font-black text-white uppercase">{formatNumber(referredRewardShards)} SHARDS + LVL {referredPetLevel} PET</p>
                    </Card>
                </div>
            </section>

            <section className="space-y-4">
                <div className="flex items-center justify-between px-1">
                    <h2 className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em]">Network Log</h2>
                    <Badge variant="secondary" size="xs" className="rounded-lg font-black tracking-widest">
                        {trackedCount} RECRUITS
                    </Badge>
                </div>

                {error ? (
                    <ErrorState message="Protocol error: History synchronization failed." onAction={() => window.location.reload()} />
                ) : trackedCount > 0 ? (
                    <div className="space-y-2">
                        {referrals!.map(referral => (
                            <Card key={referral.referred_id} className="p-3 flex items-center justify-between">
                                <span className="text-sm font-black text-white uppercase tracking-tight truncate pr-3">{referral.referred_name}</span>
                                {referral.rewarded && (
                                    <Badge variant="success" icon={CheckCircle2} size="xs" className="rounded-lg">
                                        SECURED
                                    </Badge>
                                )}
                            </Card>
                        ))}
                    </div>
                ) : (
                    <Card className="py-16 border-dashed bg-brand-deep/30 text-center flex flex-col items-center">
                        <UserPlus size={32} className="text-neutral-800 mb-4" />
                        <p className="text-[10px] font-black text-neutral-600 uppercase tracking-widest">No recruits detected in the network.</p>
                    </Card>
                )}
            </section>
        </div>
    );
};
