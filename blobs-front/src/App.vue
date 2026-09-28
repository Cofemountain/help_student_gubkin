<template>
  <div class="mobile-container">
    <!-- Всплывающие уведомления (Toast) -->
    <ToastContainer />

    <div class="shell" :class="{ 'is-public': isPublic }">

      <!-- Мобильная шапка -->
      <header v-if="!isPublic" class="topbar">
        <div class="topbar-inner">
          <div class="topbar-brand">
            <span class="brand-title">Помощь с физикой</span>
          </div>

          <div class="topbar-user" v-if="auth.role">
            <router-link to="/achievements" class="xp-badge" title="Ваши баллы и звание">
              <span class="badge-icon">{{ auth.currentTitle.badge }}</span>
              <span class="badge-text">{{ auth.xp }} XP</span>
            </router-link>

            <router-link to="/profile" class="user-avatar" :title="auth.userFullName">
              <img v-if="auth.userAvatar" :src="auth.userAvatar" :alt="auth.userName" class="topbar-avatar-img" />
              <span v-else>{{ auth.userInitials }}</span>
            </router-link>
          </div>
        </div>
      </header>

      <!-- Основной скроллируемый контент -->
      <main class="content">
        <router-view />
      </main>

      <!-- Мобильный нижний бар навигации (Всегда активен) -->
      <nav v-if="!isPublic" class="tabbar">
        <div class="tabbar-inner">
          <router-link to="/" class="tab" active-class="is-active">
            <span class="tab-icon">🏠</span>
            <span class="tab-label">Главная</span>
          </router-link>
          <router-link to="/bank" class="tab" active-class="is-active">
            <span class="tab-icon">📚</span>
            <span class="tab-label">Банк</span>
          </router-link>
          <router-link to="/requests" class="tab" active-class="is-active">
            <span class="tab-icon">📋</span>
            <span class="tab-label">Заявки</span>
          </router-link>
          <router-link to="/achievements" class="tab" active-class="is-active">
            <span class="tab-icon">🏆</span>
            <span class="tab-label">Награды</span>
          </router-link>
          <router-link to="/profile" class="tab" active-class="is-active">
            <span class="tab-icon">👤</span>
            <span class="tab-label">Профиль</span>
          </router-link>
        </div>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import ToastContainer from './components/ToastContainer.vue'

const route = useRoute()
const auth = useAuthStore()

// Публичные экраны (вход, регистрация, онбординг) без навигации
const PUBLIC_ROUTES = ['/onboarding', '/login', '/register']
const isPublic = computed(() => PUBLIC_ROUTES.includes(route.path))
</script>

<style scoped>
/* Внешний фон-холст: на десктопе центрирует телефон, на смартфонах растягивается на 100% */
.mobile-container {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  justify-content: center;
  align-items: stretch;
  background: #f1f5f9;
  width: 100%;
}

@media (max-width: 640px) {
  .mobile-container {
    background: var(--bg);
  }
}

/* Оболочка телефона (строго мобильный формат) */
.shell {
  width: 100%;
  max-width: 440px;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 0 0 50px rgba(0, 0, 0, 0.08);
  overflow-x: hidden;
  margin: 0 auto;
  padding: 0;
}

@media (max-width: 640px) {
  .shell {
    max-width: 100%;
    box-shadow: none;
  }
}

.shell.is-public {
  background: radial-gradient(circle at 50% 10%, #1e293b 0%, #0f172a 100%);
  max-width: 600px;
  box-shadow: none;
}

.shell.is-public .content {
  padding: 0;
  padding-bottom: 0;
  display: flex;
  flex-direction: column;
}

/* Мобильная шапка (Header) */
.topbar {
  position: sticky;
  top: 0;
  z-index: 90;
  width: 100%;
  box-sizing: border-box;
  background: var(--ink);
  color: var(--text-on-ink);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0 var(--space-4);
}

.topbar-inner {
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
  min-height: calc(48px + env(safe-area-inset-top, 0px));
  padding-top: env(safe-area-inset-top, 0px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-sizing: border-box;
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.brand-title {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.topbar-user {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.xp-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.12);
  color: var(--primary);
  text-decoration: none;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: var(--radius-pill);
  transition: background 0.15s ease;
}

.xp-badge:active {
  background: rgba(255, 255, 255, 0.22);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #3b82f6;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  text-decoration: none;
  border: 1.5px solid rgba(255, 255, 255, 0.3);
  overflow: hidden;
}

.topbar-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Область контента */
.content {
  flex: 1;
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
  padding: var(--space-4);
  padding-bottom: calc(80px + env(safe-area-inset-bottom, 16px));
  box-sizing: border-box;
}

/* Мобильный нижний бар табов (Tabbar) - плотный непрозрачный фон, компактное расположение */
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 100;
  background: #ffffff;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 -4px 20px rgba(15, 23, 42, 0.07);
  padding-bottom: max(env(safe-area-inset-bottom, 0px), 8px);
  padding-top: 6px;
  box-sizing: border-box;
}

.tabbar-inner {
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
  display: flex;
  justify-content: space-around;
  align-items: center;
  box-sizing: border-box;
  padding: 0 4px;
}

.tab {
  flex: 1;
  max-width: 76px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  text-decoration: none;
  color: #64748b;
  font-size: 10.5px;
  font-weight: 600;
  padding: 4px 2px;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}

.tab-icon {
  font-size: 19px;
  line-height: 1;
  transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.tab-label {
  font-size: 10.5px;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.tab.is-active {
  color: #0f172a;
}

.tab.is-active .tab-icon {
  transform: scale(1.12);
}

.tab.is-active .tab-label {
  color: #ef7d34;
  font-weight: 700;
}
</style>