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
} from 'lucide-react';
import { apiFetch, getErrorMessage } from '../api/client';
import { useToast } from '../components/ui/Toast';
import { cn } from '../utils';

type UploadMode = 'character' | 'pet';
type MediaSource = 'file' | 'url';

interface UploadOptions {
  max_size_mb: number;
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
      addToast(`File must be ${options?.max_size_mb || 10}MB or smaller.`, 'error');
      event.target.value = '';
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setMediaData(String(reader.result || ''));
      setFilename(file.name);
    };
    reader.onerror = () => addToast('Could not read selected file.', 'error');
    reader.readAsDataURL(file);
  };

  const buildMediaPayload = () => {
    if (source === 'url') {
      const url = mediaUrl.trim();
      if (!url) throw new Error('Add a media URL.');
      return { media_url: url };
    }
    if (!mediaData) throw new Error('Choose a media file.');
    return { media_data: mediaData, filename };
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    setLastResult(null);

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
        timeoutMs: 70000,
      });

      const message = result?.message || 'Upload complete.';
      setLastResult(message);
      addToast(message, 'success');
      clearMedia();
      if (mode === 'character') {
        setCharacter(initialCharacter);
      } else {
        setPet(prev => ({ ...initialPet, rarity: prev.rarity }));
      }
    } catch (err) {
      addToast(getErrorMessage(err), 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="px-4 py-6 pb-24 max-w-3xl mx-auto select-none">
      <header className="mb-6 border-b border-white/5 pb-4">
        <div className="flex items-center gap-2 mb-1">
          <ShieldCheck size={18} className="text-brand-accent" />
          <h1 className="text-xl font-bold text-white">Upload</h1>
        </div>
        <p className="text-sm font-medium text-neutral-400">Add catalog characters and pet store entries.</p>
      </header>

      <div className="grid grid-cols-2 gap-2 mb-5 rounded-lg bg-brand-deep border border-white/5 p-1">
        {[
          { id: 'character' as const, label: 'Character', icon: Image },
          { id: 'pet' as const, label: 'Pet', icon: PawPrint },
        ].map(item => {
          const Icon = item.icon;
          const active = mode === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setMode(item.id)}
              className={cn(
                'h-10 rounded-md text-sm font-semibold flex items-center justify-center gap-2 transition-colors',
                active ? 'bg-white text-brand-midnight' : 'text-neutral-400 hover:text-white'
              )}
            >
              <Icon size={16} />
              {item.label}
            </button>
          );
        })}
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <section className="rounded-lg border border-white/5 bg-brand-deep p-4">
          <div className="grid grid-cols-2 gap-2 mb-4 rounded-lg bg-brand-midnight border border-white/5 p-1">
            {[
              { id: 'file' as const, label: 'File', icon: FileImage },
              { id: 'url' as const, label: 'URL', icon: LinkIcon },
            ].map(item => {
              const Icon = item.icon;
              const active = source === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => {
                    setSource(item.id);
                    clearMedia();
                  }}
                  className={cn(
                    'h-9 rounded-md text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors',
                    active ? 'bg-white text-brand-midnight' : 'text-neutral-500 hover:text-neutral-200'
                  )}
                >
                  <Icon size={14} />
                  {item.label}
                </button>
              );
            })}
          </div>

          {source === 'file' ? (
            <label className="block">
              <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Media file</span>
              <input
                type="file"
                accept="image/*,video/mp4,video/webm"
                onChange={handleFileChange}
                className="mt-2 w-full text-sm text-neutral-300 file:mr-3 file:rounded-md file:border-0 file:bg-white file:px-3 file:py-2 file:text-sm file:font-bold file:text-brand-midnight"
              />
              {filename && <span className="mt-2 block text-xs font-medium text-neutral-500 truncate">{filename}</span>}
            </label>
          ) : (
            <label className="block">
              <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Media URL</span>
              <input
                value={mediaUrl}
                onChange={event => setMediaUrl(event.target.value)}
                placeholder="https://..."
                className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
              />
            </label>
          )}

          {previewSrc && (
            <div className="mt-4 overflow-hidden rounded-lg border border-white/5 bg-brand-midnight">
              {isVideoSrc(previewSrc) ? (
                <video src={previewSrc} controls className="w-full max-h-72 object-contain bg-black" />
              ) : (
                <img src={previewSrc} alt="Upload preview" className="w-full max-h-72 object-contain bg-black" />
              )}
            </div>
          )}
        </section>

        {mode === 'character' ? (
          <section className="rounded-lg border border-white/5 bg-brand-deep p-4 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label>
                <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Name</span>
                <input
                  value={character.name}
                  onChange={event => setCharacter(prev => ({ ...prev, name: event.target.value }))}
                  required
                  className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
                />
              </label>
              <label>
                <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Anime</span>
                <input
                  value={character.anime}
                  onChange={event => setCharacter(prev => ({ ...prev, anime: event.target.value }))}
                  required
                  className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
                />
              </label>
            </div>
            <label className="block">
              <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Rarity</span>
              <select
                value={character.rarity}
                onChange={event => setCharacter(prev => ({ ...prev, rarity: event.target.value }))}
                className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
              >
                {(options?.character_rarities || []).map(rarity => (
                  <option key={rarity.value} value={rarity.value}>
                    {rarity.value}. {rarity.label}
                  </option>
                ))}
              </select>
            </label>
          </section>
        ) : (
          <section className="rounded-lg border border-white/5 bg-brand-deep p-4 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label>
                <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Name</span>
                <input
                  value={pet.name}
                  onChange={event => setPet(prev => ({ ...prev, name: event.target.value }))}
                  required
                  className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
                />
              </label>
              <label>
                <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Pet ID</span>
                <input
                  value={pet.petid}
                  onChange={event => setPet(prev => ({ ...prev, petid: event.target.value }))}
                  placeholder="Auto from name"
                  className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
                />
              </label>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                ['hp', 'HP'],
                ['atk', 'ATK'],
                ['spd', 'SPD'],
                ['luck', 'Luck'],
              ].map(([key, label]) => (
                <label key={key}>
                  <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">{label}</span>
                  <input
                    value={pet[key as keyof typeof pet] as string}
                    onChange={event => setPet(prev => ({ ...prev, [key]: event.target.value }))}
                    inputMode="decimal"
                    className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
                  />
                </label>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label>
                <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Rarity</span>
                <input
                  value={pet.rarity}
                  onChange={event => setPet(prev => ({ ...prev, rarity: event.target.value }))}
                  className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
                />
              </label>
              <label>
                <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Ability</span>
                <input
                  value={pet.ability}
                  onChange={event => setPet(prev => ({ ...prev, ability: event.target.value }))}
                  className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
                />
              </label>
            </div>

            <label className="block">
              <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">Description</span>
              <textarea
                value={pet.desc}
                onChange={event => setPet(prev => ({ ...prev, desc: event.target.value }))}
                rows={3}
                className="mt-2 w-full rounded-lg bg-brand-midnight border border-white/10 px-3 py-3 text-sm font-medium text-white outline-none focus:border-brand-accent resize-none"
              />
            </label>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                ['zenith_price', 'Price'],
                ['req_level', 'Req Level'],
                ['sort_order', 'Sort'],
              ].map(([key, label]) => (
                <label key={key}>
                  <span className="text-xs font-bold text-neutral-500 uppercase tracking-wider">{label}</span>
                  <input
                    value={pet[key as keyof typeof pet] as string}
                    onChange={event => setPet(prev => ({ ...prev, [key]: event.target.value }))}
                    inputMode="numeric"
                    className="mt-2 w-full h-11 rounded-lg bg-brand-midnight border border-white/10 px-3 text-sm font-medium text-white outline-none focus:border-brand-accent"
                  />
                </label>
              ))}
              <label className="flex items-end gap-3 h-full pb-2">
                <input
                  type="checkbox"
                  checked={pet.enabled}
                  onChange={event => setPet(prev => ({ ...prev, enabled: event.target.checked }))}
                  className="h-5 w-5 rounded border-white/10 bg-brand-midnight accent-brand-accent"
                />
                <span className="text-sm font-semibold text-neutral-300">Enabled</span>
              </label>
            </div>
          </section>
        )}

        {lastResult && (
          <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 flex items-center gap-3 text-sm font-semibold text-emerald-400">
            <CheckCircle2 size={18} />
            {lastResult}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full h-12 rounded-lg bg-white text-brand-midnight font-bold text-sm flex items-center justify-center gap-2 transition-transform active:scale-[0.98] disabled:opacity-60"
        >
          {submitting ? <Loader2 size={18} className="animate-spin" /> : <UploadCloud size={18} />}
          {submitting ? 'Uploading' : `Upload ${mode === 'character' ? 'Character' : 'Pet'}`}
        </button>
      </form>
    </div>
  );
};
