<template>
  <div class="student-home">
    <!-- Шапка ученика -->
    <header class="student-hero">
      <div class="hero-top-row">
        <span class="oge-pill" :style="{ background: auth.ogeLevel.color }">
          ОГЭ: {{ auth.ogeLevel.title }}
        </span>
        <router-link to="/achievements" class="hero-xp-chip">
          {{ auth.currentTitle.badge }} {{ auth.xp }} XP
        </router-link>
      </div>

      <div class="hero-main">
        <h1>Здравствуйте, {{ auth.userFullName }}!</h1>
        <p class="subtitle">
          Квалификационный уровень: <strong>{{ auth.currentTitle.fullTitle }}</strong>
        </p>

        <!-- Прогресс до следующего звания -->
        <div class="hero-progress" v-if="auth.currentTitle.nextTitle">
          <div class="progress-labels">
            <span>До уровня «{{ auth.currentTitle.nextTitle }}»</span>
            <span>{{ auth.currentTitle.xpToNext }} XP</span>
          </div>
          <div class="track">
            <div class="bar" :style="{ width: `${auth.currentTitle.progress}%` }"></div>
          </div>
        </div>
      </div>

      <div class="hero-actions">
        <router-link to="/create-request" class="cta-button">
          Сформировать заявку на консультацию
        </router-link>
      </div>
    </header>

    <!-- Секция активных заявок ученика -->
    <section class="requests-section">
      <div class="section-header">
        <h2>Реестр поданных заявок</h2>
        <router-link v-if="myRequests.length > 0" to="/requests" class="section-more-link">
          Полный реестр →
        </router-link>
      </div>

      <div v-if="loadingRequests" class="loader">
        <p>Загрузка данных заявок...</p>
      </div>

      <div v-else-if="myRequests.length === 0" class="empty-state">
        <span class="empty-icon">📝</span>
        <p>В настоящее время активные заявки отсутствуют.</p>
        <p class="hint">
          При возникновении затруднений с заданием или темой оформите заявку — преподаватель предоставит письменный разбор или проведет видеоконсультацию в Яндекс Телемосте.
        </p>
        <router-link to="/create-request" class="empty-cta-btn">
          ➕ Сформировать заявку преподавателю
        </router-link>
      </div>

      <div v-else class="cards-list">
        <RequestCard
          v-for="req in visibleRequests"
          :key="req.id"
          :request="req"
          viewer-role="student"
          @updated="loadStudentTasks"
        />
        <div v-if="myRequests.length > 4" class="more-requests-footer">
          <router-link to="/requests" class="more-requests-btn">
            Смотреть все заявки ({{ myRequests.length }}) →
          </router-link>
        </div>
      </div>
    </section>

    <!-- Виджет практики и Базы решений из Банка задач -->
    <section class="practice-widget-card">
      <div class="pw-header">
        <span class="pw-badge">💡 База решений и Практикум</span>
        <span class="pw-xp-pill">+15 XP в тесте</span>
      </div>
      <div class="pw-content">
        <h3 class="pw-title">Банк задач и база разборов</h3>
        <p class="pw-desc">
          Смотрите готовые разборы реальных задач от преподавателей с формулами и чертежами или тренируйтесь на типовых заданиях ОГЭ с автоматической проверкой ответа.
        </p>
      </div>
      <div class="pw-action-wrap">
        <router-link to="/bank" class="pw-button">
          <span>📚 Открыть Банк задач и решений</span>
          <span class="pw-arrow">→</span>
        </router-link>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import RequestCard from '../components/RequestCard.vue'
import { api } from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const loadingRequests = ref(true)
const myRequests = ref([])
const visibleRequests = computed(() => {
  return myRequests.value.slice(0, 4)
})

async function loadStudentTasks() {
  loadingRequests.value = true
  try {
    const data = await api.getMyTasks(auth.telegramId || auth.userId, 'student')
    myRequests.value = data
      .map((t) => ({
        id: t.id,
        subject: t.topic?.block || 'Физика ОГЭ',
        block: t.topic?.block || 'MECHANICS',
        grade: t.grade || t.topic?.grade || 9,
        title: t.topic?.title || 'Заявка по физике',
        description: t.question,
        photoUrl: t.photo_url || '',
        status: t.status.toLowerCase(),
        scheduledTime: t.scheduled_time,
        studentName: auth.userName,
        requestType: t.request_type || 'TASK',
        telemostUrl: t.telemost_url || '',
        teacherResponse: t.teacher_response || '',
        homework: t.homework || null,
        createdAt: t.created_at,
        created_at: t.created_at,
      }))
      .sort((a, b) => (b.id || 0) - (a.id || 0))
  } catch (error) {
    console.warn('Не удалось загрузить заявки ученика:', error)
  } finally {
    loadingRequests.value = false
  }
}

onMounted(() => {
  loadStudentTasks()
})
</script>

<style scoped>
.student-home {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding-bottom: 110px;
}

.student-hero {
  background: linear-gradient(135deg, var(--ink) 0%, #1e293b 100%);
  color: white;
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.hero-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.oge-pill {
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  letter-spacing: 0.02em;
}

.hero-xp-chip {
  background: rgba(255, 255, 255, 0.12);
  color: var(--primary);
  text-decoration: none;
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
}

.hero-main h1 {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.subtitle {
  margin: 0 0 var(--space-2);
  font-size: 13px;
  opacity: 0.9;
}
.subtitle strong {
  color: var(--primary);
}

.hero-progress {
  background: rgba(255, 255, 255, 0.08);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  margin-top: 4px;
}

.progress-labels {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  opacity: 0.85;
  margin-bottom: 5px;
}

.track {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.bar {
  height: 100%;
  background: var(--primary);
  border-radius: var(--radius-pill);
  transition: width 0.3s;
}

.hero-actions {
  margin-top: 10px;
  display: flex;
  justify-content: center;
  width: 100%;
}

.cta-button {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  background: var(--primary);
  color: var(--ink);
  padding: 10px 20px;
  border-radius: var(--radius-pill);
  font-weight: 700;
  font-size: 14px;
  text-decoration: none;
  box-shadow: 0 4px 14px rgba(240, 168, 117, 0.3);
  transition: transform 0.15s ease, background 0.15s ease;
}
.cta-button:active {
  background: var(--primary-press);
  transform: scale(0.98);
}

/* Секция заявок */
.requests-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--ink);
}

.section-more-link {
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
  text-decoration: none;
}
.section-more-link:hover {
  text-decoration: underline;
}

.cards-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.loader {
  text-align: center;
  padding: var(--space-4);
  color: var(--text-muted);
  font-size: 13px;
}

.empty-state {
  background: #ffffff;
  border: 1px dashed #cbd5e1;
  border-radius: var(--radius-md);
  padding: var(--space-5) var(--space-4);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}

.empty-icon {
  font-size: 36px;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.empty-state .hint {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: normal;
  max-width: 340px;
  line-height: 1.4;
}

.empty-cta-btn {
  margin-top: var(--space-2);
  background: #f1f5f9;
  color: var(--ink);
  font-size: 12px;
  font-weight: 700;
  padding: 8px 14px;
  border-radius: var(--radius-pill);
  text-decoration: none;
  transition: background 0.15s ease;
}
.empty-cta-btn:hover {
  background: #e2e8f0;
}

/* Виджет практики ОГЭ */
.practice-widget-card {
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  margin-top: 4px;
  margin-bottom: 24px;
  box-sizing: border-box;
  width: 100%;
}

.pw-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.pw-badge {
  font-size: 11px;
  font-weight: 700;
  color: #0369a1;
  background: #e0f2fe;
  padding: 3px 10px;
  border-radius: 100px;
  white-space: nowrap;
}

.pw-xp-pill {
  font-size: 11px;
  font-weight: 700;
  color: #15803d;
  background: #dcfce7;
  padding: 3px 9px;
  border-radius: 100px;
  white-space: nowrap;
}

.pw-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.pw-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.35;
}

.pw-desc {
  margin: 0;
  font-size: 13px;
  color: #475569;
  line-height: 1.45;
}

.pw-action-wrap {
  width: 100%;
}

.pw-button {
  display: flex;
  width: 100%;
  box-sizing: border-box;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #0f172a;
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
  padding: 12px 16px;
  border-radius: 12px;
  text-decoration: none;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.18);
  transition: all 0.15s ease;
}
.pw-button:hover {
  background: #1e293b;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
  transform: translateY(-1px);
}
.pw-button:active {
  transform: scale(0.98);
}
.pw-arrow {
  font-size: 15px;
  transition: transform 0.15s;
}
.pw-button:hover .pw-arrow {
  transform: translateX(3px);
}

.more-requests-footer {
  display: flex;
  justify-content: center;
  margin-top: var(--space-2);
}

.more-requests-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 18px;
  background: var(--surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--primary);
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  transition: all 0.2s ease;
}

.more-requests-btn:hover {
  background: var(--surface-hover);
  border-color: var(--primary);
}
</style>