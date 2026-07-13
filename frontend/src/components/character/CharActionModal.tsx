import { useState, useEffect } from 'react';
import { Coins, Gem, Image as ImageIcon, Loader2, Lock, Pencil, History, X } from 'lucide-react';
import { useToast } from '../ui/Toast';
import { Modal } from './Modal';
import { apiFetch, getErrorMessage } from '../../api/client';
import { useUser, type Character, type User } from '../../context/UserContext';
import { formatNumber } from '../../utils';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';
import { motion } from 'framer-motion';

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
    const [confirm, setConfirm] = useState<null | { kind: 'recycle' | 'sell'; message: string }>(null);
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
            .catch((err) => console.warn('Registry error:', err));

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
            addToast('All fields are required.', 'error');
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
            addToast('Registry updated.', 'success');
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
            setPurchaseStage('idle');
        }
    };

    const doRecycle = async () => {
        setConfirm(null);
        setSellStage('selling');
        try {
            const res = await apiFetch('/recycle', {
                method: 'POST',
                body: JSON.stringify([selectedChar.id])
            });
            addToast(`Character recycled: +${res.reward} Shards`, 'success');
            triggerRefresh();
            setSelectedChar(null);
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
            setSellStage('idle');
        }
    };

    const doSell = async () => {
        setConfirm(null);
        setSellStage('selling');
        try {
            const res = await apiFetch(`/character/sell/${selectedChar.id}`, { method: 'POST' });
            addToast(`Character sold: +${res.reward} Shards`, 'success');
            triggerRefresh();
            setSelectedChar(null);
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
            setSellStage('idle');
        }
    };

    // Prefer Telegram's native confirm when present; otherwise fall back to an
    // in-app confirm (setConfirm) so destructive actions still prompt outside
    // the Telegram WebApp where showConfirm is undefined.
    const askConfirm = (kind: 'recycle' | 'sell', message: string) => {
        const native = window.Telegram?.WebApp?.showConfirm;
        if (native) {
            native(message, async (confirmed) => {
                if (!confirmed) {
                    setSellStage('idle');
                    return;
                }
                if (kind === 'recycle') await doRecycle();
                else await doSell();
            });
            return;
        }
        setConfirm({ kind, message });
    };

    const handleRecycle = async () => {
        setSellStage('previewing');
        try {
            const preview = await apiFetch('/recycle/preview', {
                method: 'POST',
                body: JSON.stringify([selectedChar.id])
            });
            askConfirm('recycle', `Recycle ${selectedChar.name.toUpperCase()} for ${preview.reward} Shards?`);
        } catch (err: any) {
            addToast(getErrorMessage(err), 'error');
            setSellStage('idle');
        }
    };

    const handleSell = () => {
        setSellStage('selling');
        askConfirm('sell', `Sell ${selectedChar.name.toUpperCase()} for Shards?`);
    };

    const actions = (
        <div className="w-full space-y-4">
            {canEdit && (
                <div className="w-full">
                    {editMode ? (
                        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-4 p-4 rounded-md border border-white/5 bg-zinc-900">
                            <div className="space-y-3">
                                <div className="space-y-1">
                                    <span className="text-[9px] font-bold uppercase text-zinc-600 tracking-widest pl-0.5">Character Name</span>
                                    <Input
                                        value={editForm.name}
                                        onChange={event => updateEditField('name', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        placeholder="Name..."
                                    />
                                </div>
                                <div className="space-y-1">
                                    <span className="text-[9px] font-bold uppercase text-zinc-600 tracking-widest pl-0.5">Source</span>
                                    <Input
                                        value={editForm.anime}
                                        onChange={event => updateEditField('anime', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        placeholder="Source..."
                                    />
                                </div>
                                <div className="space-y-1">
                                    <span className="text-[9px] font-bold uppercase text-zinc-600 tracking-widest pl-0.5">Rarity Class</span>
                                    <div className="relative group">
                                        <select
                                            aria-label="Rarity class"
                                            value={editForm.rarity}
                                            onChange={event => updateEditField('rarity', event.target.value)}
                                            disabled={editStage === 'saving'}
                                            className="w-full h-10 bg-zinc-950 border border-white/10 rounded-md px-3.5 text-[11px] font-bold text-zinc-100 uppercase tracking-widest outline-none focus:border-brand-accent transition-all appearance-none cursor-pointer"
                                        >
                                            {!rarityOptions.some(option => option.label === editForm.rarity) && editForm.rarity && (
                                                <option value={editForm.rarity}>{editForm.rarity.toUpperCase()}</option>
                                            )}
                                            {rarityOptions.map(option => (
                                                <option key={option.value} value={option.label}>
                                                    Tier {option.value}: {option.label.toUpperCase()}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <span className="text-[9px] font-bold uppercase text-zinc-600 tracking-widest pl-0.5">Visual Manifest</span>
                                    <Input
                                        icon={ImageIcon}
                                        value={editForm.img_url}
                                        onChange={event => updateEditField('img_url', event.target.value)}
                                        disabled={editStage === 'saving'}
                                        placeholder="Image URL..."
                                    />
                                </div>
                            </div>

                            <div className="flex gap-2 pt-1">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                        setEditForm(buildEditForm(selectedChar));
                                        setEditMode(false);
                                    }}
                                    disabled={editStage === 'saving'}
                                    className="flex-1"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    onClick={handleEditSave}
                                    variant="secondary"
                                    size="sm"
                                    isLoading={editStage === 'saving'}
                                    className="flex-[1.5]"
                                >
                                    Update Character
                                </Button>
                            </div>
                        </motion.div>
                    ) : (
                        <Button
                            variant="secondary"
                            onClick={() => setEditMode(true)}
                            className="w-full group h-12"
                            leftIcon={<Pencil size={14} className="text-zinc-500 transition-colors group-hover:text-brand-accent" />}
                        >
                            Modify Records
                        </Button>
                    )}
                </div>
            )}

            {!editMode && activeTab === 'shop' && !isOwned && (
                <div className="w-full">
                    {isSoldOut ? (
                        <Badge variant="danger" icon={Lock} className="w-full py-4 rounded-md justify-center font-bold border-none bg-red-500/10 text-red-500">
                            DEPLETED
                        </Badge>
                    ) : !canAfford ? (
                        <div className="flex flex-col gap-2">
                            <Badge variant="secondary" icon={Gem} className="w-full py-4 rounded-md justify-center font-bold border-white/5 opacity-50">
                                {formatNumber(price - zenithBalance)} Zenith Needed
                            </Badge>
                            <p className="text-[8px] font-bold text-center text-zinc-700 uppercase tracking-widest">Insufficient funds</p>
                        </div>
                    ) : purchaseStage === 'idle' ? (
                        <Button
                            onClick={() => setPurchaseStage('confirm')}
                            variant="accent"
                            className="w-full h-14"
                        >
                            Summon Character ({formatNumber(price)} Zenith)
                        </Button>
                    ) : (
                        <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="flex gap-3">
                            <Button
                                variant="outline"
                                onClick={() => setPurchaseStage('idle')}
                                className="flex-1 h-14"
                            >
                                Abort
                            </Button>
                            <Button
                                variant="accent"
                                onClick={handleBuy}
                                isLoading={purchaseStage === 'buying'}
                                className="flex-[2] h-14"
                            >
                                Confirm Summon
                            </Button>
                        </motion.div>
                    )}
                </div>
            )}

            {!editMode && isOwned && !confirm && (
                <div className="flex gap-3">
                    <Button
                        variant="danger"
                        onClick={handleRecycle}
                        disabled={sellStage !== 'idle'}
                        className="flex-1 h-14"
                        leftIcon={sellStage === 'previewing' || sellStage === 'selling' ? <Loader2 size={14} className="animate-spin" /> : <History size={14} />}
                    >
                        Recycle
                    </Button>

                    <Button
                        variant="secondary"
                        onClick={handleSell}
                        disabled={sellStage !== 'idle'}
                        className="flex-1 h-14"
                        leftIcon={sellStage === 'selling' ? <Loader2 size={14} className="animate-spin" /> : <Coins size={14} />}
                    >
                        Liquidate
                    </Button>
                </div>
            )}

            {confirm && (
                <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col gap-3">
                    <p className="text-center text-[10px] font-bold uppercase tracking-widest text-zinc-300 px-2">{confirm.message}</p>
                    <div className="flex gap-3">
                        <Button
                            variant="outline"
                            onClick={() => { setConfirm(null); setSellStage('idle'); }}
                            className="flex-1 h-14"
                        >
                            Abort
                        </Button>
                        <Button
                            variant="danger"
                            onClick={confirm.kind === 'recycle' ? doRecycle : doSell}
                            isLoading={sellStage === 'selling'}
                            className="flex-[2] h-14"
                        >
                            Confirm
                        </Button>
                    </div>
                </motion.div>
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
