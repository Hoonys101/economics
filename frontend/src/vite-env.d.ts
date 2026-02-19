/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_GOD_MODE_TOKEN: string
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}
