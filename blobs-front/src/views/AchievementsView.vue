<template>
  <div class="achievements-view">
    <!-- Шапка звания -->
    <header class="title-card">
      <div class="title-badge-large">
        {{ auth.currentTitle.badge }}
      </div>
      <div class="title-meta">
        <span class="role-chip">
          {{ auth.role === 'teacher' ? '👨‍🏫 Преподаватель (Наставник)' : '🎓 Обучающийся' }}
        </span>
        <h1>{{ auth.currentTitle.title }}</h1>
        <p class="xp-count">
          <strong>{{ auth.xp }}</strong> баллов рейтинга (XP)
        </p>
      </div>
    </header>

    <!-- Прогресс до следующего звания -->
    <section class="card progress-card" v-if="auth.currentTitle.nextTitle">
      <div class="progress-labels">
        <span>Следующая категория: <strong>{{ auth.currentTitle.nextTitle }}</strong></span>
        <span>Осталось <strong>{{ auth.currentTitle.xpToNext }} XP</strong></span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: `${auth.currentTitle.progress}%` }"></div>
      </div>
    </section>

    <!-- Прогноз оценки ОГЭ для ученика -->
    <section class="card oge-card" v-if="auth.role === 'student'">
      <div class="oge-left">
        <span class="oge-grade" :style="{ background: auth.ogeLevel.color }">
          {{ auth.ogeLevel.grade }}
        </span>
      </div>
      <div class="oge-right">
        <h3>Прогноз уровня подготовки: {{ auth.ogeLevel.title }}</h3>
        <p>Повышайте квалификационный рейтинг за решение экзаменационных задач и активное участие в консультациях.</p>
      </div>
    </section>

    <!-- Сетка ачивок -->
    <section class="achievements-section">
      <h2>🏆 Достижения и награды</h2>
      <div class="achievements-grid">
        <div
          v-for="ach in auth.achievements"
          :key="ach.id"
          class="ach-card"
          :class="{ unlocked: ach.unlocked }"
        >
          <div class="ach-icon">{{ ach.icon }}</div>
          <div class="ach-info">
            <div class="ach-top">
              <h3>{{ ach.title }}</h3>
              <span class="ach-reward">{{ ach.reward }}</span>
            </div>
            <p>{{ ach.description }}</p>
            <div class="ach-status">
              <span v-if="ach.unlocked" class="badge-unlocked">✓ Получено</span>
              <span v-else class="badge-locked">🔒 В процессе</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Тестовый блок начисления XP -->
    <section class="card test-actions">
      <h3>Тест геймификации</h3>
      <p class="hint">Быстро проверьте повышение звания и открытие ачивок:</p>
      <div class="test-btns">
        <BaseButton size="sm" variant="secondary" rounded @click="gainXp(50)">
          +50 XP (Разбор задачи)
        </BaseButton>
        <BaseButton size="sm" variant="secondary" rounded @click="gainXp(150)">
          +150 XP (Сложная часть)
        </BaseButton>
        <BaseButton size="sm" variant="primary" rounded @click="gainXp(300)">
          +300 XP (Бонус недели)
        </BaseButton>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
import BaseButton from '../components/BaseButton.vue'

const auth = useAuthStore()

function gainXp(amount) {
  auth.addXp(amount)
}
</script>

<style scoped>
.achievements-view {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.title-card {
  margin: calc(var(--space-4) * -1) calc(var(--space-4) * -1) 0 calc(var(--space-4) * -1);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  background: linear-gradient(135deg, var(--ink) 0%, #1e293b 100%);
  color: white;
  padding: var(--space-6) var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.title-badge-large {
  font-size: 64px;
  line-height: 1;
  background: rgba(255, 255, 255, 0.1);
  width: 90px;
  height: 90px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.role-chip {
  display: inline-block;
  background: rgba(255, 255, 255, 0.2);
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  margin-bottom: var(--space-1);
}

.title-meta h1 {
  margin: 0 0 var(--space-1);
  font-size: 24px;
}

.xp-count {
  margin: 0;
  font-size: 15px;
  opacity: 0.9;
}
.xp-count strong {
  color: var(--primary);
  font-size: 18px;
}

.card {
  background: #fff;
  border: 1px solid #e6e1d6;
  border-radius: var(--radius-md);
  padding: var(--space-5);
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: var(--space-2);
  color: var(--text);
}

.progress-track {
  width: 100%;
  height: 10px;
  background: var(--surface);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary) 0%, #f59e0b 100%);
  border-radius: var(--radius-pill);
  transition: width 0.4s ease;
}

.oge-card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  background: #f8fafc;
}

.oge-grade {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-md);
  color: white;
  font-size: 26px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.oge-right h3 {
  margin: 0 0 var(--space-1);
  font-size: 16px;
}
.oge-right p {
  margin: 0;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.4;
}

.achievements-section h2 {
  font-size: 18px;
  margin: 0 0 var(--space-4);
}

.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-3);
}

.ach-card {
  background: #fff;
  border: 1px solid #e6e1d6;
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  gap: var(--space-3);
  transition: all 0.2s;
  opacity: 0.65;
}

.ach-card.unlocked {
  opacity: 1;
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.ach-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.ach-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.ach-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ach-top h3 {
  margin: 0;
  font-size: 15px;
  color: var(--text);
}

.ach-reward {
  font-size: 11px;
  font-weight: 700;
  background: #fef3c7;
  color: #92400e;
  padding: 2px 6px;
  border-radius: var(--radius-pill);
}

.ach-info p {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.3;
}

.ach-status {
  margin-top: 4px;
}

.badge-unlocked {
  font-size: 11px;
  color: #10b981;
  font-weight: 700;
}

.badge-locked {
  font-size: 11px;
  color: var(--text-muted);
}

.test-actions h3 {
  margin: 0 0 var(--space-1);
  font-size: 15px;
}

.test-actions .hint {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 var(--space-3);
}

.test-btns {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}
</style>
