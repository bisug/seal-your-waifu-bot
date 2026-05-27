import React, { useEffect, ReactNode } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../utils';
import { Character } from '../../context/UserContext';

interface ModalProps {
    character: Character | null;
    onClose: () => void;
    actions?: ReactNode;
}

export const Modal = ({ character, onClose, actions }: ModalProps) => {
    useEffect(() => {
        if (character) {
            document.body.classList.add('no-scroll');
            return () => document.body.classList.remove('no-scroll');
        }
    }, [character]);

    if (!character) return null;

    return (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-brand-midnight/90">
                <div className="absolute inset-0" onClick={onClose} />

                <div className="relative w-full h-full bg-brand-midnight flex flex-col overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
                        <div className="flex flex-col">
                            <span className="text-[10px] font-bold text-brand-accent uppercase tracking-widest">{character.rarity}</span>
                            <h2 className="text-lg font-bold text-white truncate max-w-[200px]">{character.name}</h2>
                        </div>
                        <button
                            onClick={onClose}
                            className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-slate-400 active:scale-95 transition-all"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto no-scrollbar">
                        {/* Image Section */}
                        <div className="relative w-full bg-slate-900/30 flex items-center justify-center" style={{ height: '40vh' }}>
                            <img 
                                src={character.img_url} 
                                className="h-full w-full object-contain p-4"
                                alt={character.name} 
                            />
                        </div>

                        {/* Details Area */}
                        <div className="p-6 space-y-6">
                            <div>
                                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-[0.2em] block mb-1">Origin</span>
                                <p className="text-sm font-medium text-slate-300">{character.anime}</p>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div className="bg-white/5 p-3 rounded-xl border border-white/5">
                                    <span className="text-[8px] font-bold text-slate-500 uppercase tracking-widest block mb-1">Status</span>
                                    <span className={cn("text-[10px] font-bold", character.owned ? "text-brand-accent" : "text-slate-400")}>
                                        {character.owned ? "OWNED" : "LOCKED"}
                                    </span>
                                </div>
                                <div className="bg-white/5 p-3 rounded-xl border border-white/5">
                                    <span className="text-[8px] font-bold text-slate-500 uppercase tracking-widest block mb-1">Stock</span>
                                    <span className="text-[10px] font-bold text-white">{character.count > 0 ? `x${character.count}` : "None"}</span>
                                </div>
                            </div>

                            {actions && <div className="pt-4">{actions}</div>}
                        </div>
                    </div>
                </div>
            </div>
    );
};
