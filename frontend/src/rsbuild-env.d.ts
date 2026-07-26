/// <reference types="@rsbuild/core/types" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_API_PREFIX: string;
  readonly VITE_BOT_USERNAME: string;
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
