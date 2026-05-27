import React from 'react';
import { useUser, Pet } from '../context/UserContext';
import { Sparkles, Timer, Zap } from 'lucide-react';

interface HatcheryProps {
    onPetClick?: (pet: Pet) => void;
}

export const Hatchery = ({ onPetClick }: HatcheryProps) => {
    const { user } = useUser();

    return (
        <div className="px-6 py-10 space-y-12">
            <header>
                <h1 className="text-3xl font-black italic uppercase tracking-tighter text-white">Incubation Chamber</h1>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.4em] mt-1">Hatch eggs to find new companions</p>
            </header>

            <section>
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Active Eggs</h2>
                    <span className="bg-white/5 border border-white/10 px-3 py-1 rounded-full text-[9px] font-black text-white">{user?.eggs?.length || 0}/3 Slots</span>
                </div>

                <div className="space-y-4">
                    {user?.eggs && user.eggs.length > 0 ? user.eggs.map((egg, i) => (
                        <div key={i} className="glass-panel p-6 rounded-[2.5rem] border border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-6">
                                <div className="w-16 h-16 bg-brand-accent/5 rounded-3xl flex items-center justify-center border border-brand-accent/10">
                                    <Sparkles className="text-brand-accent" size={24} />
                                </div>
                                <div>
                                    <p className="text-white font-black uppercase italic tracking-tighter text-lg">{egg.type} Egg</p>
                                    <div className="flex items-center gap-2 mt-1">
                                        <Timer size={12} className="text-slate-600" />
                                        <span className="text-[10px] font-bold text-slate-500 font-mono">00:44:21</span>
                                    </div>
                                </div>
                            </div>
                            <button className="bg-brand-accent text-brand-midnight text-[9px] font-black px-6 py-3 rounded-2xl uppercase tracking-widest opacity-40">Incubating</button>
                        </div>
                    )) : (
                        <div className="glass-panel p-10 rounded-[2.5rem] border border-white/5 text-center flex flex-col items-center">
                            <Zap size={32} className="text-slate-800 mb-4" />
                            <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest leading-relaxed">
                                No active incubations detected.<br/>Acquire eggs from the matrix.
                            </p>
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
};
