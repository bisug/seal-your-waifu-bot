import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Loader2 } from 'lucide-react';
import { Modal, useToast } from './UI';
import { apiFetch } from '../api';
import { formatNumber } from '../utils';

export const CharActionModal = ({ selectedChar, setSelectedChar, activeTab, user }) => {
    const { addToast } = useToast();
    const [purchaseStage, setPurchaseStage] = useState('idle');
    const [sellStage, setSellStage] = useState('idle'); // 'idle', 'confirm_single', 'confirm_bulk', 'selling'

    useEffect(() => {
        if (!selectedChar) {
            setPurchaseStage('idle');
            setSellStage('idle');
        }
    }, [selectedChar]);

    let actions = null;

    if (activeTab === 'profile' && selectedChar?.count > 1) {
        actions = (
            <div className="w-full space-y-4">
                <AnimatePresence mode="wait">
                {sellStage === 'idle' ? (
                    <motion.div 
                        key="idle"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="flex items-center space-x-2"
                    >
                        <button 
                            onClick={() => setSellStage('confirm_single')}
                            className="flex-1 py-3.5 rounded-xl bg-brand-accent/10 border border-brand-accent/20 text-brand-accent text-[10px] font-black uppercase tracking-widest hover:bg-brand-accent/20 transition-all flex items-center justify-center space-x-2"
                        >
                            <Activity size={16} />
                            <span>Sell One (⧫)</span>
                        </button>
                        {selectedChar.count > 2 && (
                            <button 
                                onClick={() => setSellStage('confirm_bulk')}
                                className="flex-1 py-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-500 text-[10px] font-black uppercase tracking-widest hover:bg-purple-500/20 transition-all flex items-center justify-center space-x-2"
                            >
                                <Activity size={16} />
                                <span>Sell All x{selectedChar.count - 1}</span>
                            </button>
                        )}
                    </motion.div>
                ) : (
                    <motion.div 
                        key="confirm"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="p-6 glass-panel rounded-[2rem] border border-brand-accent/30 bg-brand-accent/[0.02] mb-4"
                    >
                        <div className="text-center mb-5">
                            <p className="text-brand-accent font-black uppercase text-[10px] tracking-widest mb-1">
                                {sellStage === 'confirm_bulk' ? `Sell ${selectedChar.count - 1} Duplicates?` : "Sell 1 Duplicate?"}
                            </p>
                            <p className="text-slate-500 text-[9px] uppercase font-bold">This action cannot be undone.</p>
                        </div>
                        <div className="flex space-x-3">
                            <button 
                                onClick={() => setSellStage('idle')}
                                disabled={sellStage === 'selling'}
                                className="flex-1 py-3.5 rounded-xl border border-white/10 text-slate-500 text-[10px] font-black uppercase tracking-widest active:scale-95 transition-all"
                            >
                                CANCEL
                            </button>
                            <button 
                                onClick={async () => {
                                    setSellStage('selling');
                                    const amountToSell = sellStage === 'confirm_bulk' ? selectedChar.count - 1 : 1;
                                    const charIds = Array(amountToSell).fill(selectedChar.id);
                                    
                                    try {
                                        await apiFetch('/recycle', { 
                                            method: 'POST', 
                                            body: JSON.stringify(charIds) 
                                        });
                                        window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
                                        addToast(`Sold ${amountToSell} character${amountToSell > 1 ? 's' : ''}`, 'success');
                                        setSelectedChar(null);
                                        window.dispatchEvent(new CustomEvent('user-data-refresh'));
                                    } catch (err) {
                                        addToast(err.message || 'Sell failed', 'error');
                                        setSellStage('idle');
                                    }
                                }}
                                disabled={sellStage === 'selling'}
                                className="flex-[1.5] py-3.5 rounded-xl bg-brand-accent text-white text-[10px] font-black uppercase tracking-widest shadow-lg shadow-brand-accent/20 active:scale-95 transition-all flex items-center justify-center"
                            >
                                {sellStage === 'selling' ? <Loader2 size={16} className="animate-spin" /> : 'CONFIRM SELL'}
                            </button>
                        </div>
                    </motion.div>
                )}
                </AnimatePresence>
            </div>
        );
    } else if (activeTab === 'market' && selectedChar && !selectedChar.owned) {
        actions = (
            <div className="w-full space-y-4">
                <AnimatePresence mode="wait">
                {purchaseStage === 'idle' ? (
                    <motion.div 
                    key="idle" 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="flex items-center justify-between p-6 bg-brand-neon/5 border border-brand-neon/20 rounded-[3rem]"
                    >
                        <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-full bg-brand-neon/20 flex items-center justify-center text-brand-neon shadow-lg shadow-brand-neon/20">
                            <Activity size={20} />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Price</p>
                            <p className="text-xl font-black text-white">⧫ {formatNumber(selectedChar.zenith_price || 5)}</p>
                        </div>
                        </div>
                        <button 
                        onClick={() => {
                            window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                            setPurchaseStage('confirm');
                        }}
                        className="px-10 py-4 rounded-2xl bg-brand-neon text-brand-midnight text-[11px] font-black uppercase tracking-[0.25em] shadow-2xl shadow-brand-neon/40 active:scale-95 transition-all"
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
