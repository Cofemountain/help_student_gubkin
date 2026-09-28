<template>
  <button
    class="chip"
    :class="{ active: isActive }"
    @click="$emit('toggle')"
  >
    {{ label }}
  </button>
</template>

<script setup>
defineProps({
  label: String,
  isActive: Boolean
})
defineEmits(['toggle'])
</script>

<style scoped>
.chip {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-pill);
  border: 1px solid #ddd;
  background: white;
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.chip.active {
  background: var(--primary);
  border-color: var(--primary);
  color: var(--ink);
  font-weight: 600;
}

.chip:hover:not(.active) {
  border-color: var(--text-muted);
  color: var(--text);
}
</style>