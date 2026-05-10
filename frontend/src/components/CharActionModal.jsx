import React, { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Loader2, Zap, Trash2, ArrowRightLeft } from 'lucide-react';
import { useToast, Modal } from './UI';
import { apiFetch } from '../api';

export const CharActionModal = ({ selectedChar, setSelectedChar, activeTab, user }) => {
    const { addToast } = useToast();
    const [purchaseStage, setPurchaseStage] = useState('idle');
    const [sellStage, setSellStage] = useState('idle');

    useEffect(() => {
        if (!selectedChar) {
            Promise.resolve().then(() => {
                setPurchaseStage('idle');
                setSellStage('idle');
            });
        }
    }, [selectedChar]);

    if (!selectedChar) return null;

    const isOwned = (user?.characters || []).some(c => c.id === selectedChar.id);

    const handleBuy = async () => {
        setPurchaseStage('buying');
        try {
            await apiFetch(`/shop/buy/character/${selectedChar.id}`, { method: 'POST' });
            addToast(`Acquired ${selectedChar.name}!`, 'success');
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
            window.dispatchEvent(new CustomEvent('user-data-refresh'));
            window.dispatchEvent(new CustomEvent('shop-data-refresh'));
            setSelectedChar(null);
        } catch (err) {
            addToast(err.message, 'error');
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
            setPurchaseStage('idle');
        }
    };

    const handleRecycle = async () => {
        if (!window.confirm(`Recycle ${selectedChar.name} for Zenith?`)) return;
        setSellStage('selling');
        try {
            const res = await apiFetch('/recycle', {
                method: 'POST',
                body: JSON.stringify([selectedChar.id])
            });
            addToast(`Recycled! +${res.reward} Zenith`, 'success');
            window.dispatchEvent(new CustomEvent('user-data-refresh'));
            setSelectedChar(null);
        } catch (err) {
            addToast(err.message, 'error');
        } finally {
            setSellStage('idle');
        }
    };

    const actions = (
        <div className="space-y-4 w-full">
            {activeTab === 'market' && !isOwned && (
                <div className="w-full">
                    {purchaseStage === 'idle' ? (
                        <button 
                            onClick={() => setPurchaseStage('confirm')}
                            className="w-full py-5 rounded-[2rem] bg-brand-accent text-white font-black uppercase text-[11px] tracking-[0.3em] shadow-xl active:scale-95 transition-all flex items-center justify-center gap-3"
                        >
                            BUY FOR {selectedChar.zenith_price} <Zap size={16} />
                        </button>
                    ) : (
                        <div className="p-1 glass-panel rounded-[2rem] border border-brand-accent/20 flex space-x-1">
                            <button 
                                onClick={() => setPurchaseStage('idle')}
                                className="flex-1 py-4 text-[10px] font-black uppercase tracking-widest text-slate-500"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={handleBuy}
                                disabled={purchaseStage === 'buying'}
                                className="flex-[2] py-4 bg-brand-accent text-white rounded-[1.8rem] text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-2"
                            >
                                {purchaseStage === 'buying' ? <Loader2 size={16} className="animate-spin" /> : 'Confirm Pay'}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {isOwned && (
                <div className="flex gap-3">
                   <button
                    onClick={handleRecycle}
                    disabled={sellStage === 'selling'}
                    className="flex-1 py-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500 text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-2 active:scale-95 transition-all"
                   >
                     {sellStage === 'selling' ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                     <span>Recycle</span>
                   </button>

                   <button
                    onClick={() => addToast('Trading soon...', 'info')}
                    className="flex-1 py-4 rounded-2xl bg-white/5 border border-white/10 text-white/50 text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-2 active:scale-95 transition-all"
                   >
                     <ArrowRightLeft size={14} />
                     <span>Trade</span>
                   </button>
                </div>
            )}
        </div>
    );

    return (
        <Modal
            character={selectedChar}
            onClose={() => setSelectedChar(null)}
            actions={actions}
        />
    );
};
