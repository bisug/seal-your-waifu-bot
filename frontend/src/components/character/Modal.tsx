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
            document.body.style.overflow = 'hidden';
            return () => { document.body.style.overflow = 'unset'; };
        }
    }, [character]);

    if (!character) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="absolute inset-0" onClick={onClose} />

            <div className="relative w-full max-w-sm max-h-[90vh] bg-brand-midnight rounded-2xl flex flex-col overflow-hidden shadow-2xl border border-white/10">
                {/* Header */}
                <div className="flex items-start justify-between p-4 border-b border-white/5">
                    <div className="flex flex-col pr-4">
                        <span className="text-xs font-semibold text-brand-accent mb-0.5">{character.rarity}</span>
                        <h2 className="text-lg font-bold text-white line-clamp-1">{character.name}</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 -mr-2 rounded-lg text-neutral-400 hover:text-white hover:bg-white/5 transition-colors shrink-0"
                        aria-label="Close Modal"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto no-scrollbar">
                    {/* Image Section */}
                    <div className="relative w-full aspect-square bg-brand-deep flex items-center justify-center p-6 border-b border-white/5">
                        <img
                            src={character.img_url}
                            className="w-full h-full object-contain drop-shadow-2xl"
                            alt={character.name}
                        />
                    </div>

                    {/* Details Area */}
                    <div className="p-5 space-y-5">
                        <div>
                            <span className="text-xs font-semibold text-neutral-500 block mb-1">Origin</span>
                            <p className="text-sm font-medium text-neutral-200">{character.anime}</p>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-brand-deep p-3 rounded-xl border border-white/5 flex flex-col">
                                <span className="text-xs font-semibold text-neutral-500 mb-1">Status</span>
                                <span className={cn("text-sm font-bold", character.owned ? "text-emerald-500" : "text-neutral-400")}>
                                    {character.owned ? "Owned" : "Locked"}
                                </span>
                            </div>
                            <div className="bg-brand-deep p-3 rounded-xl border border-white/5 flex flex-col">
                                <span className="text-xs font-semibold text-neutral-500 mb-1">Stock</span>
                                <span className="text-sm font-bold text-white">{character.count > 0 ? `x${character.count}` : "None"}</span>
                            </div>
                        </div>

                        {actions && <div className="pt-2">{actions}</div>}
                    </div>
                </div>
            </div>
        </div>
    );
};
