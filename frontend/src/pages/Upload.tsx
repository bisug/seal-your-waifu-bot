import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from 'react';
import {
  CheckCircle2,
  FileImage,
  Image,
  Link as LinkIcon,
  Loader2,
  PawPrint,
  ShieldCheck,
  UploadCloud,
  Target,
  Sparkles,
  Info,
  ChevronRight,
  Database,
  Type,
  Video,
  Zap,
  Gem,
} from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { useUser } from '../context/UserContext';
import { cn } from '../utils';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { motion, AnimatePresence } from 'framer-motion';

type UploadMode = 'character' | 'pet';
type MediaSource = 'file' | 'url';

interface UploadOptions {
  max_size_mb: number;
  role?: {
    role_label?: string | null;
    role_tag?: string | null;
    role_symbol?: string | null;
    upload_reward?: {
      balance?: number;
      zenith?: number;
    } | null;
    role_benefits?: string[];
  };
  character_rarities: Array<{ value: number; label: string }>;
  pet_defaults: {
    rarity: string;
    hp: number;
    atk: number;
    spd: number;
    luck: number;
    ability: string;
    zenith_price: number;
    req_level: number;
    sort_order: number;
    enabled: boolean;
  };
}

const initialCharacter = {
  name: '',
  anime: '',
  rarity: '1',
};

const initialPet = {
  name: '',
  petid: '',
  rarity: 'Common',
  hp: '100',
  atk: '20',
  spd: '20',
  luck: '0.08',
  ability: 'None',
  desc: '',
  zenith_price: '0',
  req_level: '0',
  sort_order: '100',
  enabled: true,
};

const numberFrom = (value: string, fallback: number) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const isVideoSrc = (src: string) => /\.(mp4|webm)(\?|#|$)/i.test(src);

export const Upload = () => {
  const { addToast } = useToast();
  const { user, refreshUser } = useUser();
  const [mode, setMode] = useState<UploadMode>('character');
  const [source, setSource] = useState<MediaSource>('file');
  const [options, setOptions] = useState<UploadOptions | null>(null);
  const [character, setCharacter] = useState(initialCharacter);
  const [pet, setPet] = useState(initialPet);
  const [mediaUrl, setMediaUrl] = useState('');
  const [mediaData, setMediaData] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState<string | null>(null);

  useEffect(() => {
    apiFetch('/admin/upload/options')
      .then((data: UploadOptions) => {
        setOptions(data);
        setPet(prev => ({
          ...prev,
          rarity: data.pet_defaults.rarity,
          hp: String(data.pet_defaults.hp),
          atk: String(data.pet_defaults.atk),
          spd: String(data.pet_defaults.spd),
          luck: String(data.pet_defaults.luck),
          ability: data.pet_defaults.ability,
          zenith_price: String(data.pet_defaults.zenith_price),
          req_level: String(data.pet_defaults.req_level),
          sort_order: String(data.pet_defaults.sort_order),
          enabled: data.pet_defaults.enabled,
        }));
      })
      .catch(err => addToast(getErrorMessage(err), 'error'));
  }, [addToast]);

  const previewSrc = useMemo(() => {
    if (source === 'file') return mediaData || '';
    return mediaUrl.trim();
  }, [mediaData, mediaUrl, source]);

  const uploadReward = user?.upload_reward
    ? [
        user.upload_reward.balance ? `${numberFrom(String(user.upload_reward.balance), 0).toLocaleString()} SHARDS` : '',
        user.upload_reward.zenith ? `${numberFrom(String(user.upload_reward.zenith), 0).toLocaleString()} ZENITH` : '',
      ].filter(Boolean).join(' + ')
    : '';
  const roleBenefits = user?.role_benefits || options?.role?.role_benefits || [];

  const clearMedia = () => {
    setMediaData(null);
    setFilename(null);
    setMediaUrl('');
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const maxBytes = (options?.max_size_mb || 10) * 1024 * 1024;
    if (file.size > maxBytes) {
      addToast(`Protocol Limit: File must be ${options?.max_size_mb || 10}MB or smaller.`, 'error');
      event.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setMediaData(String(reader.result || ''));
      setFilename(file.name);
    };
    reader.onerror = () => addToast('System error: Could not read selected file.', 'error');
    reader.readAsDataURL(file);
  };

  const buildMediaPayload = () => {
    if (source === 'url') {
      const url = mediaUrl.trim();
      if (!url) throw new Error('Input required: Add a media URL.');
      return { media_url: url };
    }
    if (!mediaData) throw new Error('Input required: Choose a media file.');
    return { media_data: mediaData, filename };
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    setLastResult(null);
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium');

    try {
      const mediaPayload = buildMediaPayload();
      const endpoint = mode === 'character' ? '/admin/upload/character' : '/admin/upload/pet';
      const payload = mode === 'character'
        ? {
            ...mediaPayload,
            name: character.name.trim(),
            anime: character.anime.trim(),
            rarity: Number(character.rarity),
          }
        : {
            ...mediaPayload,
            name: pet.name.trim(),
            petid: pet.petid.trim() || null,
            rarity: pet.rarity.trim() || 'Common',
            hp: numberFrom(pet.hp, 100),
            atk: numberFrom(pet.atk, 20),
            spd: numberFrom(pet.spd, 20),
            luck: pet.luck.trim(),
            ability: pet.ability.trim() || 'None',
            desc: pet.desc.trim(),
            zenith_price: numberFrom(pet.zenith_price, 0),
            req_level: numberFrom(pet.req_level, 0),
            sort_order: numberFrom(pet.sort_order, 100),
            enabled: pet.enabled,
          };

      const result = await apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload),
        timeoutMs: 90000,
      });

      const message = result?.message || 'Transmission complete. Asset secured.';
      setLastResult(message);
      addToast(message, 'success');
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
      refreshUser().catch(() => undefined);
      clearMedia();
      if (mode === 'character') {
        setCharacter(initialCharacter);
      } else {
        setPet(prev => ({ ...initialPet, rarity: prev.rarity }));
      }
    } catch (err) {
      addToast(getErrorMessage(err), 'error');
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="pb-32 pt-8 max-w-3xl mx-auto adaptive-px space-y-10 select-none">
      <header className="space-y-6">
        <div className="flex items-center gap-4">
           <div className="w-12 h-12 rounded-2xl bg-brand-accent/10 border border-brand-accent/20 flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)]">
                <UploadCloud className="text-brand-accent" size={26} />
           </div>
           <div className="flex flex-col gap-1">
              <h1 className="text-3xl font-black text-white tracking-tighter uppercase leading-none">Intake</h1>
              <div className="flex items-center gap-2">
                 <ShieldCheck size={11} className="text-neutral-600" />
                 <p className="text-[10px] font-black text-neutral-500 uppercase tracking-widest leading-none">
                    ASSET INGESTION & REGISTRY TERMINAL
                 </p>
              </div>
           </div>
        </div>

        {user?.role_tag && (
          <div className="flex flex-wrap gap-2 pt-2">
            <Badge variant="primary" size="xs" className="px-2.5 py-1 rounded-md font-black border-brand-accent/30 bg-brand-accent/10">
              {user.role_symbol} {user.role_label || user.role_tag}
            </Badge>
            {uploadReward && (
              <Badge variant="success" size="xs" className="px-2.5 py-1 rounded-md font-mono border-success/10 bg-success/5 text-success">
                REWARD: {uploadReward}
              </Badge>
            )}
            {roleBenefits.slice(0, 3).map((benefit) => (
              <Badge key={benefit} variant="secondary" size="xs" className="px-2.5 py-1 rounded-md border-white/5 bg-white/[0.02] text-neutral-400">
                {benefit.toUpperCase()}
              </Badge>
            ))}
          </div>
        )}
      </header>

      <div className="p-1.5 rounded-2xl bg-black/40 border border-white/[0.03] grid grid-cols-2 gap-3">
        {[
          { id: 'character' as const, label: 'ASSET_CHAR', icon: Image },
          { id: 'pet' as const, label: 'UNIT_COMP', icon: PawPrint },
        ].map(item => {
          const active = mode === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                  window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                  setMode(item.id);
              }}
              className={cn(
                'h-12 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 transition-all duration-300',
                active ? 'bg-white text-black shadow-xl' : 'text-neutral-600 hover:text-white hover:bg-white/[0.02]'
              )}
            >
              <item.icon size={16} strokeWidth={2.5} />
              {item.label}
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        <section className="space-y-4">
          <div className="flex items-center gap-2 px-1">
             <Target size={12} className="text-neutral-700" />
             <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.3em]">MEDIA_SOURCE</span>
          </div>
          <Card variant="tactical" className="p-6 border-white/[0.04] bg-white/[0.01] space-y-6">
            <div className="grid grid-cols-2 gap-3 p-1 bg-black/40 rounded-xl border border-white/[0.03]">
                {[
                { id: 'file' as const, label: 'LOCAL_STORAGE', icon: FileImage },
                { id: 'url' as const, label: 'REMOTE_LINK', icon: LinkIcon },
                ].map(item => {
                const active = source === item.id;
                return (
                    <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                        window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                        setSource(item.id);
                        clearMedia();
                    }}
                    className={cn(
                        'h-10 rounded-lg text-[9px] font-black uppercase tracking-widest flex items-center justify-center gap-2 transition-all duration-300',
                        active ? 'bg-neutral-800 text-white shadow-lg' : 'text-neutral-600 hover:text-neutral-300'
                    )}
                    >
                    <item.icon size={14} />
                    {item.label}
                    </button>
                );
                })}
            </div>

            {source === 'file' ? (
                <div className="space-y-3">
                    <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Media Manifest</span>
                    <div className="relative group">
                        <input
                            type="file"
                            accept="image/*,video/mp4,video/webm"
                            onChange={handleFileChange}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                        />
                        <div className="h-20 w-full rounded-2xl border border-dashed border-white/10 group-hover:border-brand-accent/40 group-hover:bg-brand-accent/[0.01] transition-all flex flex-col items-center justify-center gap-2 bg-black/20">
                            <UploadCloud size={20} className="text-neutral-700 group-hover:text-brand-accent transition-colors" />
                            <p className="text-[10px] font-black text-neutral-600 uppercase tracking-widest group-hover:text-white transition-colors">
                                {filename ? filename : 'DROP FILE OR TAP TO BROWSE'}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 opacity-40 pl-1">
                       <Info size={10} />
                       <span className="text-[8px] font-black uppercase tracking-widest">LIMIT: {options?.max_size_mb || 10}MB_MAX</span>
                    </div>
                </div>
            ) : (
                <div className="space-y-3">
                    <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Remote Link ID</span>
                    <Input
                        icon={LinkIcon}
                        value={mediaUrl}
                        onChange={event => setMediaUrl(event.target.value)}
                        placeholder="https://secure.registry/asset.jpg"
                    />
                </div>
            )}

            <AnimatePresence>
                {previewSrc && (
                    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="mt-4 rounded-2xl overflow-hidden border border-white/[0.05] bg-brand-midnight shadow-2xl relative group">
                        <div className="absolute top-3 left-3 z-10">
                           <Badge variant="tactical" size="xs" className="bg-black/60 backdrop-blur-md border-white/10 opacity-60">PREVIEW_SYNC_OK</Badge>
                        </div>
                        {isVideoSrc(previewSrc) ? (
                            <video src={previewSrc} controls className="w-full max-h-80 object-contain bg-black" />
                        ) : (
                            <img src={previewSrc} alt="Upload preview" className="w-full max-h-80 object-contain bg-black transition-transform duration-1000 group-hover:scale-105" />
                        )}
                        <div className="absolute inset-0 bg-scanline opacity-[0.03] pointer-events-none" />
                    </motion.div>
                )}
            </AnimatePresence>
          </Card>
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-2 px-1">
             <Database size={12} className="text-neutral-700" />
             <span className="text-[9px] font-black text-neutral-600 uppercase tracking-[0.3em]">METADATA_REGISTRY</span>
          </div>
          <Card variant="tactical" className="p-6 border-white/[0.04] bg-white/[0.01] space-y-6">
            {mode === 'character' ? (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="space-y-3">
                           <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Designation</span>
                           <Input
                             icon={Type}
                             value={character.name}
                             onChange={event => setCharacter(prev => ({ ...prev, name: event.target.value }))}
                             required
                             placeholder="ASSET NAME..."
                           />
                        </div>
                        <div className="space-y-3">
                           <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Origin Origin</span>
                           <Input
                             icon={Database}
                             value={character.anime}
                             onChange={event => setCharacter(prev => ({ ...prev, anime: event.target.value }))}
                             required
                             placeholder="DATA SOURCE..."
                           />
                        </div>
                    </div>
                    <div className="space-y-3">
                        <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Rarity Classification</span>
                        <div className="relative group">
                            <select
                                value={character.rarity}
                                onChange={event => setCharacter(prev => ({ ...prev, rarity: event.target.value }))}
                                className="w-full h-12 bg-black/40 border border-white/10 rounded-xl px-4 text-[11px] font-black text-white uppercase tracking-widest outline-none focus:border-brand-accent transition-all appearance-none cursor-pointer hover:bg-white/[0.02]"
                            >
                                {(options?.character_rarities || []).map(rarity => (
                                <option key={rarity.value} value={rarity.value}>
                                    CLASS_{rarity.value}: {rarity.label.toUpperCase()}
                                </option>
                                ))}
                            </select>
                            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-600 group-hover:text-brand-accent transition-colors pointer-events-none">
                               <ChevronRight size={16} />
                            </div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="space-y-3">
                           <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Unit Name</span>
                           <Input
                             icon={PawPrint}
                             value={pet.name}
                             onChange={event => setPet(prev => ({ ...prev, name: event.target.value }))}
                             required
                             placeholder="UNIT DESIGNATION..."
                           />
                        </div>
                        <div className="space-y-3">
                           <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Personnel ID</span>
                           <Input
                             icon={Target}
                             value={pet.petid}
                             onChange={event => setPet(prev => ({ ...prev, petid: event.target.value }))}
                             placeholder="AUTO_ID_GEN"
                           />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        {[
                            { key: 'hp', label: 'VITALITY', icon: Target },
                            { key: 'atk', label: 'STRIKE', icon: Target },
                            { key: 'spd', label: 'VELOCITY', icon: Target },
                            { key: 'luck', label: 'LUCK_RT', icon: Target },
                        ].map((stat) => (
                            <div key={stat.key} className="space-y-2">
                                <span className="text-[9px] font-black text-neutral-700 uppercase tracking-widest pl-1">{stat.label}</span>
                                <Input
                                    value={pet[stat.key as keyof typeof pet] as string}
                                    onChange={event => setPet(prev => ({ ...prev, [stat.key]: event.target.value }))}
                                    inputMode="decimal"
                                    className="font-mono text-center px-2"
                                    placeholder="0"
                                />
                            </div>
                        ))}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        <div className="space-y-3">
                           <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Class Rank</span>
                           <Input
                             value={pet.rarity}
                             onChange={event => setPet(prev => ({ ...prev, rarity: event.target.value }))}
                             placeholder="RANK..."
                           />
                        </div>
                        <div className="space-y-3">
                           <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Primary Ability</span>
                           <Input
                             icon={Zap}
                             value={pet.ability}
                             onChange={event => setPet(prev => ({ ...prev, ability: event.target.value }))}
                             placeholder="SPECIAL PERK..."
                           />
                        </div>
                    </div>

                    <div className="space-y-3">
                        <span className="text-[10px] font-black text-neutral-600 uppercase tracking-[0.2em] pl-1">Registry Description</span>
                        <textarea
                            value={pet.desc}
                            onChange={event => setPet(prev => ({ ...prev, desc: event.target.value }))}
                            rows={3}
                            placeholder="INPUT DETAILED ASSET OVERVIEW..."
                            className="w-full rounded-xl bg-black/40 border border-white/10 px-4 py-4 text-xs font-bold text-white outline-none focus:border-brand-accent transition-all resize-none uppercase tracking-widest placeholder:text-neutral-800 shadow-inner"
                        />
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 items-end">
                        {[
                            { key: 'zenith_price', label: 'COST', icon: Gem },
                            { key: 'req_level', label: 'LEVEL', icon: Target },
                            { key: 'sort_order', label: 'ORDER', icon: History },
                        ].map((item) => (
                            <div key={item.key} className="space-y-2">
                                <span className="text-[9px] font-black text-neutral-700 uppercase tracking-widest pl-1">{item.label}</span>
                                <Input
                                    value={pet[item.key as keyof typeof pet] as string}
                                    onChange={event => setPet(prev => ({ ...prev, [item.key]: event.target.value }))}
                                    inputMode="numeric"
                                    className="font-mono text-center"
                                />
                            </div>
                        ))}
                        <div className="flex items-center gap-3 pb-3 pl-2">
                            <input
                            type="checkbox"
                            checked={pet.enabled}
                            onChange={event => setPet(prev => ({ ...prev, enabled: event.target.checked }))}
                            className="h-6 w-6 rounded-lg border-white/10 bg-black/40 accent-brand-accent cursor-pointer"
                            id="pet-enabled"
                            />
                            <label htmlFor="pet-enabled" className="text-[10px] font-black text-neutral-500 uppercase tracking-widest cursor-pointer select-none">
                                ONLINE
                            </label>
                        </div>
                    </div>
                </div>
            )}
          </Card>
        </section>

        {lastResult && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-success/20 bg-success/[0.03] p-5 flex items-center gap-4 text-[11px] font-black uppercase tracking-widest text-success shadow-lg">
            <div className="w-8 h-8 rounded-full bg-success/10 flex items-center justify-center border border-success/20 shadow-inner">
               <CheckCircle2 size={18} strokeWidth={3} />
            </div>
            {lastResult}
          </motion.div>
        )}

        <div className="pt-4">
            <Button
            type="submit"
            disabled={submitting}
            variant="tactical"
            className="w-full h-16 rounded-2xl font-black text-[12px] uppercase tracking-[0.4em] shadow-2xl active:scale-[0.98] transition-all"
            >
            {submitting ? (
                <>
                    <Loader2 size={20} className="animate-spin mr-3" />
                    TRANSMITTING...
                </>
            ) : (
                <>
                    <UploadCloud size={20} strokeWidth={2.5} className="mr-3" />
                    AUTHORIZE_UPLOAD
                </>
            )}
            </Button>
        </div>
      </form>

      <div className="flex items-center justify-center gap-3 opacity-20 py-4 pt-12">
         <Sparkles size={12} className="text-brand-accent" />
         <span className="text-[9px] font-black uppercase tracking-[0.4em] text-white">Secure Upload Channel</span>
      </div>
    </div>
  );
};
