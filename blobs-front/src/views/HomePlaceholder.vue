<template>
  <!-- Если роли нет (не залогинен) - показываем загрузку -->
  <div v-if="!auth.role" class="loading-screen">
    <p>Загрузка профиля...</p>
  </div>

  <!-- Если роль ученик - рендерим StudentHome -->
  <StudentHome v-else-if="auth.role === 'student'" />

  <!-- Если роль учитель - рендерим TeacherDashboard -->
  <TeacherDashboard v-else-if="auth.role === 'teacher'" />

  <!-- На случай ошибки данных -->
  <div v-else class="error-screen">
    <p>Ошибка: неизвестная роль.</p>
  </div>
</template>

<script setup>
// Импортируем компоненты напрямую
import StudentHome from './StudentHome.vue'
import TeacherDashboard from './TeacherDashboard.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
// Никаких computed здесь быть НЕ ДОЛЖНО!
</script>

<style scoped>
.loading-screen, .error-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 50vh;
  color: var(--text-muted);
}
</style>