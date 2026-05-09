import React, { useState, useEffect } from 'react';
import { User, Activity } from 'lucide-react';
import { cn } from '../utils';

export const Avatar = ({ src, alt, className, size = 'default', fallbackIcon: Fallback = User }) => {
  const [error, setError] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setError(false);
    setLoaded(false);
  }, [src]);

  return (
    <div className={cn('relative overflow-hidden bg-slate-900 border border-white/10 flex items-center justify-center', className)}>
      {!error && src ? (
        <img
          src={src}
          alt={alt || "Avatar"}
          onLoad={() => setLoaded(true)}
          onError={() => setError(true)}
          className={cn(
            'w-full h-full object-cover transition-opacity duration-300',
            loaded ? 'opacity-100' : 'opacity-0'
          )}
        />
      ) : null}
      
      {error ? (
        <div className="absolute inset-0 bg-brand-midnight/60 flex items-center justify-center">
          <User size={size === 'large' ? 24 : 14} className="text-slate-600" />
        </div>
      ) : !loaded && (
        <div className="absolute inset-0 bg-brand-midnight/60 flex flex-col items-center justify-center backdrop-blur-sm animate-pulse">
          <Activity size={size === 'large' ? 24 : 14} className="text-slate-600/80 mb-0.5" />
        </div>
      )}
    </div>
  );
};
