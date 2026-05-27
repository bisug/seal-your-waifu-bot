import React from 'react';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { Skeleton } from '../components/ui/Skeleton';
import { apiFetch } from '../api/client';
import { ArrowRightLeft, User, Shield } from 'lucide-react';

export const Trade = () => {
    const { data: trades, loading } = useApi('/trade/offers');
    const { addToast } = useToast();

    if (loading) return (
        <div className="px-6 pb-12 pt-4 space-y-4">
            <Skeleton className="h-40 rounded-3xl" />
        </div>
    );

    return (
        <div className="px-6 pb-12 pt-4">
            <div className="flex items-center space-x-3 mb-8">
                <ArrowRightLeft className="text-brand-accent" size={24} />
                <h1 className="text-2xl font-black uppercase tracking-tighter italic">Trade Desk</h1>
            </div>

            <div className="glass-panel p-8 rounded-[3rem] border border-white/5 text-center flex flex-col items-center">
                 <Shield size={48} className="text-slate-800 mb-6" />
                 <h2 className="text-lg font-black text-white uppercase tracking-widest mb-2">No Active Offers</h2>
                 <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-relaxed">
                     When you initiate or receive a trade offer,<br/>it will materialize here.
                 </p>
            </div>
        </div>
    );
};
