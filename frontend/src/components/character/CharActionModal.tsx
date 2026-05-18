import React, { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Loader2, Zap, Trash2, ArrowRightLeft } from 'lucide-react';
import { useToast } from '../ui/Toast';
import { Modal } from './Modal';
import { apiFetch } from '../../api/client';
import { useUser } from '../../context/UserContext';

export const CharActionModal = ({ selectedChar, setSelectedChar, activeTab, user }) => {
    const { addToast } = useToast();
    const { triggerRefresh } = useUser();
    const [purchaseStage, setPurchaseStage] = useState('idle');
    const [sellStage, setSellStage] = useState('idle');

    useEffect(() => {
        if (!selectedChar) {
            setPurchaseStage('idle');
            setSellStage('idle');
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
            triggerRefresh();
            // Optional: triggerShopRefresh if passed as prop
            setSelectedChar(null);
        } catch (err) {
            addToast(err.message, 'error');
            window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
            setPurchaseStage('idle');
        }
    };

    const handleRecycle = async () => {
        setSellStage('previewing');
        try {
            const preview = await apiFetch('/recycle/preview', {
                method: 'POST',
                body: JSON.stringify([selectedChar.id])
            });

            window.Telegram?.WebApp?.showConfirm(
                `Recycle ${selectedChar.name} for ${preview.reward} Zenith?`,
                async (confirmed) => {
                    if (!confirmed) {
                        setSellStage('idle');
                        return;
                    }

                    setSellStage('selling');
                    try {
                        const res = await apiFetch('/recycle', {
                            method: 'POST',
                            body: JSON.stringify([selectedChar.id])
                        });
                        addToast(`Recycled! +${res.reward} Zenith`, 'success');
                        triggerRefresh();
                        setSelectedChar(null);
                    } catch (err) {
                        addToast(err.message, 'error');
                        setSellStage('idle');
                    }
                }
            );
        } catch (err) {
            addToast(err.message, 'error');
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
                            className="w-full py-4 rounded-3xl bg-brand-accent text-white font-black uppercase text-[10px] tracking-[0.2em] shadow-xl active:scale-95 transition-all flex items-center justify-center gap-2"
                        >
                            BUY FOR {selectedChar.zenith_price} <Zap size={14} />
                        </button>
                    ) : (
                        <div className="p-1 glass-panel rounded-3xl border border-brand-accent/20 flex space-x-1">
                            <button 
                                onClick={() => setPurchaseStage('idle')}
                                className="flex-1 py-3 text-[9px] font-black uppercase tracking-widest text-slate-500"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={handleBuy}
                                disabled={purchaseStage === 'buying'}
                                className="flex-[2] py-3 bg-brand-accent text-white rounded-[1.25rem] text-[9px] font-black uppercase tracking-widest flex items-center justify-center gap-2"
                            >
                                {purchaseStage === 'buying' ? <Loader2 size={14} className="animate-spin" /> : 'Confirm Pay'}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {isOwned && (
                <div className="flex gap-3">
                   <button
                    onClick={handleRecycle}
                    disabled={sellStage !== 'idle'}
                    className="flex-1 py-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-500 text-[10px] font-black uppercase tracking-widest flex items-center justify-center gap-2 active:scale-95 transition-all"
                   >
                     {sellStage !== 'idle' ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
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
