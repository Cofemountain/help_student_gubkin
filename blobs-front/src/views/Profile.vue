<template>
  <div class="profile-page">
    <!-- Шапка профиля -->
    <header class="profile-header">
      <div class="avatar-circle">
        <img v-if="auth.userAvatar" :src="auth.userAvatar" :alt="auth.userName" class="profile-real-avatar" />
        <span v-else class="profile-initials">{{ auth.userInitials }}</span>
      </div>
      <div class="profile-meta">
        <div class="name-row">
          <h1>{{ auth.userFullName }}</h1>
        </div>
        <p v-if="auth.userUsername" class="user-handle">{{ auth.userUsername }}</p>
        <p v-else class="user-handle">ID пользователя: {{ auth.userId }}</p>
        <div class="tags-row">
          <span class="role-badge" :class="auth.role">
            {{ auth.role === 'teacher' ? 'Преподаватель (Наставник)' : 'Обучающийся (Ученик)' }}
          </span>
          <span class="title-chip">
            {{ auth.currentTitle.fullTitle }}
          </span>
        </div>
      </div>
    </header>

    <!-- Карточка звания и ачивок -->
    <section class="card achievements-summary-card">
      <div class="ach-summary-top">
        <div class="ach-text">
          <h2>{{ auth.currentTitle.fullTitle }}</h2>
          <p class="xp-val">Накопленный рейтинг: <strong>{{ auth.xp }} XP</strong></p>
        </div>
        <router-link to="/achievements" class="ach-pill-btn">
          <span class="ach-icon">🏆</span>
          <span>Достижения</span>
        </router-link>
      </div>

      <div class="progress-box" v-if="auth.currentTitle.nextTitle">
        <div class="progress-labels">
          <span>До уровня «{{ auth.currentTitle.nextTitle }}»</span>
          <span>{{ auth.currentTitle.xpToNext }} XP</span>
        </div>
        <div class="track">
          <div class="bar" :style="{ width: `${auth.currentTitle.progress}%` }"></div>
        </div>
      </div>
    </section>

    <!-- Переключение роли (Сегментированный переключатель) -->
    <section class="card role-card">
      <div class="role-card-header">
        <h2>Режим личного кабинета</h2>
        <span class="active-mode-label" :class="auth.role">
          {{ auth.role === 'teacher' ? '👨‍🏫 Кабинет преподавателя' : '🎓 Кабинет обучающегося' }}
        </span>
      </div>
      <p class="hint">Переключение между рабочими профилями обучающегося и преподавателя:</p>
      
      <div class="segmented-role-toggle">
        <button
          type="button"
          class="seg-btn"
          :class="{ active: auth.role === 'student' }"
          @click="changeRole('student')"
        >
          <span class="seg-icon">🎓</span>
          <span class="seg-text">Обучающийся</span>
        </button>
        <button
          type="button"
          class="seg-btn"
          :class="{ active: auth.role === 'teacher' }"
          @click="changeRole('teacher')"
        >
          <span class="seg-icon">👨‍🏫</span>
          <span class="seg-text">Преподаватель</span>
        </button>
      </div>

      <div class="role-info-banner" :class="auth.role">
        <p v-if="auth.role === 'student'">
          💡 <strong>Профиль обучающегося:</strong> самостоятельное решение экзаменационных заданий в открытом банке, проверка правильности ответов и оформление заявок на экспертную консультацию.
        </p>
        <p v-else>
          💡 <strong>Профиль преподавателя:</strong> методическая экспертиза решений обучающихся, проведение видеоконсультаций в Яндекс Телемосте и выдача индивидуальных заданий формата ОГЭ.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

function changeRole(newRole) {
  auth.switchRole(newRole)
}
</script>

<style scoped>
.profile-page {
  max-width: 650px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) 0;
}

.avatar-circle {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
  border: 2.5px solid #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.profile-real-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.profile-initials {
  color: #ffffff;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.5px;
}

.name-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.name-row h1 {
  margin: 0;
  font-size: 20px;
}

.user-handle {
  margin: 2px 0 var(--space-2);
  font-size: 13px;
  color: var(--text-muted);
}

.tags-row {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.role-badge {
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
}
.role-badge.student {
  background: #e6f4ea;
  color: #137333;
}
.role-badge.teacher {
  background: #e8f0fe;
  color: #1a73e8;
}

.title-chip {
  background: #fef3c7;
  color: #92400e;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
}

.card {
  background: #fff;
  border-radius: var(--radius-lg);
  border: 1px solid #e6e1d6;
  padding: var(--space-5);
}
.card h2 {
  margin: 0 0 var(--space-3);
  font-size: 16px;
}

.ach-summary-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: var(--space-3);
}

.ach-text h2 {
  margin: 0 0 4px;
}

.xp-val {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
}
.xp-val strong {
  color: var(--ink);
}

.ach-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #f8fafc;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  text-decoration: none;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.ach-pill-btn:active {
  background: #eff6ff;
  border-color: #bfdbfe;
  transform: scale(0.97);
}
.ach-pill-btn .ach-icon {
  font-size: 14px;
  line-height: 1;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.track {
  width: 100%;
  height: 8px;
  background: var(--surface);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.bar {
  height: 100%;
  background: var(--primary);
  border-radius: var(--radius-pill);
  transition: width 0.3s;
}

.role-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.role-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.role-card-header h2 {
  margin: 0;
  font-size: 16px;
}

.active-mode-label {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: var(--radius-pill);
}
.active-mode-label.student {
  background: #e6f4ea;
  color: #137333;
}
.active-mode-label.teacher {
  background: #e8f0fe;
  color: #1a73e8;
}

.segmented-role-toggle {
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: #f1f5f9;
  padding: 4px;
  border-radius: var(--radius-pill);
  gap: 4px;
  border: 1px solid #e2e8f0;
}

.seg-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 14px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  -webkit-tap-highlight-color: transparent;
}

.seg-btn.active {
  background: #ffffff;
  color: var(--ink);
  font-weight: 700;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
}

.seg-icon {
  font-size: 16px;
  line-height: 1;
}

.role-info-banner {
  padding: 12px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.45;
  background: #f8fafc;
  border-left: 3px solid #cbd5e1;
}
.role-info-banner.student {
  border-left-color: #f0a875;
  background: #fff8f3;
}
.role-info-banner.teacher {
  border-left-color: #3b82f6;
  background: #f0f7ff;
}
.role-info-banner p {
  margin: 0;
  color: #334155;
}

.hint {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.4;
}
</style>
