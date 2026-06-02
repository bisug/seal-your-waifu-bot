import React, { useState, useEffect } from 'react';
import { Loader2, Zap, Trash2 } from 'lucide-react';
import { useToast } from '../ui/Toast';
import { Modal } from './Modal';
import { apiFetch } from '../../api/client';
import { useUser } from '../../context/UserContext';

interface CharActionModalProps {
    selectedChar: any;
    setSelectedChar: (char: any) => void;
    activeTab: string;
    user: any;
    onPurchaseSuccess?: (char: any) => void;
}

export const CharActionModal = ({ selectedChar, setSelectedChar, activeTab, user, onPurchaseSuccess }: CharActionModalProps) => {
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

    const isOwned = (user?.characters || []).some(c => String(c.id) === String(selectedChar.id));

    const handleBuy = async () => {
        setPurchaseStage('buying');
        try {
            await apiFetch(`/shop/buy/character/${selectedChar.id}`, { method: 'POST' });
            triggerRefresh();
            setSelectedChar(null);
            if (onPurchaseSuccess) onPurchaseSuccess(selectedChar);
        } catch (err: any) {
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
                    } catch (err: any) {
                        addToast(err.message, 'error');
                        setSellStage('idle');
                    }
                }
            );
        } catch (err: any) {
            addToast(err.message, 'error');
            setSellStage('idle');
        }
    };

    const handleSell = async () => {
        setSellStage('selling');
        try {
            // Confirm selling for Shards (using bot's sell logic)
            window.Telegram?.WebApp?.showConfirm(
                `Sell ${selectedChar.name} for Shards?`,
                async (confirmed) => {
                    if (!confirmed) {
                        setSellStage('idle');
                        return;
                    }

                    try {
                        const res = await apiFetch(`/character/sell/${selectedChar.id}`, { method: 'POST' });
                        addToast(`Sold! +${res.reward} Shards`, 'success');
                        triggerRefresh();
                        setSelectedChar(null);
                    } catch (err: any) {
                        addToast(err.message, 'error');
                        setSellStage('idle');
                    }
                }
            );
        } catch (err: any) {
            addToast(err.message, 'error');
            setSellStage('idle');
        }
    };

    const actions = (
        <div className="w-full space-y-3">
            {activeTab === 'shop' && !isOwned && (
                <div className="w-full">
                    {purchaseStage === 'idle' ? (
                        <button 
                            onClick={() => setPurchaseStage('confirm')}
                            className="w-full py-3 rounded-lg bg-brand-accent text-white font-semibold text-sm hover:bg-brand-accent-secondary active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                        >
                            Buy for {selectedChar.zenith_price} <Zap size={16} />
                        </button>
                    ) : (
                        <div className="flex gap-2">
                            <button 
                                onClick={() => setPurchaseStage('idle')}
                                className="flex-1 py-3 rounded-lg bg-white/5 text-neutral-300 hover:bg-white/10 font-semibold text-sm transition-colors"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={handleBuy}
                                disabled={purchaseStage === 'buying'}
                                className="flex-[2] py-3 rounded-lg bg-brand-accent text-white font-semibold text-sm hover:bg-brand-accent-secondary disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2 transition-colors"
                            >
                                {purchaseStage === 'buying' ? <Loader2 size={16} className="animate-spin" /> : 'Confirm Payment'}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {isOwned && (
                <div className="flex gap-2">
                    <button
                        onClick={handleRecycle}
                        disabled={sellStage !== 'idle'}
                        className="flex-1 py-3 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 font-semibold text-sm active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2 transition-all"
                    >
                        {sellStage === 'previewing' || sellStage === 'selling' ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                        <span>Recycle</span>
                    </button>

                    <button
                        onClick={handleSell}
                        disabled={sellStage !== 'idle'}
                        className="flex-1 py-3 rounded-lg bg-brand-accent/10 text-brand-accent hover:bg-brand-accent/20 font-semibold text-sm active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center gap-2 transition-all"
                    >
                        {sellStage === 'selling' ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
                        <span>Sell</span>
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
