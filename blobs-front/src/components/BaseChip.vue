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
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border-radius: 100px;
  border: 1.5px solid #e2e8f0;
  background: #ffffff;
  color: #475569;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.chip.active {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #1d4ed8;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.2);
}

.chip:hover:not(.active) {
  border-color: #cbd5e1;
  background: #f8fafc;
  color: #0f172a;
}
</style>