import React, { useState, useEffect } from 'react';
import { Coins, Gem, Image as ImageIcon, Loader2, Lock, Pencil, Save, Trash2, X } from 'lucide-react';
import { useToast } from '../ui/Toast';
import { Modal } from './Modal';
import { apiFetch, getErrorMessage } from '../../api/client';
import { useUser } from '../../context/UserContext';
import { formatNumber } from '../../utils';

interface CharActionModalProps {
    selectedChar: any;
    setSelectedChar: (char: any) => void;
    activeTab: string;
    user: any;
    onPurchaseSuccess?: (char: any) => void;
}

interface RarityOption {
    value: number;
    label: string;
}

interface CharacterEditForm {
    name: string;
    anime: string;
    rarity: string;
    img_url: string;
}

const buildEditForm = (character: any): CharacterEditForm => ({
    name: character?.name || '',
    anime: character?.anime || '',
    rarity: character?.rarity || '',
    img_url: character?.img_url || '',
});

export const CharActionModal = ({ selectedChar, setSelectedChar, activeTab, user, onPurchaseSuccess }: CharActionModalProps) => {
    const { addToast } = useToast();
    const { triggerRefresh } = useUser();
    const [purchaseStage, setPurchaseStage] = useState('idle');
    const [sellStage, setSellStage] = useState('idle');
    const [editMode, setEditMode] = useState(false);
    const [editStage, setEditStage] = useState<'idle' | 'saving'>('idle');
    const [editForm, setEditForm] = useState<CharacterEditForm>(() => buildEditForm(selectedChar));
    const [rarityOptions, setRarityOptions] = useState<RarityOption[]>([]);
    const canEdit = Boolean(user?.can_edit_character ?? user?.is_sudo);
    const selectedCharId = selectedChar?.id;

    useEffect(() => {
        setPurchaseStage('idle');
        setSellStage('idle');
        setEditStage('idle');
        setEditMode(false);
        setEditForm(buildEditForm(selectedChar));
    }, [selectedCharId, selectedChar]);

    useEffect(() => {
        if (!canEdit || rarityOptions.length > 0) return;

        let cancelled = false;
        apiFetch('/admin/upload/options')
            .then((data) => {
                if (!cancelled) setRarityOptions(data?.character_rarities || []);
            })
            .catch((err) => console.warn('Could not load rarity options:', err));

        return () => {
            cancelled = true;
        };
    }, [canEdit, rarityOptions.length]);

    if (!selectedChar) return null;

    const isOwned = (user?.characters || []).some(c => String(c.id) === String(selectedChar.id));
    const zenithBalance = Number(user?.stats?.zenith ?? user?.zenith ?? 0);
    const price = Number(selectedChar.zenith_price || 0);
    const stockRemaining = typeof selectedChar.stock_remaining === 'number'
        ? selectedChar.stock_remaining
        : typeof selectedChar.stock_limit === 'number' && typeof selectedChar.sold_count === 'number'
            ? Math.max(0, selectedChar.stock_limit - selectedChar.sold_count)
            : null;
    const isSoldOut = Boolean(selectedChar.sold_out) || (stockRemaining !== null && stockRemaining <= 0);
    const canAfford = zenithBalance >= price;

    const updateEditField = (field: keyof CharacterEditForm, value: string) => {
        setEditForm(prev => ({ ...prev, [field]: value }));
    };

    const handleEditSave = async () => {
        if (editStage !== 'idle') return;

        const payload = {
            name: editForm.name.trim(),
            anime: editForm.anime.trim(),
            rarity: editForm.rarity.trim(),
            img_url: editForm.img_url.trim(),
        };

        if (!payload.name || !payload.anime || !payload.rarity || !payload.img_url) {
            addToast('Fill in all character fields.', 'error');
            return;
        }

        setEditStage('saving');
        try {
            const result = await apiFetch(`/admin/character/${selectedChar.id}`, {
                method: 'PATCH',
                body: JSON.stringify(payload),
            });
            const updatedChar = {
                ...selectedChar,
                ...(result?.character || payload),
                id: selectedChar.id,
            };

            setSelectedChar(updatedChar);
            setEditForm(buildEditForm(updatedChar));
            setEditMode(false);
            addToast(result?.message || 'Character updated.', result?.status === 'unchanged' ? 'info' : 'success');
            triggerRefresh();
            window.dispatchEvent(new Event('gallery-refresh'));
            window.dispatchEvent(new Event('harem-refresh'));
            window.dispatchEvent(new Event('shop-refresh'));
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
        } finally {
            setEditStage('idle');
        }
    };

    const handleBuy = async () => {
        setPurchaseStage('buying');
        try {
            await apiFetch(`/shop/buy/character/${selectedChar.id}`, { method: 'POST' });
            triggerRefresh();
            window.dispatchEvent(new Event('shop-refresh'));
            setSelectedChar(null);
            if (onPurchaseSuccess) onPurchaseSuccess(selectedChar);
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
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
                        addToast(getErrorMessage(err), 'error');
                        setSellStage('idle');
                    }
                }
            );
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
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
                        addToast(getErrorMessage(err), 'error');
                        setSellStage('idle');
                    }
                }
            );
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
            setSellStage('idle');
        }
    };

    const actions = (
        <div className="w-full space-y-3">
            {canEdit && (
                <div className="w-full">
                    {editMode ? (
                        <form
                            onSubmit={(event) => {
                                event.preventDefault();
                                handleEditSave();
                            }}
                            className="space-y-3 rounded-lg border border-white/10 bg-white/[0.03] p-3"
                        >
                            <div className="grid grid-cols-1 gap-3">
                                <label>
                                    <span className="text-[10px] font-bold uppercase text-neutral-500">Name</span>
                                    <input
                                        value={editForm.name}
                                        onChange={event => updateEditField('name', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        className="mt-1.5 h-10 w-full rounded-lg border border-white/10 bg-brand-deep px-3 text-sm font-medium text-white outline-none focus:border-brand-accent disabled:opacity-60"
                                    />
                                </label>
                                <label>
                                    <span className="text-[10px] font-bold uppercase text-neutral-500">Anime</span>
                                    <input
                                        value={editForm.anime}
                                        onChange={event => updateEditField('anime', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        className="mt-1.5 h-10 w-full rounded-lg border border-white/10 bg-brand-deep px-3 text-sm font-medium text-white outline-none focus:border-brand-accent disabled:opacity-60"
                                    />
                                </label>
                                <label>
                                    <span className="text-[10px] font-bold uppercase text-neutral-500">Rarity</span>
                                    {rarityOptions.length > 0 ? (
                                        <select
                                            value={editForm.rarity}
                                            onChange={event => updateEditField('rarity', event.target.value)}
                                            disabled={editStage === 'saving'}
                                            className="mt-1.5 h-10 w-full rounded-lg border border-white/10 bg-brand-deep px-3 text-sm font-medium text-white outline-none focus:border-brand-accent disabled:opacity-60"
                                        >
                                            {!rarityOptions.some(option => option.label === editForm.rarity) && editForm.rarity && (
                                                <option value={editForm.rarity}>{editForm.rarity}</option>
                                            )}
                                            {rarityOptions.map(option => (
                                                <option key={option.value} value={option.label}>
                                                    {option.value}. {option.label}
                                                </option>
                                            ))}
                                        </select>
                                    ) : (
                                        <input
                                            value={editForm.rarity}
                                            onChange={event => updateEditField('rarity', event.target.value)}
                                            disabled={editStage === 'saving'}
                                            className="mt-1.5 h-10 w-full rounded-lg border border-white/10 bg-brand-deep px-3 text-sm font-medium text-white outline-none focus:border-brand-accent disabled:opacity-60"
                                        />
                                    )}
                                </label>
                                <label>
                                    <span className="text-[10px] font-bold uppercase text-neutral-500">Image URL</span>
                                    <div className="mt-1.5 flex items-center gap-2 rounded-lg border border-white/10 bg-brand-deep px-3 focus-within:border-brand-accent">
                                        <ImageIcon size={15} className="shrink-0 text-neutral-500" />
                                        <input
                                            value={editForm.img_url}
                                            onChange={event => updateEditField('img_url', event.target.value)}
                                            disabled={editStage === 'saving'}
                                            className="h-10 min-w-0 flex-1 bg-transparent text-sm font-medium text-white outline-none disabled:opacity-60"
                                        />
                                    </div>
                                </label>
                            </div>

                            <div className="flex gap-2">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setEditForm(buildEditForm(selectedChar));
                                        setEditMode(false);
                                    }}
                                    disabled={editStage === 'saving'}
                                    className="flex-1 rounded-lg bg-white/5 py-3 text-sm font-semibold text-neutral-300 transition-colors hover:bg-white/10 disabled:opacity-60"
                                >
                                    <span className="flex items-center justify-center gap-2">
                                        <X size={16} />
                                        Cancel
                                    </span>
                                </button>
                                <button
                                    type="submit"
                                    disabled={editStage === 'saving'}
                                    className="flex-[1.5] rounded-lg bg-brand-accent py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-accent-secondary disabled:pointer-events-none disabled:opacity-60"
                                >
                                    <span className="flex items-center justify-center gap-2">
                                        {editStage === 'saving' ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                                        Save
                                    </span>
                                </button>
                            </div>
                        </form>
                    ) : (
                        <button
                            onClick={() => setEditMode(true)}
                            className="w-full rounded-lg border border-brand-accent/20 bg-brand-accent/10 py-3 text-sm font-semibold text-brand-accent transition-all hover:bg-brand-accent/20 active:scale-[0.98] flex items-center justify-center gap-2"
                        >
                            <Pencil size={16} />
                            <span>Edit info</span>
                        </button>
                    )}
                </div>
            )}

            {!editMode && activeTab === 'shop' && !isOwned && (
                <div className="w-full">
                    {isSoldOut ? (
                        <div className="w-full rounded-lg border border-red-500/15 bg-red-500/10 px-3 py-3 text-sm font-semibold text-red-300 flex items-center justify-center gap-2">
                            <Lock size={16} />
                            <span>Sold out for this rotation</span>
                        </div>
                    ) : !canAfford ? (
                        <div className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-3 text-sm font-semibold text-neutral-300 flex items-center justify-center gap-2">
                            <Gem size={16} className="text-brand-accent" />
                            <span>{formatNumber(price - zenithBalance)} more Zenith needed</span>
                        </div>
                    ) : purchaseStage === 'idle' ? (
                        <button
                            onClick={() => setPurchaseStage('confirm')}
                            className="w-full py-3 rounded-lg bg-brand-accent text-white font-semibold text-sm hover:bg-brand-accent-secondary active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                        >
                            <span>Buy for {formatNumber(price)}</span>
                            <Gem size={16} />
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
                                {purchaseStage === 'buying' ? <Loader2 size={16} className="animate-spin" /> : 'Confirm purchase'}
                            </button>
                        </div>
                    )}
                </div>
            )}

            {!editMode && isOwned && (
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
                        {sellStage === 'selling' ? <Loader2 size={16} className="animate-spin" /> : <Coins size={16} />}
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
