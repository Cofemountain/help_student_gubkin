<template>
  <div class="teacher-feed">
    <!-- Шапка раздела Заявок -->
    <header class="feed-header">
      <div class="header-top">
        <h2>Реестр заявок на консультации</h2>
        <div class="top-actions">
          <router-link v-if="auth.role === 'student'" to="/create-request" class="create-req-btn">
            ➕ Сформировать заявку
          </router-link>
          <button class="refresh-btn" @click="refreshCurrentTab" title="Обновить список">
            🔄
          </button>
        </div>
      </div>

      <!-- Переключатель режима: Все заявки / Мои заявки -->
      <div class="mode-tabs">
        <button
          type="button"
          class="mode-tab-btn"
          :class="{ active: viewMode === 'all' }"
          @click="switchMode('all')"
        >
          {{ auth.role === 'teacher' ? '📋 Свободные заявки' : '📋 Все обращения' }}
        </button>
        <button
          type="button"
          class="mode-tab-btn"
          :class="{ active: viewMode === 'my' }"
          @click="switchMode('my')"
        >
          {{ auth.role === 'teacher' ? '🤝 Принятые в работу' : '👤 Мои заявки' }}
          {{ myRequests.length ? `(${myRequests.length})` : '' }}
        </button>
      </div>

      <!-- Фильтр по классу (7, 8, 9 классы) -->
      <div v-if="viewMode === 'all'" class="grade-filter-pills">
        <button
          v-for="g in gradeOptions"
          :key="g.value"
          type="button"
          class="grade-filter-btn"
          :class="{ active: activeGrade === g.value }"
          @click="setGradeFilter(g.value)"
        >
          {{ g.label }}
        </button>
      </div>

      <!-- Фильтры по разделу физики (только для общей ленты) -->
      <div v-if="viewMode === 'all'" class="filter-chips">
        <BaseChip
          v-for="b in blocks"
          :key="b.key"
          :label="b.label"
          :is-active="activeBlock === b.key"
          @toggle="setFilter(b.key)"
        />
      </div>
    </header>

    <!-- Список заявок -->
    <main class="feed-list">
      <div v-if="loading" class="loader">
        <p>Загрузка данных реестра...</p>
      </div>

      <!-- Если пусто в режиме Мои заявки (для преподавателя и ученика) -->
      <div v-else-if="viewMode === 'my' && myRequests.length === 0" class="empty-state">
        <template v-if="auth.role === 'teacher'">
          <p>В настоящий момент у вас отсутствуют принятые в работу заявки.</p>
          <p class="hint">Перейдите во вкладку «Свободные заявки» и выберите задание для проведения разбора (+25 XP).</p>
          <button type="button" class="cta-create-btn" @click="switchMode('all')">
            📋 Перейти к реестру заявок
          </button>
        </template>
        <template v-else>
          <p>В настоящее время поданные заявки отсутствуют.</p>
          <p class="hint">Сформируйте обращение для получения квалифицированной консультации преподавателя:</p>
          <router-link to="/create-request" class="cta-create-btn">
            ✍️ Сформировать заявку
          </router-link>
        </template>
      </div>

      <!-- Если пусто в режиме Все заявки -->
      <div v-else-if="viewMode === 'all' && filteredRequests.length === 0" class="empty-state">
        <p>В выбранном тематическом разделе или классе открытые заявки отсутствуют.</p>
        <p class="hint">Попробуйте выбрать «Все классы» или другой раздел физики.</p>
        <router-link v-if="auth.role === 'student'" to="/create-request" class="cta-create-btn">
          ➕ Сформировать заявку
        </router-link>
      </div>

      <!-- Сетка карточек заявок -->
      <div v-else class="cards-grid">
        <RequestCard
          v-for="req in currentList"
          :key="req.id"
          :request="req"
          :viewer-role="auth.role || 'teacher'"
          @take="handleTake(req)"
          @updated="refreshCurrentTab"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import RequestCard from '../components/RequestCard.vue'
import BaseChip from '../components/BaseChip.vue'
import { api } from '../services/api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const viewMode = ref('all') // 'all' | 'my'

// Фильтр по классам
const activeGrade = ref('ALL')
const gradeOptions = [
  { value: 'ALL', label: 'Все классы' },
  { value: 7, label: '7 класс' },
  { value: 8, label: '8 класс' },
  { value: 9, label: '9 класс + ОГЭ' },
]

// Разделы с полными официальными наименованиями
const blocks = [
  { key: 'ALL', label: 'Все разделы' },
  { key: 'MECHANICS', label: '⚙️ Механика' },
  { key: 'THERMODYNAMICS', label: '🔥 Тепловые явления' },
  { key: 'ELECTRODYNAMICS', label: '⚡ Электродинамика' },
  { key: 'QUANTUM', label: '🔬 Квантовая физика' },
  { key: 'PART_2_ADVANCED', label: '⭐️ 2-я часть ОГЭ' },
]
const activeBlock = ref('ALL')

const loading = ref(true)
const allRequests = ref([])
const myRequests = ref([])

async function loadFeed() {
  loading.value = true
  try {
    const data = await api.getBoardTasks('OPEN')
    allRequests.value = data.map((t) => ({
      id: t.id,
      subject: t.topic?.block || 'Физика',
      block: t.topic?.block || 'MECHANICS',
      grade: t.grade || t.topic?.grade || 9,
      part: t.part || 'PART_1',
      title: t.topic?.title || 'Вопрос по физике',
      description: t.question,
      photoUrl: t.photo_url || '',
      status: t.status.toLowerCase(),
      scheduledTime: t.scheduled_time,
      studentName: t.student?.first_name || 'Ученик',
      requestType: t.request_type || 'TASK',
      telemostUrl: t.telemost_url || '',
      teacherResponse: t.teacher_response || '',
      homework: t.homework || null,
      student: t.student,
      createdAt: t.created_at,
      created_at: t.created_at,
    }))
  } catch (e) {
    console.warn('Сервер вернул ошибку, загружаем демо-ленту заявок:', e)
    allRequests.value = [
      {
        id: 101,
        subject: 'Механика',
        block: 'MECHANICS',
        grade: 7,
        part: 'PART_1',
        title: 'Плотность твердого тела и архимедова сила',
        description: 'Не получается рассчитать объем погруженной части бруска.',
        photoUrl: '',
        status: 'open',
        scheduledTime: 'Сегодня в 18:00',
        requestType: 'TASK',
        telemostUrl: '',
        teacherResponse: '',
      },
      {
        id: 102,
        subject: 'Электрические явления',
        block: 'ELECTRODYNAMICS',
        grade: 8,
        part: 'PART_1',
        title: 'Закон Ома и смешанное соединение проводников',
        description: 'Как распределяется сила тока при параллельном соединении резисторов?',
        photoUrl: '',
        status: 'open',
        scheduledTime: 'Сегодня в 19:30',
        requestType: 'TELEMOST',
        telemostUrl: 'https://telemost.yandex.ru/',
        teacherResponse: '',
      },
      {
        id: 103,
        subject: 'Механика ОГЭ',
        block: 'MECHANICS',
        grade: 9,
        part: 'PART_2',
        title: 'Закон сохранения импульса (№24 ОГЭ)',
        description: 'Разбор комбинированной расчетной задачи второй части ОГЭ.',
        photoUrl: '',
        status: 'open',
        scheduledTime: 'Завтра в 17:00',
        requestType: 'TASK',
        telemostUrl: '',
        teacherResponse: '',
      },
    ]
  } finally {
    loading.value = false
  }
}

async function loadMyRequests() {
  try {
    const asRole = auth.role === 'teacher' ? 'tutor' : 'student'
    const data = await api.getMyTasks(auth.userId, asRole)
    myRequests.value = data.map((t) => ({
      id: t.id,
      subject: t.topic?.block || 'Физика',
      block: t.topic?.block || 'MECHANICS',
      grade: t.grade || t.topic?.grade || 9,
      part: t.part || 'PART_1',
      title: t.topic?.title || 'Вопрос по физике',
      description: t.question,
      photoUrl: t.photo_url || '',
      status: t.status.toLowerCase(),
      scheduledTime: t.scheduled_time,
      studentName: t.student?.first_name || (auth.role === 'teacher' ? 'Ученик' : auth.userName),
      requestType: t.request_type || 'TASK',
      telemostUrl: t.telemost_url || '',
      teacherResponse: t.teacher_response || '',
      homework: t.homework || null,
      student: t.student,
      createdAt: t.created_at,
      created_at: t.created_at,
    }))
  } catch (e) {
    console.warn('Не удалось загрузить мои заявки:', e)
  }
}

function switchMode(mode) {
  viewMode.value = mode
  if (mode === 'my') {
    loadMyRequests()
  } else {
    loadFeed()
  }
}

function refreshCurrentTab() {
  if (viewMode.value === 'my') {
    loadMyRequests()
  } else {
    loadFeed()
  }
}

onMounted(() => {
  loadFeed()
  loadMyRequests()
})

const filteredRequests = computed(() => {
  return allRequests.value
    .filter((req) => {
      const matchBlock = activeBlock.value === 'ALL' || req.block === activeBlock.value
      const matchGrade = activeGrade.value === 'ALL' || req.grade === activeGrade.value
      return matchBlock && matchGrade
    })
    .slice()
    .sort((a, b) => (b.id || 0) - (a.id || 0))
})

const currentList = computed(() => {
  const list = viewMode.value === 'my' ? myRequests.value : filteredRequests.value
  return list.slice().sort((a, b) => (b.id || 0) - (a.id || 0))
})

function setFilter(blockKey) {
  activeBlock.value = blockKey
}

function setGradeFilter(gradeValue) {
  activeGrade.value = gradeValue
}

async function handleTake(request) {
  const myUserId = auth.userId ? String(auth.userId) : null
  const reqStudentId = request.student_id ? String(request.student_id) : (request.student?.id ? String(request.student.id) : null)
  const reqTgId = request.student?.telegram_id ? String(request.student.telegram_id) : null
  const reqName = (request.student_name || request.studentName || request.student?.first_name || '').trim().toLowerCase()
  const myName = (auth.userName || '').trim().toLowerCase()

  if ((myUserId && reqStudentId && myUserId === reqStudentId) || (myUserId && reqTgId && myUserId === reqTgId) || (reqName && myName && reqName === myName)) {
    window.alert('⚠️ Преподаватель не может взять на разбор собственную заявку!')
    return
  }

  try {
    await api.acceptTask(request.id, auth.userId)
    request.status = 'in_progress'
    auth.addXp(25)
    window.alert(`🎉 Вы взяли заявку "${request.title}" на разбор! (+25 XP)`)
    refreshCurrentTab()
  } catch (e) {
    const msg = e?.message || ''
    if (msg.includes('собственн') || msg.includes('Тьютор не может') || msg.includes('не может взять')) {
      window.alert('⚠️ Преподаватель не может взять на разбор собственную заявку!')
    } else {
      request.status = 'in_progress'
      refreshCurrentTab()
    }
  }
}
</script>

<style scoped>
.teacher-feed {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
  padding-bottom: 110px;
  max-width: 600px;
  margin: 0 auto;
}

.feed-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.header-top h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  color: var(--text);
  line-height: 1.25;
  flex: 1;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.create-req-btn {
  background: var(--primary);
  color: var(--ink);
  text-decoration: none;
  font-size: 11.5px;
  font-weight: 700;
  padding: 6px 10px;
  border-radius: var(--radius-pill);
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.create-req-btn:active {
  background: var(--primary-press);
}

.refresh-btn {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  padding: 6px 10px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  font-size: 13px;
}

/* Переключатель вкладок */
.mode-tabs {
  display: flex;
  background: #f1f5f9;
  padding: 3px;
  border-radius: var(--radius-pill);
  gap: 4px;
}

.mode-tab-btn {
  flex: 1;
  border: none;
  background: transparent;
  padding: 6px 10px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  color: #64748b;
  transition: all 0.15s ease;
}

.mode-tab-btn.active {
  background: #ffffff;
  color: var(--ink);
  font-weight: 700;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Фильтр по классу (7, 8, 9) */
.grade-filter-pills {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;
  white-space: nowrap;
  -webkit-overflow-scrolling: touch;
}
.grade-filter-btn {
  border: 1.5px solid #e2e8f0;
  background: #ffffff;
  color: #475569;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 100px;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}
.grade-filter-btn:hover:not(.active) {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #0f172a;
}
.grade-filter-btn.active {
  background: #fff8f3;
  border-color: #f97316;
  color: #c2410c;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(249, 115, 22, 0.15);
}

.filter-chips {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 2px;
  white-space: nowrap;
  -webkit-overflow-scrolling: touch;
}

.cards-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  width: 100%;
}

.empty-state {
  text-align: center;
  padding: var(--space-6) var(--space-3);
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
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
}

.cta-create-btn {
  margin-top: 6px;
  background: var(--primary);
  color: var(--ink);
  text-decoration: none;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 18px;
  border-radius: var(--radius-pill);
  display: inline-block;
}

.loader {
  text-align: center;
  padding: var(--space-6);
  color: var(--text-muted);
  font-size: 13px;
}
</style>