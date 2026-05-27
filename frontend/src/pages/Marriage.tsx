import React from 'react';
import { useApi } from '../hooks/useApi';
import { Skeleton } from '../components/ui/Skeleton';
import { Heart, Users } from 'lucide-react';

export const Marriage = () => {
    const { data: partners, loading } = useApi('/marriage/partners');

    if (loading) return (
        <div className="px-6 py-12 space-y-4">
            <Skeleton className="h-40 rounded-3xl" />
            <Skeleton className="h-40 rounded-3xl" />
        </div>
    );

    return (
        <div className="px-6 py-12">
            <div className="flex items-center space-x-3 mb-8">
                <Heart className="text-red-500 fill-red-500" size={24} />
                <h1 className="text-2xl font-black uppercase tracking-tighter italic">Social Status</h1>
            </div>

            <div className="glass-panel p-8 rounded-[3rem] border border-white/5 text-center flex flex-col items-center">
                 <Users size={48} className="text-slate-800 mb-6" />
                 <h2 className="text-lg font-black text-white uppercase tracking-widest mb-2">No Bonds Established</h2>
                 <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-relaxed">
                     You are not currently married to any collectors.
                 </p>
            </div>
        </div>
    );
};
