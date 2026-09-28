<template>
  <div style="padding: 20px;">
    <h2>Кнопки</h2>
    <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:20px;">
      <BaseButton variant="primary" size="sm">Small Primary</BaseButton>
      <BaseButton variant="primary" size="md">Medium Primary</BaseButton>
      <BaseButton variant="secondary" size="lg">Large Secondary</BaseButton>
      <BaseButton variant="outline">Outline</BaseButton>
      <BaseButton variant="danger">Danger</BaseButton>
      <BaseButton disabled>Disabled</BaseButton>
    </div>

    <h2>Чипсы (Фильтры)</h2>
    <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:20px;">
      <BaseChip label="Все" :is-active="true" />
      <BaseChip label="Математика" :is-active="false" />
      <BaseChip label="Физика" :is-active="false" />
      <BaseChip label="Информатика" :is-active="false" />
      <BaseChip label="Русский язык" :is-active="false" />
    </div>

    <p style="color:#888; margin-top:20px;">
      Попробуй поменять props у BaseButton в коде выше (например, add hover эффекты или изменить цвета в tokens.css) и смотри, как меняется этот экран.
    </p>
  </div>
</template>

<script setup>
import BaseButton from '../components/BaseButton.vue'
import BaseChip from '../components/BaseChip.vue'
</script>