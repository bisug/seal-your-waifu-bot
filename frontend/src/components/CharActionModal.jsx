import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Loader2 } from 'lucide-react';
import { Modal, useToast } from './UI';
import { apiFetch } from '../api';
import { formatNumber } from '../utils';

export const CharActionModal = ({ selectedChar, setSelectedChar, activeTab, user }) => {
    const { addToast } = useToast();
    const [purchaseStage, setPurchaseStage] = useState('idle');

    useEffect(() => {
        if (!selectedChar) setPurchaseStage('idle');
    }, [selectedChar]);

    let actions = null;

    if (activeTab === 'profile' && selectedChar?.count > 1) {
        actions = (
            <button 
                onClick={() => {
                const tg = window.Telegram?.WebApp;
                const msg = `Sell 1 x ${selectedChar.name} for Zenith ⧫?`;
                
                const callback = async (confirmed) => {
                    if (!confirmed) return;
                    try {
                        await apiFetch('/recycle', { 
                            method: 'POST', 
                            body: JSON.stringify([selectedChar.id]) 
                        });
                        addToast('Character sold', 'success');
                        setSelectedChar(null);
                        window.dispatchEvent(new CustomEvent('user-data-refresh'));
                    } catch (err) {
                        addToast(err.message || 'Fusion failed', 'error');
                    }
                };

                if (tg?.showConfirm) {
                    tg.showConfirm(msg, callback);
                } else if (window.confirm(msg)) {
                    callback(true);
                }
                }}
                className="w-full py-3.5 rounded-xl bg-brand-accent/10 border border-brand-accent/20 text-brand-accent text-[10px] font-black uppercase tracking-widest hover:bg-brand-accent/20 transition-all flex items-center justify-center space-x-2 mb-4"
            >
                <Zap size={14} />
                <span>Sell Duplicate</span>
            </button>
        );
    } else if (activeTab === 'shop' && selectedChar && !selectedChar.owned) {
        actions = (
            <div className="w-full space-y-4">
                <AnimatePresence mode="wait">
                {purchaseStage === 'idle' ? (
                    <motion.div 
                    key="idle" 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex items-center justify-between p-5 bg-brand-neon/5 border border-brand-neon/20 rounded-[2.5rem]"
                    >
                        <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-full bg-brand-neon/20 flex items-center justify-center text-brand-neon shadow-lg shadow-brand-neon/20">
                            <Zap size={20} />
                        </div>
                        <div>
                            <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest">Price</p>
                            <p className="text-sm font-black text-white">⧫ {formatNumber(selectedChar.zenith_price || 5)}</p>
                        </div>
                        </div>
                        <button 
                        onClick={() => {
                            window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                            setPurchaseStage('confirm');
                        }}
                        className="px-8 py-3 rounded-2xl bg-brand-neon text-brand-midnight text-[10px] font-black uppercase tracking-[0.2em] shadow-xl shadow-brand-neon/30 active:scale-95 transition-all"
                        >
                        BUY
                        </button>
                    </motion.div>
                ) : purchaseStage === 'confirm' || purchaseStage === 'buying' ? (
                    <motion.div 
                    key="confirm"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="p-6 glass-panel rounded-[2.5rem] border border-brand-accent/30 bg-brand-accent/[0.02]"
                    >
                    <div className="text-center mb-5">
                        <p className="text-brand-accent font-black uppercase text-[10px] tracking-widest mb-1">Confirm Purchase?</p>
                        <p className="text-slate-500 text-[9px] uppercase font-bold">Zenith Balance: ⧫ {formatNumber(user?.stats?.zenith)}</p>
                    </div>
                    
                    <div className="flex space-x-3">
                        <button 
                            onClick={() => setPurchaseStage('idle')}
                            disabled={purchaseStage === 'buying'}
                            className="flex-1 py-3.5 rounded-xl border border-white/10 text-slate-500 text-[10px] font-black uppercase tracking-widest active:scale-95 transition-all"
                        >
                            CANCEL
                        </button>
                        <button 
                            onClick={async () => {
                                setPurchaseStage('buying');
                                try {
                                    const res = await apiFetch(`/shop/buy/character/${selectedChar.id}`, { method: 'POST' });
                                    if (res.status === 'success') {
                                        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
                                        addToast('Character added to harem', 'success');
                                        setSelectedChar(null);
                                        // Trigger refresh events
                                        window.dispatchEvent(new CustomEvent('user-data-refresh'));
                                        window.dispatchEvent(new CustomEvent('shop-data-refresh'));
                                    }
                                } catch (err) {
                                    addToast(err.message || 'Transaction failed', 'error');
                                    setPurchaseStage('confirm');
                                }
                            }}
                            disabled={purchaseStage === 'buying'}
                            className="flex-[1.5] py-3.5 rounded-xl bg-brand-accent text-white text-[10px] font-black uppercase tracking-widest shadow-lg shadow-brand-accent/20 active:scale-95 transition-all flex items-center justify-center"
                        >
                            {purchaseStage === 'buying' ? (
                            <Loader2 size={16} className="animate-spin" />
                            ) : (
                            'CONFIRM PURCHASE'
                            )}
                        </button>
                    </div>
                    </motion.div>
                ) : null}
                </AnimatePresence>
            </div>
        );
    }

    return (
        <Modal
            character={selectedChar}
            onClose={() => setSelectedChar(null)}
            actions={actions}
        />
    );
};
