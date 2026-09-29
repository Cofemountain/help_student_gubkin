<template>
  <div class="teacher-dashboard">
    <!-- Шапка преподавателя -->
    <header class="teacher-hero">
      <div class="hero-top-row">
        <span class="role-badge">👨‍🏫 Преподаватель физики</span>
        <router-link to="/achievements" class="hero-xp-chip">
          {{ auth.currentTitle.badge }} {{ auth.xp }} XP →
        </router-link>
      </div>

      <div class="hero-main">
        <h1>Здравствуйте, {{ auth.userFullName }}!</h1>
        <p class="subtitle">
          Квалификационная категория: <strong>{{ auth.currentTitle.fullTitle }}</strong>
        </p>

        <!-- Прогресс до следующего звания -->
        <div class="hero-progress" v-if="auth.currentTitle.nextTitle">
          <div class="progress-labels">
            <span>До квалификации «{{ auth.currentTitle.nextTitle }}»</span>
            <span>{{ auth.currentTitle.xpToNext }} XP</span>
          </div>
          <div class="track">
            <div class="bar" :style="{ width: `${auth.currentTitle.progress}%` }"></div>
          </div>
        </div>
      </div>

      <div class="hero-actions">
        <router-link to="/requests" class="cta-button">
          📋 Реестр входящих заявок {{ openTasksCount ? `(${openTasksCount})` : '' }}
        </router-link>
      </div>
    </header>

    <!-- Карточки статистики -->
    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-icon">📬</span>
        <div class="stat-val">{{ openTasksCount }}</div>
        <div class="stat-label">Ожидают разбора</div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">🤝</span>
        <div class="stat-val">{{ inWorkCount }}</div>
        <div class="stat-label">В вашей работе</div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">⚡</span>
        <div class="stat-val">+50 XP</div>
        <div class="stat-label">За разбор задания</div>
      </div>
    </div>

    <!-- Задачи в работе у преподавателя (если есть) -->
    <section v-if="myTasksInWork.length > 0" class="section">
      <div class="section-header">
        <h2>Принятые в работу заявки</h2>
        <router-link to="/requests" class="section-more-link">Полный реестр →</router-link>
      </div>
      <div class="cards-list">
        <RequestCard
          v-for="req in myTasksInWork"
          :key="req.id"
          :request="req"
          viewer-role="teacher"
          @updated="loadAllData"
        />
      </div>
    </section>

    <!-- Свежие открытые заявки от учеников -->
    <section class="section">
      <div class="section-header">
        <h2>Новые заявки от обучающихся</h2>
        <router-link to="/requests" class="section-more-link">Смотреть все ({{ openTasksCount }}) →</router-link>
      </div>

      <div v-if="loading" class="loader">
        <p>Загрузка реестра заявок...</p>
      </div>

      <div v-else-if="recentOpenTasks.length === 0" class="empty-state">
        <span class="empty-icon">✅</span>
        <p>В настоящий момент все поступившие заявки обработаны.</p>
        <p class="hint">Новые обращения обучающихся на разбор заданий или видеоконсультацию отобразятся здесь автоматически.</p>
        <router-link to="/bank" class="empty-cta-btn">
          📚 Открыть банк заданий ОГЭ
        </router-link>
      </div>

      <div v-else class="cards-list">
        <RequestCard
          v-for="req in recentOpenTasks"
          :key="req.id"
          :request="req"
          viewer-role="teacher"
          @take="handleTakeTask(req)"
          @updated="loadAllData"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import RequestCard from '../components/RequestCard.vue'
import { api } from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const loading = ref(true)
const openTasksCount = ref(0)
const inWorkCount = ref(0)
const recentOpenTasks = ref([])
const myTasksInWork = ref([])

async function loadAllData() {
  loading.value = true
  try {
    const tasks = await api.getBoardTasks('OPEN')
    openTasksCount.value = tasks.length
    recentOpenTasks.value = tasks
      .slice()
      .sort((a, b) => (b.id || 0) - (a.id || 0))
      .slice(0, 3)
      .map((t) => ({
        id: t.id,
        subject: t.topic?.block || 'Физика',
        block: t.topic?.block || 'MECHANICS',
        grade: t.grade || t.topic?.grade || 9,
        title: t.topic?.title || 'Вопрос по физике',
        description: t.question,
        photoUrl: t.photo_url || '',
        status: t.status.toLowerCase(),
        scheduledTime: t.scheduled_time,
        studentName: t.student?.first_name || 'Ученик',
        requestType: t.request_type || 'TASK',
        telemostUrl: t.telemost_url || '',
        teacherResponse: t.teacher_response || '',
        createdAt: t.created_at,
        created_at: t.created_at,
      }))
  } catch (e) {
    console.warn('Не удалось загрузить открытые задачи:', e)
  }

  try {
    const myTasks = await api.getMyTasks(auth.userId, 'tutor')
    const inWork = myTasks.filter((t) => (t.status || '').toUpperCase() === 'IN_PROGRESS')
    inWorkCount.value = inWork.length
    myTasksInWork.value = inWork
      .map((t) => ({
        id: t.id,
        subject: t.topic?.block || 'Физика',
        block: t.topic?.block || 'MECHANICS',
        grade: t.grade || t.topic?.grade || 9,
        title: t.topic?.title || 'Вопрос по физике',
        description: t.question,
        photoUrl: t.photo_url || '',
        status: t.status.toLowerCase(),
        scheduledTime: t.scheduled_time,
        studentName: t.student?.first_name || 'Ученик',
        requestType: t.request_type || 'TASK',
        telemostUrl: t.telemost_url || '',
        teacherResponse: t.teacher_response || '',
        createdAt: t.created_at,
        created_at: t.created_at,
      }))
      .sort((a, b) => (b.id || 0) - (a.id || 0))
  } catch (e) {
    console.warn('Не удалось загрузить задачи в работе:', e)
  } finally {
    loading.value = false
  }
}

async function handleTakeTask(req) {
  const myUserId = auth.userId ? String(auth.userId) : null
  const reqStudentId = req.student_id ? String(req.student_id) : (req.student?.id ? String(req.student.id) : null)
  const reqTgId = req.student?.telegram_id ? String(req.student.telegram_id) : (req.student_tg_id ? String(req.student_tg_id) : null)
  const reqName = (req.student_name || req.student?.first_name || '').trim().toLowerCase()
  const myName = (auth.userName || '').trim().toLowerCase()

  if ((myUserId && reqStudentId && myUserId === reqStudentId) || (myUserId && reqTgId && myUserId === reqTgId) || (reqName && myName && reqName === myName)) {
    window.alert('⚠️ Преподаватель не может взять на разбор собственную заявку!')
    return
  }

  try {
    await api.acceptTask(req.id, auth.userId)
    req.status = 'in_progress'
    auth.addXp(25)
    window.alert(`🎉 Вы взяли заявку "${req.title}" на разбор! (+25 XP)`)
    loadAllData()
  } catch (e) {
    const msg = e?.message || ''
    if (msg.includes('собственн') || msg.includes('Тьютор не может') || msg.includes('не может взять')) {
      window.alert('⚠️ Преподаватель не может взять на разбор собственную заявку!')
    } else {
      req.status = 'in_progress'
    }
  }
}

onMounted(() => {
  loadAllData()
})
</script>

<style scoped>
.teacher-dashboard {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding-bottom: 110px;
}

.teacher-hero {
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

.role-badge {
  background: rgba(255, 255, 255, 0.15);
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
  margin-top: 8px;
  display: flex;
  justify-content: center;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: auto;
  max-width: 92%;
  box-sizing: border-box;
  background: var(--primary);
  color: var(--ink);
  padding: 8px 18px;
  border-radius: var(--radius-pill);
  font-weight: 700;
  font-size: 13.5px;
  text-decoration: none;
  box-shadow: 0 4px 14px rgba(240, 168, 117, 0.3);
  transition: transform 0.15s ease, background 0.15s ease;
}
.cta-button:active {
  background: var(--primary-press);
  transform: scale(0.98);
}

/* Статистика */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-2);
}

.stat-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-md);
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 2px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.stat-icon {
  font-size: 20px;
  line-height: 1;
}
.stat-val {
  font-size: 18px;
  font-weight: 800;
  color: var(--ink);
}
.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.2;
}

/* Секции списков */
.section {
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
  max-width: 320px;
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
</style>