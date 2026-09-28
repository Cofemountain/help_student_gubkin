<template>
  <div class="toast-wrapper" aria-live="polite">
    <transition-group name="toast-slide" tag="div" class="toast-list">
      <div
        v-for="t in toast.toasts"
        :key="t.id"
        class="toast-item"
        :class="`toast-${t.type}`"
        @click="toast.remove(t.id)"
      >
        <div class="toast-icon">
          <span v-if="t.type === 'success'">✅</span>
          <span v-else-if="t.type === 'error'">❌</span>
          <span v-else-if="t.type === 'warning'">⚠️</span>
          <span v-else>ℹ️</span>
        </div>

        <div class="toast-body">
          <strong v-if="t.title" class="toast-title">{{ t.title }}</strong>
          <span class="toast-message">{{ t.message }}</span>
        </div>

        <button type="button" class="toast-close" @click.stop="toast.remove(t.id)" title="Закрыть">
          ✕
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useToastStore } from '../stores/toast'

const toast = useToastStore()
</script>

<style scoped>
.toast-wrapper {
  position: fixed;
  top: calc(14px + env(safe-area-inset-top, 0px));
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 440px;
  padding: 0 14px;
  box-sizing: border-box;
  z-index: 999999;
  pointer-events: none;
}

.toast-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.toast-item {
  pointer-events: auto;
  width: 100%;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.95);
  color: #ffffff;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28), 0 0 0 1px rgba(255, 255, 255, 0.12);
  cursor: pointer;
  user-select: none;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.toast-item:hover {
  transform: translateY(-1px);
}

.toast-icon {
  font-size: 18px;
  line-height: 1;
  flex-shrink: 0;
}

.toast-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 13px;
  font-weight: 700;
  color: #f8fafc;
}

.toast-message {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  color: #e2e8f0;
  word-break: break-word;
}

.toast-close {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 14px;
  padding: 4px;
  cursor: pointer;
  line-height: 1;
  border-radius: 6px;
  flex-shrink: 0;
  transition: color 0.15s;
}

.toast-close:hover {
  color: #ffffff;
}

/* Цветовые акценты левой границы */
.toast-success {
  border-left: 4px solid #10b981;
}

.toast-error {
  border-left: 4px solid #ef4444;
}

.toast-warning {
  border-left: 4px solid #f59e0b;
}

.toast-info {
  border-left: 4px solid #3b82f6;
}

/* Анимации появления и скрытия */
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-slide-enter-from {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.toast-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.95);
}
</style>
