import React from 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { UserPlus, Copy, CheckCircle2 } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { useToast } from '../components/ui/Toast';

interface Referral {
    referred_id: number;
    referred_name: string;
    rewarded: boolean;
}

export const Referrals = () => {
    const { user } = useUser();
    const { addToast } = useToast();
    const { data: referrals, loading, error } = useApi<Referral[]>('/social/referrals', { initialData: [] });
    const botUsername = import.meta.env.VITE_BOT_USERNAME || 'Seal_Your_WaifuBot';
    const referralLink = user?.id ? `https://t.me/${botUsername}?start=ref_${user.id}` : '';
    const referralCount = referrals?.length || 0;

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

    if (loading && !referrals?.length) return (
        <div className="px-6 pb-12 pt-4">
            <Skeleton className="h-64 rounded-2xl" />
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

            <section className="bg-brand-deep p-6 rounded-xl border border-white/5 text-center flex flex-col items-center shadow-sm">
                 <p className="text-xs text-neutral-500 font-semibold uppercase tracking-wider mb-3">Your invite link</p>
                 <div className="bg-black/30 border border-white/5 p-4 rounded-lg w-full mb-5 break-all select-text">
                    <code className="text-xs font-mono text-brand-accent">{referralLink || 'Preparing your link...'}</code>
                 </div>
                 <button
                    onClick={copyToClipboard}
                    disabled={!referralLink}
                    className="px-6 py-3 bg-brand-accent text-white text-sm font-bold rounded-lg active:scale-95 transition-all shadow-sm flex items-center space-x-2 disabled:opacity-50"
                 >
                    <Copy size={16} />
                    <span>Copy link</span>
                 </button>
            </section>

            <section className="mt-6 bg-brand-deep p-5 rounded-xl border border-white/5 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-bold text-white">Joined friends</h2>
                    <span className="text-sm font-bold text-brand-accent tabular-nums">{referralCount}</span>
                </div>

                {error ? (
                    <p className="text-sm text-neutral-500">Referral history could not be loaded right now.</p>
                ) : referralCount > 0 ? (
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
