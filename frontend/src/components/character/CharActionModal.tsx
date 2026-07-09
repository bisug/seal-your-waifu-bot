import { useState, useEffect } from 'react';
import { Coins, Gem, Image as ImageIcon, Loader2, Lock, Pencil, Save, Trash2, X, Heart, Sparkles } from 'lucide-react';
import { useToast } from '../ui/Toast';
import { Modal } from './Modal';
import { apiFetch, getErrorMessage } from '../../api/client';
import { useUser, type Character, type User } from '../../context/UserContext';
import { formatNumber } from '../../utils';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';

interface CharActionModalProps {
    selectedChar: Character | null;
    setSelectedChar: (char: Character | null) => void;
    activeTab: string;
    user: User | null;
    onPurchaseSuccess?: (char: Character) => void;
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

const buildEditForm = (character: Character | null): CharacterEditForm => ({
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

    const isOwned = (user?.characters || []).some((c: Character) => String(c.id) === String(selectedChar.id));
    const zenithBalance = Number(user?.stats.zenith ?? user?.zenith ?? 0);
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
            addToast(result?.message || 'Waifu entry updated.', result?.status === 'unchanged' ? 'info' : 'success');
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
                `RECYCLE ${selectedChar.name.toUpperCase()} FOR ${preview.reward} ZENITH?`,
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
            window.Telegram?.WebApp?.showConfirm(
                `SELL ${selectedChar.name.toUpperCase()} FOR SHARDS?`,
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
        <div className="w-full space-y-4">
            {canEdit && (
                <div className="w-full">
                    {editMode ? (
                        <form
                            onSubmit={(event) => {
                                event.preventDefault();
                                handleEditSave();
                            }}
                            className="space-y-4 rounded-xl border border-white/[0.05] bg-white/[0.01] p-5"
                        >
                            <div className="space-y-4">
                                <div className="space-y-1.5">
                                    <span className="text-[10px] font-black uppercase text-neutral-600 tracking-widest pl-1">Waifu Name</span>
                                    <Input
                                        value={editForm.name}
                                        onChange={event => updateEditField('name', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        placeholder="NAME..."
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <span className="text-[10px] font-black uppercase text-neutral-600 tracking-widest pl-1">Origin Anime</span>
                                    <Input
                                        value={editForm.anime}
                                        onChange={event => updateEditField('anime', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        placeholder="ANIME..."
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <span className="text-[10px] font-black uppercase text-neutral-600 tracking-widest pl-1">Rarity Class</span>
                                    <div className="relative group">
                                        <select
                                            value={editForm.rarity}
                                            onChange={event => updateEditField('rarity', event.target.value)}
                                            disabled={editStage === 'saving'}
                                            className="w-full h-11 bg-brand-deep border border-white/10 rounded-md px-4 text-xs font-black text-white uppercase tracking-widest outline-none focus:border-brand-accent transition-all appearance-none cursor-pointer"
                                        >
                                            {!rarityOptions.some(option => option.label === editForm.rarity) && editForm.rarity && (
                                                <option value={editForm.rarity}>{editForm.rarity.toUpperCase()}</option>
                                            )}
                                            {rarityOptions.map(option => (
                                                <option key={option.value} value={option.label}>
                                                    {option.label.toUpperCase()}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <div className="space-y-1.5">
                                    <span className="text-[10px] font-black uppercase text-neutral-600 tracking-widest pl-1">Visual Asset</span>
                                    <Input
                                        icon={ImageIcon}
                                        value={editForm.img_url}
                                        onChange={event => updateEditField('img_url', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        placeholder="URL..."
                                    />
                                </div>
                            </div>

                            <div className="flex gap-3 pt-2">
                                <Button
                                    variant="secondary"
                                    onClick={() => {
                                        setEditForm(buildEditForm(selectedChar));
                                        setEditMode(false);
                                    }}
                                    disabled={editStage === 'saving'}
                                    className="flex-1 rounded-md uppercase tracking-widest text-[10px] font-black"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    type="submit"
                                    variant="tactical"
                                    isLoading={editStage === 'saving'}
                                    className="flex-[1.5] rounded-md uppercase tracking-widest text-[10px] font-black"
                                >
                                    Update Entry
                                </Button>
                            </div>
                        </form>
                    ) : (
                        <Button
                            variant="secondary"
                            onClick={() => setEditMode(true)}
                            className="w-full rounded-md uppercase tracking-widest text-[10px] font-black border-white/5 py-4"
                        >
                            <Pencil size={14} className="mr-2" />
                            Update Archive Registry
                        </Button>
                    )}
                </div>
            )}

            {!editMode && activeTab === 'shop' && !isOwned && (
                <div className="w-full">
                    {isSoldOut ? (
                        <Badge variant="danger" icon={Lock} size="md" className="w-full py-4 rounded-md justify-center font-black tracking-widest border-none">
                            SUMMONS DEPLETED
                        </Badge>
                    ) : !canAfford ? (
                        <Badge variant="secondary" icon={Gem} size="md" className="w-full py-4 rounded-md justify-center font-black tracking-widest border-white/5">
                            {formatNumber(price - zenithBalance)} ZENITH NEEDED
                        </Badge>
                    ) : purchaseStage === 'idle' ? (
                        <Button
                            onClick={() => setPurchaseStage('confirm')}
                            variant="tactical"
                            className="w-full py-5 rounded-md uppercase tracking-[0.2em] text-[11px] font-black"
                        >
                            Summon for {formatNumber(price)} Zenith
                        </Button>
                    ) : (
                        <div className="flex gap-3">
                            <Button
                                variant="secondary"
                                onClick={() => setPurchaseStage('idle')}
                                className="flex-1 rounded-md uppercase tracking-widest text-[10px] font-black"
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="tactical"
                                onClick={handleBuy}
                                isLoading={purchaseStage === 'buying'}
                                className="flex-[2] rounded-md uppercase tracking-widest text-[10px] font-black"
                            >
                                Confirm Summon
                            </Button>
                        </div>
                    )}
                </div>
            )}

            {!editMode && isOwned && (
                <div className="flex gap-3">
                    <Button
                        variant="danger"
                        onClick={handleRecycle}
                        disabled={sellStage !== 'idle'}
                        className="flex-1 rounded-md uppercase tracking-widest text-[10px] font-black py-4"
                    >
                        {sellStage === 'previewing' || sellStage === 'selling' ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} className="mr-2" />}
                        Recycle
                    </Button>

                    <Button
                        variant="secondary"
                        onClick={handleSell}
                        disabled={sellStage !== 'idle'}
                        className="flex-1 rounded-md uppercase tracking-widest text-[10px] font-black py-4"
                    >
                        {sellStage === 'selling' ? <Loader2 size={14} className="animate-spin" /> : <Coins size={14} className="mr-2" />}
                        Sell
                    </Button>
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
