<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  // Initialize theme from localStorage, default to tcm-zen
  const savedTheme = localStorage.getItem('app-theme') || 'tcm-zen'
  document.documentElement.setAttribute('data-theme', savedTheme)
  
  if (savedTheme === 'dark-future') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
})
</script>

<style>
/* Base Theme Variables */
:root {
  /* Default: TCM Zen */
  --theme-bg: #F9F6F0;
  --theme-page-bg: #F0EFE9;
  --theme-card-bg: #FFFFFF;
  --theme-text: #2C3E50;
  --theme-text-secondary: #5C6E7A;
  --theme-border: rgba(44, 62, 80, 0.1);
  --theme-border-light: rgba(44, 62, 80, 0.05);
  --theme-accent: #4A7C59;
  --theme-accent-rgb: 74, 124, 89;
  --theme-accent-hover: #3E6B4B;
  --theme-shadow: 0 4px 12px rgba(44, 62, 80, 0.05);
  --theme-overlay: rgba(249, 246, 240, 0.85);

  /* Element Plus Overrides for TCM Zen */
  --el-color-primary: var(--theme-accent);
  --el-color-primary-light-3: #75A584;
  --el-color-primary-dark-2: var(--theme-accent-hover);
  --el-text-color-primary: var(--theme-text);
  --el-text-color-regular: var(--theme-text-secondary);
  --el-text-color-secondary: #8B9AA4;
  --el-bg-color: var(--theme-bg);
  --el-bg-color-page: var(--theme-page-bg);
  --el-bg-color-overlay: var(--theme-card-bg);
  --el-border-color: var(--theme-border);
  --el-border-color-light: var(--theme-border-light);
  --el-fill-color-blank: var(--theme-card-bg);

  /* Map --tcm-* variables to --theme-* dynamically to support all refactored views */
  --tcm-bg-color: var(--theme-bg);
  --tcm-page-bg: var(--theme-page-bg);
  --tcm-card-bg: var(--theme-card-bg);
  --tcm-text-primary: var(--theme-text);
  --tcm-text-regular: var(--theme-text-secondary);
  --tcm-border-color: var(--theme-border);
  --tcm-accent-color: var(--theme-accent);
  --tcm-shadow: var(--theme-shadow);
  --tcm-ambient-gradient: radial-gradient(circle at 50% 0%, rgba(74, 124, 89, 0.05) 0%, transparent 70%);
}

[data-theme="modern-clinical"] {
  --theme-bg: #F3F4F6;
  --theme-page-bg: #E5E7EB;
  --theme-card-bg: #FFFFFF;
  --theme-text: #1F2937;
  --theme-text-secondary: #4B5563;
  --theme-border: rgba(31, 41, 55, 0.1);
  --theme-border-light: rgba(31, 41, 55, 0.05);
  --theme-accent: #3B82F6;
  --theme-accent-rgb: 59, 130, 246;
  --theme-accent-hover: #2563EB;
  --theme-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  --theme-overlay: rgba(255, 255, 255, 0.9);

  /* Element Plus Overrides for Modern Clinical */
  --el-color-primary: var(--theme-accent);
  --el-color-primary-light-3: #93C5FD;
  --el-color-primary-dark-2: var(--theme-accent-hover);
  --el-text-color-primary: var(--theme-text);
  --el-text-color-regular: var(--theme-text-secondary);
  --el-text-color-secondary: #6B7280;
  --el-bg-color: var(--theme-bg);
  --el-bg-color-page: var(--theme-page-bg);
  --el-bg-color-overlay: var(--theme-card-bg);
  --el-border-color: var(--theme-border);
  --el-border-color-light: var(--theme-border-light);
  --el-fill-color-blank: var(--theme-card-bg);
  --tcm-ambient-gradient: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.03) 0%, transparent 70%);
}

[data-theme="dark-future"] {
  --theme-bg: #050505;
  --theme-page-bg: #0a0a0a;
  --theme-card-bg: rgba(15, 15, 15, 0.6);
  --theme-text: #f3f4f6;
  --theme-text-secondary: #d1d5db;
  --theme-border: rgba(255, 255, 255, 0.08);
  --theme-border-light: rgba(255, 255, 255, 0.04);
  --theme-accent: #10B981;
  --theme-accent-rgb: 16, 185, 129;
  --theme-accent-hover: #059669;
  --theme-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  --theme-overlay: rgba(20, 20, 20, 0.7);

  /* Element Plus Overrides for Dark Future */
  --el-color-primary: var(--theme-accent);
  --el-color-primary-light-3: #34D399;
  --el-color-primary-dark-2: var(--theme-accent-hover);
  --el-text-color-primary: var(--theme-text);
  --el-text-color-regular: var(--theme-text-secondary);
  --el-text-color-secondary: #9ca3af;
  --el-bg-color: var(--theme-bg);
  --el-bg-color-page: var(--theme-page-bg);
  --el-bg-color-overlay: var(--theme-card-bg);
  --el-border-color: var(--theme-border);
  --el-border-color-light: var(--theme-border-light);
  --el-fill-color-blank: var(--theme-card-bg);
  --tcm-ambient-gradient: radial-gradient(circle at 50% 0%, rgba(16, 185, 129, 0.05) 0%, transparent 70%);
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  background-color: var(--theme-bg);
  color: var(--theme-text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  transition: background-color 0.3s ease, color 0.3s ease;
}

#app {
  width: 100%;
  height: 100vh;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--theme-border);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--theme-text-secondary);
}

/* Override Element Plus specific defaults for Modern AI/Bento UI Feel */
.el-menu {
  border-right: none !important;
  background-color: transparent !important;
}
.el-popper {
  background-color: var(--theme-card-bg) !important;
  backdrop-filter: blur(16px) !important;
  border: 1px solid var(--theme-border-light) !important;
  border-radius: 24px !important;
  box-shadow: var(--theme-shadow) !important;
}

/* Base Component Border Radius & Border Removals */
.el-button, .el-input__wrapper, .el-textarea__inner, .el-card, .el-dialog, .el-message-box, .el-select-dropdown, .el-dropdown-menu {
  border-radius: 24px !important;
}

.el-card {
  border: 1px solid var(--theme-border-light) !important;
  background: var(--theme-card-bg) !important;
  backdrop-filter: blur(20px) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.04) !important;
  overflow: visible !important;
}

.el-button {
  border: none !important;
  font-weight: 600 !important;
  padding: 12px 24px !important;
  height: auto !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08) !important;
}
.el-button--primary {
  background: linear-gradient(135deg, var(--theme-accent), var(--theme-accent-hover)) !important;
  color: #fff !important;
}

.el-input__wrapper, .el-textarea__inner {
  box-shadow: none !important;
  border: 1px solid var(--theme-border-light) !important;
  background: var(--theme-page-bg) !important;
  padding: 12px 20px !important;
  transition: all 0.3s ease !important;
}
.el-input__wrapper:hover, .el-textarea__inner:hover, .el-input__wrapper.is-focus, .el-textarea__inner:focus {
  border-color: var(--theme-accent) !important;
  background: var(--theme-card-bg) !important;
  box-shadow: 0 0 0 4px rgba(var(--theme-accent-rgb), 0.1) !important;
}

.el-dialog, .el-message-box {
  background: var(--theme-card-bg) !important;
  backdrop-filter: blur(24px) !important;
  border: 1px solid var(--theme-border-light) !important;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.1) !important;
  border-radius: 32px !important;
  overflow: hidden;
}
.el-dialog__header, .el-message-box__header {
  padding: 24px 32px 16px !important;
  border-bottom: none !important;
  margin-right: 0 !important;
}
.el-dialog__body, .el-message-box__content {
  padding: 16px 32px 32px !important;
}
.el-dialog__footer, .el-message-box__btns {
  padding: 16px 32px 24px !important;
  border-top: 1px solid var(--theme-border-light) !important;
  background: var(--theme-page-bg) !important;
}

/* Glassmorphism utility */
.glass-panel {
  background: var(--theme-card-bg) !important;
  backdrop-filter: blur(20px) !important;
  border: 1px solid var(--theme-border-light) !important;
  border-radius: 32px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.04) !important;
}
</style>