declare module '*.vue' {
  import type { DefineComponent } from 'vue'
}

declare module '*.ts' {
  import type { Import } from 'vite'
}

declare module '*.json' {
  import type { ImportEnv } from 'vite'
}

declare module '*.svg' {
  content: string
}

declare interface ImportMetaEnv {
  readonly VITE_APP_TITLE: string
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
