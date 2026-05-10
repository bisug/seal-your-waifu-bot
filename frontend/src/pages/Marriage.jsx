import React from 'react';
import { useApi, Skeleton } from '../components/UI';
import { Heart, Calendar } from 'lucide-react';
import { Avatar } from '../components/Avatar';

export const Marriage = () => {
  const { data: marriage, loading } = useApi('/social/marriage');

  if (loading) return <Skeleton className="h-48 rounded-3xl" />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Marriage Status</h2>
      </div>

      {!marriage ? (
        <div className="glass-panel p-10 rounded-3xl border border-white/5 text-center flex flex-col items-center opacity-80">
          <Heart size={40} className="text-slate-800 mb-4" />
          <p className="text-slate-500 text-[11px] font-bold uppercase tracking-widest italic leading-relaxed">
            You are not married yet.<br/>Propose to someone in the bot!
          </p>
        </div>
      ) : (
        <div className="glass-panel p-6 rounded-3xl border border-white/5 relative overflow-hidden text-center">
          <div className="absolute top-0 right-0 w-32 h-32 bg-pink-500/10 rounded-full blur-3xl -mr-10 -mt-10" />

          <div className="relative z-10 flex flex-col items-center">
            <div className="flex items-center justify-center space-x-4 mb-6">
               <Avatar src={window.Telegram?.WebApp?.initDataUnsafe?.user?.photo_url} className="w-16 h-16 rounded-full border-2 border-brand-accent" />
               <div className="text-pink-500 animate-pulse">
                  <Heart size={32} fill="currentColor" />
               </div>
               <Avatar src={marriage.partner_avatar} className="w-16 h-16 rounded-full border-2 border-pink-500" />
            </div>

            <h3 className="text-lg font-black text-white mb-1 uppercase tracking-tight">Married to {marriage.partner_name}</h3>

            <div className="flex items-center justify-center space-x-2 text-slate-500 mb-4">
               <Calendar size={12} />
               <span className="text-[10px] font-bold uppercase tracking-widest">Since {new Date(marriage.married_at).toLocaleDateString()}</span>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-2xl p-4 w-full">
               <p className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em]">Together forever in the harem</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
