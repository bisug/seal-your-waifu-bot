import React from 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { Users, Copy } from 'lucide-react';

export const Referrals = () => {
    const { data: refData, loading } = useApi('/social/referrals');
    const user_id = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;
    const bot_username = import.meta.env.VITE_BOT_USERNAME || 'Seal_Your_WaifuBot';
    const referralLink = `https://t.me/${bot_username}?start=ref_${user_id}`;

    const copyToClipboard = () => {
        navigator.clipboard.writeText(referralLink);
        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
    };

    if (loading) return (
        <div className="px-6 pb-12 pt-4">
            <Skeleton className="h-64 rounded-[3rem]" />
        </div>
    );

    return (
        <div className="px-6 pb-12 pt-4">
            <div className="flex items-center space-x-3 mb-8">
                <Users className="text-brand-accent" size={24} />
                <h1 className="text-2xl font-black uppercase tracking-tighter italic">Network</h1>
            </div>

            <div className="glass-panel p-8 rounded-[3rem] border border-brand-accent/10 bg-brand-accent/5 text-center flex flex-col items-center">
                 <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-4">Your Invitation Link</p>
                 <div className="bg-black/40 border border-white/5 p-4 rounded-2xl w-full mb-6 break-all">
                    <code className="text-[10px] font-mono text-brand-accent">{referralLink}</code>
                 </div>
                 <button
                    onClick={copyToClipboard}
                    className="px-8 py-4 bg-brand-accent text-brand-midnight text-[11px] font-black rounded-2xl uppercase tracking-widest active:scale-95 transition-all shadow-lg shadow-brand-accent/20 flex items-center space-x-2"
                 >
                    <Copy size={16} />
                    <span>Copy Link</span>
                 </button>
            </div>
        </div>
    );
};
