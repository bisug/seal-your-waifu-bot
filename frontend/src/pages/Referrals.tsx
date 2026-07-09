import 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { UserPlus, Copy, CheckCircle2, Send, Gem, Gift, Target, Share2, Sparkles, Activity } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { useToast } from '../components/ui/Toast';
import { ErrorState } from '../components/ui/ErrorState';
import { formatNumber } from '../utils';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { motion, AnimatePresence } from 'framer-motion';

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
            addToast('Protocol error: Referral link not initialized.', 'error');
            return;
        }

        try {
            await navigator.clipboard.writeText(referralLink);
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
            addToast('Deployment link copied to clipboard.', 'success');
        } catch {
            addToast('System error: Manual copying required.', 'error');
        }
    };

    const shareReferral = () => {
        if (!referralLink) {
            addToast('Protocol error: Referral link not initialized.', 'error');
            return;
        }

        const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent('Sync with me on PROTOCOL and secure your welcome assets.')}`;
        window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
        if (window.Telegram?.WebApp?.openTelegramLink) {
            window.Telegram.WebApp.openTelegramLink(shareUrl);
        } else {
            window.open(shareUrl, '_blank', 'noopener,noreferrer');
        }
    };

    if (loading && !referrals?.length) return (
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-10">
            <Skeleton className="h-48 rounded-[32px]" />
            <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-28 rounded-2xl" />
                <Skeleton className="h-28 rounded-2xl" />
            </div>
            <Skeleton className="h-80 rounded-[32px]" />
        </div>
    );

    return (
        <div className="pb-32 pt-8 max-w-2xl mx-auto adaptive-px space-y-12 select-none">
            <header className="space-y-2">
                <div className="flex items-center gap-4">
                   <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                        <UserPlus className="text-brand-accent" size={26} />
                   </div>
                   <div className="flex flex-col gap-1">
                      <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Recruitment</h1>
                      <div className="flex items-center gap-2">
                         <Target size={11} className="text-neutral-600" />
                         <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                            NETWORK EXPANSION & REFERRAL PROTOCOL
                         </p>
                      </div>
                   </div>
                </div>
            </header>

            <section className="space-y-8">
                <Card variant="tactical" className="p-8 flex flex-col items-center text-center space-y-8 bg-gradient-to-br from-[#0c0c0e] to-brand-midnight border-white/[0.06] rounded-[32px] shadow-2xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-6 opacity-[0.02] group-hover:opacity-[0.05] transition-opacity duration-700">
                        <Share2 size={120} className="rotate-12" />
                    </div>

                    <div className="space-y-3 relative z-10 w-full">
                        <p className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.4em] mb-4">DEPLOYMENT_LINK_ID</p>
                        <div className="px-6 py-4 bg-black/60 border border-white/[0.04] rounded-2xl font-mono text-[11px] text-brand-accent break-all max-w-full select-all shadow-inner group-hover:border-brand-accent/20 transition-colors">
                            {referralLink || 'INITIALIZING_SECURE_LINK...'}
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 w-full relative z-10">
                        <Button
                            variant="primary"
                            onClick={shareReferral}
                            disabled={!referralLink}
                            className="py-7 rounded-2xl font-black uppercase text-[12px] tracking-[0.2em] shadow-xl active:scale-[0.98]"
                        >
                            <Send size={18} className="mr-3" strokeWidth={2.5} /> Share
                        </Button>
                        <Button
                            variant="secondary"
                            onClick={copyToClipboard}
                            disabled={!referralLink}
                            className="py-7 rounded-2xl font-black uppercase text-[12px] tracking-[0.2em] border-white/10 shadow-lg active:scale-[0.98]"
                        >
                            <Copy size={18} className="mr-3" strokeWidth={2.5} /> Copy
                        </Button>
                    </div>
                </Card>

                <div className="grid grid-cols-2 gap-4">
                    <Card variant="tactical" className="p-5 flex flex-col justify-between border-white/[0.04] bg-white/[0.01]">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.2em]">Active Syncs</span>
                            <div className="w-8 h-8 rounded-lg bg-brand-accent/10 flex items-center justify-center text-brand-accent border border-brand-accent/20 shadow-sm">
                               <UserPlus size={14} />
                            </div>
                        </div>
                        <div className="text-3xl font-black text-white tabular-nums font-mono drop-shadow-md">{formatNumber(referralCount)}</div>
                    </Card>

                    <Card variant="tactical" className="p-5 flex flex-col justify-between border-white/[0.04] bg-white/[0.01]">
                        <div className="flex items-center justify-between mb-4">
                            <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.2em]">Asset Credits</span>
                            <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-500 border border-amber-500/20 shadow-sm">
                               <Gem size={14} />
                            </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-black text-white tabular-nums font-mono drop-shadow-md">{formatNumber(earnedShards)}</span>
                            <span className="text-[9px] font-black text-neutral-600 uppercase tracking-widest">SHARDS</span>
                        </div>
                    </Card>
                </div>
            </section>

            <section className="space-y-6">
                <div className="flex items-center gap-2 px-1">
                   <h2 className="text-[11px] font-black text-neutral-600 uppercase tracking-[0.3em]">REWARD PARAMETERS</h2>
                   <div className="h-px flex-1 bg-white/[0.03]" />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Card variant="tactical" className="p-5 border-brand-accent/20 bg-brand-accent/[0.02] flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 flex items-center justify-center text-brand-accent shrink-0 border border-brand-accent/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]">
                           <Activity size={24} />
                        </div>
                        <div>
                           <p className="text-[9px] font-black text-brand-accent uppercase tracking-[0.2em] mb-1">OPERATOR BONUS</p>
                           <p className="text-sm font-black text-white uppercase tracking-tight leading-none">
                              {formatNumber(referrerRewardShards)} SHARDS <span className="text-neutral-700 mx-1">+</span> {formatNumber(referrerRewardXp)} XP
                           </p>
                        </div>
                    </Card>
                    <Card variant="tactical" className="p-5 border-success/20 bg-success/[0.02] flex items-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-success/10 flex items-center justify-center text-success shrink-0 border border-success/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                           <Gift size={24} />
                        </div>
                        <div>
                           <p className="text-[9px] font-black text-success uppercase tracking-[0.2em] mb-1">RECRUIT PACKAGE</p>
                           <p className="text-sm font-black text-white uppercase tracking-tight leading-none">
                              {formatNumber(referredRewardShards)} SHARDS <span className="text-neutral-700 mx-1">+</span> LVL {referredPetLevel} COMPANION
                           </p>
                        </div>
                    </Card>
                </div>
            </section>

            <section className="space-y-6">
                <div className="flex items-center justify-between px-1">
                    <div className="flex items-center gap-2">
                        <h2 className="text-[11px] font-black text-neutral-600 uppercase tracking-[0.3em]">NETWORK LOG</h2>
                        <div className="h-1 w-1 rounded-full bg-neutral-800" />
                    </div>
                    <Badge variant="tactical" size="xs" className="opacity-40 font-mono tracking-tighter uppercase">
                        {trackedCount} VERIFIED_UNITS
                    </Badge>
                </div>

                <AnimatePresence mode="wait">
                {error ? (
                    <div className="py-12">
                        <ErrorState message="Protocol mismatch: History synchronization failed." onAction={() => window.location.reload()} />
                    </div>
                ) : trackedCount > 0 ? (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 gap-3">
                        {referrals!.map(referral => (
                            <Card key={referral.referred_id} variant="tactical" className="p-4 flex items-center justify-between border-white/[0.03] bg-white/[0.01] hover:bg-white/[0.02] transition-colors group">
                                <div className="flex items-center gap-4 min-w-0">
                                   <div className="w-10 h-10 rounded-xl bg-brand-midnight border border-white/5 flex items-center justify-center text-neutral-700 font-mono text-[10px] group-hover:text-brand-accent transition-colors">
                                      ID_{String(referral.referred_id).slice(-4)}
                                   </div>
                                   <span className="text-sm font-black text-white uppercase tracking-tight truncate pr-4 drop-shadow-sm">{referral.referred_name}</span>
                                </div>
                                {referral.rewarded && (
                                    <Badge variant="success" icon={CheckCircle2} size="xs" className="rounded-xl px-3 py-1 font-black tracking-[0.1em] shadow-sm border-none bg-success/10 text-success animate-in">
                                        VERIFIED
                                    </Badge>
                                )}
                            </Card>
                        ))}
                    </motion.div>
                ) : (
                    <Card variant="tactical" className="py-24 border-dashed border-white/[0.08] bg-white/[0.01] text-center flex flex-col items-center justify-center space-y-4 rounded-[32px]">
                        <div className="w-16 h-16 rounded-full border border-white/5 flex items-center justify-center opacity-10">
                           <UserPlus size={40} />
                        </div>
                        <div className="space-y-1">
                            <p className="text-[11px] font-black text-neutral-700 uppercase tracking-[0.4em]">Network Empty</p>
                            <p className="text-[9px] font-bold text-neutral-800 uppercase tracking-widest">DEPLOY RECRUITMENT PROTOCOL TO POPULATE</p>
                        </div>
                    </Card>
                )}
                </AnimatePresence>
            </section>

            <div className="flex items-center justify-center gap-3 opacity-20 py-4">
               <Sparkles size={12} className="text-brand-accent" />
               <span className="text-[9px] font-black uppercase tracking-[0.4em] text-white">Network Secure</span>
            </div>
        </div>
    );
};
