import { useState, useEffect } from 'react';
import { Coins, Gem, Image as ImageIcon, Loader2, Lock, Pencil, Save, Trash2, X, Heart, Sparkles, Target, History } from 'lucide-react';
import { useToast } from '../ui/Toast';
import { Modal } from './Modal';
import { apiFetch, getErrorMessage } from '../../api/client';
import { useUser, type Character, type User } from '../../context/UserContext';
import { formatNumber, cn } from '../../utils';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';
import { motion, AnimatePresence } from 'framer-motion';

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
            .catch((err) => console.warn('Registry error: Could not load rarity classification:', err));

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
            addToast('Input required: Complete all asset fields.', 'error');
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
            addToast(result?.message || 'Archive registry updated successfully.', result?.status === 'unchanged' ? 'info' : 'success');
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
                `AUTHORIZE RECYCLE: ${selectedChar.name.toUpperCase()} FOR ${preview.reward} ZENITH?`,
                async (confirmed) => {
                    if (!confirmed) {
                        setSellStage('idle');
                        return;
                    }

                    setSellStage('selling');
                    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                    try {
                        const res = await apiFetch('/recycle', {
                            method: 'POST',
                            body: JSON.stringify([selectedChar.id])
                        });
                        addToast(`Asset recycled. +${res.reward} Zenith assets secured.`, 'success');
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
                `AUTHORIZE LIQUIDATION: ${selectedChar.name.toUpperCase()} FOR SHARDS?`,
                async (confirmed) => {
                    if (!confirmed) {
                        setSellStage('idle');
                        return;
                    }

                    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');
                    try {
                        const res = await apiFetch(`/character/sell/${selectedChar.id}`, { method: 'POST' });
                        addToast(`Asset liquidated. +${res.reward} Shards secured.`, 'success');
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
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-5 p-6 rounded-[24px] border border-white/[0.04] bg-white/[0.01] shadow-inner">
                            <div className="space-y-4">
                                <div className="space-y-2">
                                    <span className="text-[10px] font-black uppercase text-neutral-600 tracking-[0.2em] pl-1">ASSET_NAME</span>
                                    <Input
                                        value={editForm.name}
                                        onChange={event => updateEditField('name', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        placeholder="DESIGNATION..."
                                    />
                                </div>
                                <div className="space-y-2">
                                    <span className="text-[10px] font-black uppercase text-neutral-600 tracking-[0.2em] pl-1">DATA_SOURCE</span>
                                    <Input
                                        value={editForm.anime}
                                        onChange={event => updateEditField('anime', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        placeholder="ORIGIN..."
                                    />
                                </div>
                                <div className="space-y-2">
                                    <span className="text-[10px] font-black uppercase text-neutral-600 tracking-[0.2em] pl-1">RARITY_CLASS</span>
                                    <div className="relative group">
                                        <select
                                            value={editForm.rarity}
                                            onChange={event => updateEditField('rarity', event.target.value)}
                                            disabled={editStage === 'saving'}
                                            className="w-full h-12 bg-[#0a0a0c] border border-white/10 rounded-xl px-4 text-xs font-black text-white uppercase tracking-widest outline-none focus:border-brand-accent transition-all appearance-none cursor-pointer"
                                        >
                                            {!rarityOptions.some(option => option.label === editForm.rarity) && editForm.rarity && (
                                                <option value={editForm.rarity}>{editForm.rarity.toUpperCase()}</option>
                                            )}
                                            {rarityOptions.map(option => (
                                                <option key={option.value} value={option.label}>
                                                    CLASS_{option.value}: {option.label.toUpperCase()}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <span className="text-[10px] font-black uppercase text-neutral-600 tracking-[0.2em] pl-1">VISUAL_MANIFEST</span>
                                    <Input
                                        icon={ImageIcon}
                                        value={editForm.img_url}
                                        onChange={event => updateEditField('img_url', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        placeholder="URL_ID..."
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
                                    className="flex-1 rounded-xl h-11 uppercase tracking-widest text-[10px] font-black"
                                >
                                    ABORT
                                </Button>
                                <Button
                                    onClick={handleEditSave}
                                    variant="tactical"
                                    isLoading={editStage === 'saving'}
                                    className="flex-[1.5] rounded-xl h-11 uppercase tracking-widest text-[10px] font-black"
                                >
                                    UPDATE_REGISTRY
                                </Button>
                            </div>
                        </motion.div>
                    ) : (
                        <Button
                            variant="secondary"
                            onClick={() => setEditMode(true)}
                            className="w-full rounded-xl uppercase tracking-[0.2em] text-[10px] font-black border-white/5 py-5 group shadow-lg"
                        >
                            <Pencil size={14} className="mr-3 text-neutral-600 group-hover:text-brand-accent transition-colors" />
                            AUTHORIZE_REGISTRY_PATCH
                        </Button>
                    )}
                </div>
            )}

            {!editMode && activeTab === 'shop' && !isOwned && (
                <div className="w-full">
                    {isSoldOut ? (
                        <Badge variant="danger" icon={Lock} size="md" className="w-full py-5 rounded-2xl justify-center font-black tracking-[0.3em] border-none shadow-xl bg-danger/10 text-danger">
                            SUMMONS_EXHAUSTED
                        </Badge>
                    ) : !canAfford ? (
                        <div className="flex flex-col gap-2">
                            <Badge variant="tactical" icon={Gem} size="md" className="w-full py-5 rounded-2xl justify-center font-black tracking-[0.2em] border-white/10 bg-black/40 opacity-50">
                                {formatNumber(price - zenithBalance)} ZENITH REQUIRED
                            </Badge>
                            <p className="text-[8px] font-black text-center text-neutral-700 uppercase tracking-widest">INSUFFICIENT_FUNDS_DETECTED</p>
                        </div>
                    ) : purchaseStage === 'idle' ? (
                        <Button
                            onClick={() => setPurchaseStage('confirm')}
                            variant="tactical"
                            className="w-full py-6 rounded-2xl uppercase tracking-[0.3em] text-[12px] font-black shadow-2xl active:scale-[0.98]"
                        >
                            SUMMON_ASSET ({formatNumber(price)} ZENITH)
                        </Button>
                    ) : (
                        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex gap-4">
                            <Button
                                variant="secondary"
                                onClick={() => setPurchaseStage('idle')}
                                className="flex-1 rounded-2xl h-14 uppercase tracking-[0.2em] text-[10px] font-black border-white/5"
                            >
                                ABORT
                            </Button>
                            <Button
                                variant="tactical"
                                onClick={handleBuy}
                                isLoading={purchaseStage === 'buying'}
                                className="flex-[2.5] rounded-2xl h-14 uppercase tracking-[0.2em] text-[11px] font-black shadow-xl"
                            >
                                CONFIRM_SUMMON
                            </Button>
                        </motion.div>
                    )}
                </div>
            )}

            {!editMode && isOwned && (
                <div className="flex gap-4">
                    <Button
                        variant="danger"
                        onClick={handleRecycle}
                        disabled={sellStage !== 'idle'}
                        className="flex-1 rounded-2xl h-14 uppercase tracking-[0.2em] text-[10px] font-black shadow-lg"
                    >
                        {sellStage === 'previewing' || sellStage === 'selling' ? <Loader2 size={16} className="animate-spin" /> : <History size={16} strokeWidth={2.5} className="mr-2" />}
                        RECYCLE
                    </Button>

                    <Button
                        variant="secondary"
                        onClick={handleSell}
                        disabled={sellStage !== 'idle'}
                        className="flex-1 rounded-2xl h-14 uppercase tracking-[0.2em] text-[10px] font-black border-white/10"
                    >
                        {sellStage === 'selling' ? <Loader2 size={16} className="animate-spin" /> : <Coins size={16} strokeWidth={2.5} className="mr-2" />}
                        LIQUIDATE
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
