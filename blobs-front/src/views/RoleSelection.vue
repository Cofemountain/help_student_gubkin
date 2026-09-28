<template>
  <div class="onboarding-canvas">
    <div class="portal-card">
      <!-- Верхняя шапка платформы -->
      <header class="portal-header">
        <div class="institution-tag">
          <span class="emblem">🏛</span>
          <span>Образовательная платформа • ОГЭ по физике (9 класс)</span>
        </div>

        <!-- Карточка профиля пользователя из МАКС -->
        <div class="user-id-card">
          <div class="avatar-wrap">
            <img
              v-if="auth.userAvatar"
              :src="auth.userAvatar"
              :alt="auth.userName"
              class="real-avatar"
            />
            <div v-else class="initials-avatar">
              {{ auth.userInitials }}
            </div>
            <span class="auth-dot" title="Подключено к МАКС"></span>
          </div>

          <div class="user-meta">
            <h2>Здравствуйте, {{ auth.userFullName }}!</h2>
            <div class="meta-sub">
              <span class="tag-status">Профиль МАКС подтверждён</span>
            </div>
          </div>
        </div>

        <p class="intro-description">
          Выберите ваш рабочий профиль для перехода в личный кабинет:
        </p>
      </header>

      <!-- Выбор роли: Обучающийся или Преподаватель -->
      <div class="role-grid">
        <!-- Карточка Обучающегося -->
        <div
          class="role-card"
          :class="{ selected: selectedRole === 'student' }"
          @click="selectedRole = 'student'"
        >
          <div class="card-top">
            <div class="role-emblem student">🎓</div>
            <div class="selector-check">
              <span v-if="selectedRole === 'student'">✓</span>
            </div>
          </div>
          <h3>Кабинет обучающегося</h3>
          <p class="role-summary">
            Помощь по физике для 7, 8 и 9 классов, разбор сложных тем, домашних заданий и подготовка к ОГЭ.
          </p>
          <ul class="role-perks">
            <li>
              <span class="perk-bullet">📝</span>
              <span>Формирование заявок на разбор сложных заданий</span>
            </li>
            <li>
              <span class="perk-bullet">📹</span>
              <span>Индивидуальные видеоконсультации в Яндекс Телемосте</span>
            </li>
            <li>
              <span class="perk-bullet">📚</span>
              <span>Практикум в открытом банке задач с автопроверкой</span>
            </li>
          </ul>
        </div>

        <!-- Карточка Преподавателя -->
        <div
          class="role-card"
          :class="{ selected: selectedRole === 'teacher' }"
          @click="selectedRole = 'teacher'"
        >
          <div class="card-top">
            <div class="role-emblem teacher">👨‍🏫</div>
            <div class="selector-check">
              <span v-if="selectedRole === 'teacher'">✓</span>
            </div>
          </div>
          <h3>Кабинет преподавателя</h3>
          <p class="role-summary">
            Методическая поддержка учащихся, экспертная оценка решений и контроль выполнения заданий.
          </p>
          <ul class="role-perks">
            <li>
              <span class="perk-bullet">📋</span>
              <span>Единый реестр входящих заявок от обучающихся</span>
            </li>
            <li>
              <span class="perk-bullet">🔒</span>
              <span>Закрытый банк заданий для выдачи домашних работ</span>
            </li>
            <li>
              <span class="perk-bullet">🏆</span>
              <span>Квалификационная шкала званий и рейтинг наставника</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Квалификационная шкала званий для выбранной роли -->
      <section class="qualifications-panel">
        <div class="panel-header">
          <span class="panel-icon">🎖</span>
          <h4>Квалификационная шкала: {{ selectedRole === 'teacher' ? 'Преподаватель (Наставник)' : 'Обучающийся (Ученик)' }}</h4>
        </div>
        <div class="tiers-row">
          <div
            v-for="(t, idx) in previewTitles"
            :key="idx"
            class="tier-badge"
            :class="{ active: idx === 0 }"
          >
            <span class="t-badge">{{ t.badge }}</span>
            <div class="t-text">
              <span class="t-title">{{ t.name }}</span>
              <span class="t-range">{{ t.xp }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Кнопка перехода в кабинет -->
      <footer class="portal-footer">
        <BaseButton
          variant="primary"
          size="lg"
          rounded
          class="submit-role-btn"
          @click="confirmRole"
        >
          Войти в кабинет {{ selectedRole === 'teacher' ? 'преподавателя' : 'обучающегося' }}
        </BaseButton>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import BaseButton from '../components/BaseButton.vue'

const router = useRouter()
const auth = useAuthStore()

const selectedRole = ref(auth.role || 'student')

const previewTitles = computed(() => {
  if (selectedRole.value === 'teacher') {
    return [
      { badge: '🥉', name: 'Наставник-стажёр', xp: '0–149 XP' },
      { badge: '🥈', name: 'Опытный наставник', xp: '150–499 XP' },
      { badge: '🥇', name: 'Мастер физики', xp: '500–999 XP' },
      { badge: '🏆', name: 'Заслуженный преподаватель', xp: '1000+ XP' },
    ]
  } else {
    return [
      { badge: '🥉', name: 'Юный наблюдатель', xp: '0–149 XP' },
      { badge: '🥈', name: 'Знаток законов физики', xp: '150–499 XP' },
      { badge: '🥇', name: 'Мастер физики', xp: '500+ XP' },
    ]
  }
})

function confirmRole() {
  auth.selectRole(selectedRole.value)
  router.push('/')
}
</script>

<style scoped>
.onboarding-canvas {
  min-height: 100vh;
  min-height: 100dvh;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 12px 24px;
  background: radial-gradient(circle at 50% 10%, #1e293b 0%, #0f172a 100%);
  font-family: var(--font, system-ui, -apple-system, sans-serif);
  width: 100%;
}

.portal-card {
  width: 100%;
  max-width: 520px;
  background: #ffffff;
  border-radius: var(--radius-lg, 20px);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
  padding: 20px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-sizing: border-box;
  margin: auto 0;
}

.portal-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Официальный значок платформы */
.institution-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #334155;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 100px;
  align-self: flex-start;
  letter-spacing: 0.01em;
}

.emblem {
  font-size: 13px;
}

/* Блок профиля пользователя */
.user-id-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 10px 14px;
}

.avatar-wrap {
  position: relative;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.real-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #3b82f6;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.2);
}

.initials-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #1e293b 0%, #3b82f6 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.15);
}

.auth-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: #10b981;
  border: 2px solid #ffffff;
}

.user-meta h2 {
  margin: 0;
  font-size: 19px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.meta-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.tag-handle {
  font-size: 13px;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 6px;
}

.tag-status {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.intro-description {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: #475569;
}

/* Сетка выбора ролей */
.role-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}

@media (min-width: 540px) {
  .role-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.role-card {
  border: 2px solid #e2e8f0;
  border-radius: 14px;
  padding: 12px 14px;
  cursor: pointer;
  background: #ffffff;
  transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
}

.role-card:hover {
  border-color: #94a3b8;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
}

.role-card.selected {
  border-color: #2563eb;
  background: #f8faff;
  box-shadow: 0 8px 20px rgba(37, 99, 235, 0.12);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.role-emblem {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.role-emblem.student {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.role-emblem.teacher {
  background: #fef3c7;
  border: 1px solid #fde68a;
}

.selector-check {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 12px;
  font-weight: 800;
  transition: all 0.2s;
}

.role-card.selected .selector-check {
  background: #2563eb;
  border-color: #2563eb;
}

.role-card h3 {
  margin: 0 0 4px;
  font-size: 15.5px;
  font-weight: 800;
  color: #0f172a;
}

.role-summary {
  margin: 0 0 8px;
  font-size: 12px;
  line-height: 1.4;
  color: #64748b;
}

.role-perks {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11.5px;
  color: #334155;
  line-height: 1.35;
}

.role-perks li {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.perk-bullet {
  font-size: 12px;
  flex-shrink: 0;
  line-height: 1.2;
}

/* Панель званий */
.qualifications-panel {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 12px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.panel-icon {
  font-size: 13px;
}

.panel-header h4 {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
}

.tiers-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(115px, 1fr));
  gap: 6px;
}

.tier-badge {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 6px 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tier-badge.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.t-badge {
  font-size: 16px;
}

.t-text {
  display: flex;
  flex-direction: column;
}

.t-title {
  font-size: 11px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.t-range {
  font-size: 10px;
  color: #64748b;
}

/* Кнопка подтверждения */
.portal-footer {
  margin-top: 2px;
}

.submit-role-btn {
  width: 100%;
  font-size: 15px;
  font-weight: 700;
  padding: 13px 18px;
  box-shadow: 0 4px 14px rgba(240, 168, 117, 0.35);
}
</style>
