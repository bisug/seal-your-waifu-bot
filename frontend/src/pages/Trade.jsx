import React, { useState } from 'react';
import { useApi, useToast, Skeleton } from '../components/UI';
import { Repeat, Check, X, ArrowRightLeft } from 'lucide-react';
import { apiFetch } from '../api';

export const Trade = () => {
  const { data: offers, loading, execute: fetchOffers } = useApi('/trade/offers');
  const { addToast } = useToast();
  const [processing, setProcessing] = useState(null);

  const handleResponse = async (tradeId, action) => {
    setProcessing(tradeId);
    try {
      await apiFetch(`/trade/respond/${tradeId}`, {
        method: 'POST',
        body: JSON.stringify({ action })
      });
      addToast(`Trade ${action}ed!`, 'success');
      fetchOffers();
    } catch (err) {
      addToast(err.message, 'error');
    } finally {
      setProcessing(null);
    }
  };

  if (loading && !offers) return (
    <div className="space-y-4">
      {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 rounded-3xl" />)}
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Active Trade Offers</h2>
        <button onClick={() => fetchOffers()} className="text-brand-accent text-[10px] font-black uppercase tracking-widest">Refresh</button>
      </div>

      {offers?.length === 0 ? (
        <div className="glass-panel p-10 rounded-3xl border border-white/5 text-center flex flex-col items-center opacity-80">
          <ArrowRightLeft size={40} className="text-slate-800 mb-4" />
          <p className="text-slate-500 text-[11px] font-bold uppercase tracking-widest italic">No active trades found.</p>
        </div>
      ) : (
        offers?.map(offer => (
          <div key={offer.id} className="glass-panel p-4 rounded-3xl border border-white/5 relative overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-brand-accent/10 flex items-center justify-center">
                  <Repeat size={14} className="text-brand-accent" />
                </div>
                <span className="text-[10px] font-black uppercase tracking-widest text-white">{offer.sender_name}</span>
              </div>
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest bg-white/5 px-2 py-0.5 rounded-lg">{offer.status}</span>
            </div>

            <div className="grid grid-cols-2 gap-4 items-center mb-4">
              <div className="text-center">
                <div className="aspect-square rounded-2xl overflow-hidden border border-white/10 mb-2">
                  <img src={offer.sender_char.img_url} className="w-full h-full object-cover" />
                </div>
                <p className="text-[10px] font-black text-white truncate">{offer.sender_char.name}</p>
                <p className="text-[8px] font-bold text-slate-500 uppercase truncate">{offer.sender_char.rarity}</p>
              </div>

              <div className="flex justify-center">
                <ArrowRightLeft className="text-slate-700" size={20} />
              </div>

              <div className="text-center absolute right-4 top-16 w-[calc(50%-1.5rem)]">
                 <div className="aspect-square rounded-2xl overflow-hidden border border-white/10 mb-2">
                  <img src={offer.receiver_char.img_url} className="w-full h-full object-cover" />
                </div>
                <p className="text-[10px] font-black text-white truncate">{offer.receiver_char.name}</p>
                <p className="text-[8px] font-bold text-slate-500 uppercase truncate">{offer.receiver_char.rarity}</p>
              </div>
            </div>

            {offer.receiver_id === window.Telegram?.WebApp?.initDataUnsafe?.user?.id && offer.status === 'pending' && (
              <div className="flex space-x-2">
                <button
                  disabled={!!processing}
                  onClick={() => handleResponse(offer.id, 'accept')}
                  className="flex-1 bg-brand-accent text-white py-2 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center justify-center space-x-2 active:scale-95 transition-transform"
                >
                  <Check size={12} />
                  <span>Accept</span>
                </button>
                <button
                  disabled={!!processing}
                  onClick={() => handleResponse(offer.id, 'reject')}
                  className="flex-1 bg-white/5 text-red-500 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center justify-center space-x-2 active:scale-95 transition-transform"
                >
                  <X size={12} />
                  <span>Reject</span>
                </button>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
};
