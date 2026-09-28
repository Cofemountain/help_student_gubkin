<template>
  <label class="field">
    <span class="label">{{ label }}</span>
    <input
      class="input"
      :type="type"
      :placeholder="placeholder"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <span v-if="error" class="err">{{ error }}</span>
  </label>
</template>

<script setup>
defineProps({
  label: String,
  type: { type: String, default: 'text' },   // text | password | email
  placeholder: String,
  modelValue: [String, Number],              // текущее значение поля
  error: String,                             // текст ошибки (пусто = нет ошибки)
})
defineEmits(['update:modelValue'])           // v-model будет работать благодаря этому имени
</script>

<style scoped>
.field { display:block; margin-bottom: var(--space-4); }
.label { display:block; font-size:14px; font-weight:600; color: var(--text-muted); margin-bottom: var(--space-2); }
.input {
  width:100%; box-sizing:border-box;
  padding: var(--space-3) var(--space-4);
  border:1px solid #d8d3c8; border-radius: var(--radius-md);
  font: inherit; color: var(--text); background:#fff;
}
.input:focus { outline:none; border-color: var(--primary); box-shadow: 0 0 0 3px rgba(240,168,117,.25); }
.err { display:block; margin-top: var(--space-1); font-size:13px; color: var(--danger); }
</style>