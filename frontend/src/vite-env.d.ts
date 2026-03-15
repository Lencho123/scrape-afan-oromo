// vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string; // your env variable
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}