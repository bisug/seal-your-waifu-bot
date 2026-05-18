import React, { useState, useEffect } from 'react';
import { User } from 'lucide-react';
import { cn } from '../utils';

interface AvatarProps {
  src?: string | null;
  alt?: string;
  className?: string;
}

export const Avatar = ({ src, alt = "Avatar", className = "" }: AvatarProps) => {
  const [error, setError] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    // Wrap in microtask to avoid cascading render warning
    Promise.resolve().then(() => {
      setError(false);
      setLoaded(false);
    });
  }, [src]);

  return (
    <div className={cn("relative overflow-hidden bg-white/5 flex items-center justify-center shrink-0", className)}>
      {!error && src ? (
        <>
          <img
            src={src}
            alt={alt}
            onLoad={() => setLoaded(true)}
            onError={() => setError(true)}
            className={cn(
              "w-full h-full object-cover transition-opacity duration-300",
              loaded ? "opacity-100" : "opacity-0"
            )}
          />
          {!loaded && (
            <div className="absolute inset-0 animate-pulse bg-white/10" />
          )}
        </>
      ) : (
        <User className="text-white/20 w-1/2 h-1/2" />
      )}
    </div>
  );
};
