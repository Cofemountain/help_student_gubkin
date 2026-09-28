<template>
  <button
    class="btn"
    :class="[variant, size, { rounded }]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'primary' }, // primary, secondary, outline, danger
  size: { type: String, default: 'md' },         // sm, md, lg
  disabled: { type: Boolean, default: false },
  rounded: { type: Boolean, default: false }     // <-- НОВОЕ СВОЙСТВО
})
</script>

<style scoped>
.btn {
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-weight: 600;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  /* Базовое скругление для обычных размеров */
  border-radius: var(--radius-sm);
}

/* Размеры */
.sm { padding: var(--space-1) var(--space-3); font-size: 14px; height: 32px; }
.md { padding: var(--space-2) var(--space-4); font-size: 16px; height: 44px; border-radius: var(--radius-md); }
.lg { padding: var(--space-3) var(--space-5); font-size: 18px; height: 56px; border-radius: var(--radius-lg); } /* Добавили radius-lg */

/* Если включен флаг rounded — делаем полную таблетку */
.rounded {
  border-radius: var(--radius-pill);
}

/* Варианты цветов */
.primary { background: var(--primary); color: var(--ink); }
.primary:hover:not(:disabled) { filter: brightness(0.95); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(240, 168, 117, 0.3); }
.primary:active:not(:disabled) { transform: translateY(0); }

.secondary { background: var(--ink); color: white; }
.secondary:hover:not(:disabled) { opacity: 0.9; }

.outline { background: transparent; border: 2px solid var(--ink); color: var(--ink); }
.outline:hover:not(:disabled) { background: var(--surface); }

.danger { background: var(--danger); color: white; }

/* Состояние Disabled */
:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(1);
}
</style>