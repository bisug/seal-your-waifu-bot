import React from 'react';
import { useApi, Skeleton } from '../components/UI';
import { Users, Gift, Copy, Check } from 'lucide-react';

export const Referrals = () => {
  const { data: referrals, loading } = useApi('/social/referrals');
  const [copied, setCopied] = React.useState(false);
  const user_id = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || '0';
  const referralLink = `https://t.me/Seal_Your_WaifuBot?start=ref_${user_id}`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(referralLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading && !referrals) return <Skeleton className="h-48 rounded-3xl" />;

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-3">Your Referral Link</h2>
        <div className="glass-panel p-4 rounded-2xl border border-white/5 flex items-center justify-between">
          <div className="truncate flex-1 mr-4">
             <p className="text-[10px] font-mono text-slate-400 truncate">{referralLink}</p>
          </div>
          <button
            onClick={copyToClipboard}
            className="p-2 bg-brand-accent/10 rounded-xl text-brand-accent active:scale-90 transition-transform"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
          </button>
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Milestone Rewards</h2>
          <span className="text-[9px] font-black text-brand-accent uppercase tracking-widest">{referrals?.length || 0} Referred</span>
        </div>

        <div className="grid grid-cols-1 gap-3">
          {[
            { target: 1, reward: '1,000 Zenith', icon: Gift },
            { target: 5, reward: 'Rare Egg', icon: Gift },
            { target: 10, reward: 'Legendary Egg', icon: Gift },
          ].map((milestone, i) => {
            const isReached = (referrals?.length || 0) >= milestone.target;
            return (
              <div key={i} className={`glass-panel p-4 rounded-2xl border border-white/5 flex items-center justify-between ${isReached ? 'bg-brand-accent/5 border-brand-accent/20' : 'opacity-60'}`}>
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-xl ${isReached ? 'bg-brand-accent/20 text-brand-accent' : 'bg-white/5 text-slate-500'}`}>
                    <milestone.icon size={16} />
                  </div>
                  <div>
                    <p className="text-[10px] font-black text-white uppercase tracking-widest">{milestone.reward}</p>
                    <p className="text-[8px] font-bold text-slate-500 uppercase">Target: {milestone.target} Users</p>
                  </div>
                </div>
                {isReached && <Check size={16} className="text-brand-accent" />}
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-3">Recent Referrals</h2>
        {referrals?.length === 0 ? (
          <div className="glass-panel p-8 rounded-2xl border border-white/5 text-center flex flex-col items-center opacity-80">
            <Users size={32} className="text-slate-800 mb-3" />
            <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest italic">No referrals yet.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {referrals?.map(ref => (
              <div key={ref.referred_id} className="glass-panel p-3 rounded-xl border border-white/5 flex items-center justify-between">
                <span className="text-[10px] font-black text-white">{ref.referred_name}</span>
                <span className="text-[8px] font-black text-brand-accent uppercase tracking-widest">Completed</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
