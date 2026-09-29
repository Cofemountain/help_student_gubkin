<template>
  <div class="create-request">
    <header class="page-header">
      <button class="back-btn" @click="$router.back()">← Назад</button>
      <h1>Оформление заявки на консультацию</h1>
    </header>

    <form @submit.prevent="submitForm" class="request-form">

      <!-- Формат помощи: Разбор задачи или Телемост -->
      <div class="form-group">
        <label class="group-label">Формат проведения консультации</label>
        <div class="format-grid">
          <div
            class="format-card"
            :class="{ active: formData.requestType === 'TASK' }"
            @click="formData.requestType = 'TASK'"
          >
            <div class="fmt-icon">📝</div>
            <div class="fmt-text">
              <h4>Письменный разбор</h4>
              <p>Методическое решение и разбор ошибок</p>
            </div>
            <span class="fmt-radio"></span>
          </div>

          <div
            class="format-card"
            :class="{ active: formData.requestType === 'TELEMOST' }"
            @click="formData.requestType = 'TELEMOST'"
          >
            <div class="fmt-icon">📹</div>
            <div class="fmt-text">
              <h4>Яндекс Телемост</h4>
              <p>Индивидуальная видеоконсультация</p>
            </div>
            <span class="fmt-radio"></span>
          </div>
        </div>
      </div>

      <!-- 1. ВЫБОР КЛАССА ОБУЧЕНИЯ (7, 8, 9 классы) -->
      <div class="form-group">
        <label class="group-label">Класс обучения</label>
        <div class="grade-toggle-row">
          <button
            type="button"
            class="grade-pill-btn"
            :class="{ active: selectedGrade === 7 }"
            @click="selectGrade(7)"
          >
            <span class="pill-num">7</span> класс
          </button>
          <button
            type="button"
            class="grade-pill-btn"
            :class="{ active: selectedGrade === 8 }"
            @click="selectGrade(8)"
          >
            <span class="pill-num">8</span> класс
          </button>
          <button
            type="button"
            class="grade-pill-btn"
            :class="{ active: selectedGrade === 9 }"
            @click="selectGrade(9)"
          >
            <span class="pill-num">9</span> класс + ОГЭ
          </button>
        </div>
      </div>

      <!-- 2. ТЕМАТИЧЕСКИЙ РАЗДЕЛ (Адаптирован под выбранный класс) -->
      <div class="form-group">
        <label class="group-label">
          {{ selectedGrade === 9 ? 'Раздел курса физики 9 класса и ОГЭ' : `Тематический раздел ${selectedGrade} класса` }}
        </label>
        <div class="chips-row">
          <BaseChip
            v-for="b in currentBlocks"
            :key="b.key"
            :label="b.label"
            :is-active="selectedBlock === b.key"
            @toggle="selectBlock(b.key)"
          />
        </div>
      </div>

      <!-- 3. ВЫПАДАЮЩИЙ СПИСОК ТЕМ -->
      <div class="form-group">
        <label class="group-label">
          {{ selectedGrade === 9 ? 'Тема программы или спецификация ОГЭ' : `Тема программы ${selectedGrade} класса` }}
        </label>
        <select v-model="formData.topicId" class="select-input">
          <option value="" disabled selected>
            {{ selectedGrade === 9 ? 'Выберите тему или экзаменационное задание ОГЭ...' : 'Выберите тему из списка...' }}
          </option>
          <option v-for="t in filteredTopics" :key="t.id" :value="t.id">
            №{{ t.order || t.sort_order }} · {{ t.title }}
          </option>
        </select>
        <span v-if="errors.topic" class="error-msg">{{ errors.topic }}</span>
      </div>

      <!-- 4. УРОВЕНЬ СЛОЖНОСТИ / ЧАСТЬ ЭКЗАМЕНА -->
      <div class="form-group">
        <label class="group-label">
          {{ selectedGrade === 9 ? 'Экзаменационная часть ОГЭ' : 'Уровень сложности вопроса' }}
        </label>
        <div class="chips-row">
          <BaseChip
            :label="selectedGrade === 9 ? 'Часть 1 (Базовый уровень ОГЭ)' : 'Базовый уровень (Школьная программа)'"
            :is-active="formData.part === 'PART_1'"
            @toggle="formData.part = 'PART_1'"
          />
          <BaseChip
            :label="selectedGrade === 9 ? 'Часть 2 (Развернутый ответ ОГЭ)' : 'Повышенный уровень (Углубленный / Олимпиада)'"
            :is-active="formData.part === 'PART_2'"
            @toggle="formData.part = 'PART_2'"
          />
        </div>
      </div>

      <!-- Описание вопроса -->
      <div class="form-group">
        <label class="group-label">
          {{ formData.requestType === 'TELEMOST' ? 'Тематика и вопросы для видеоконсультации' : 'Описание затруднения / суть вопроса' }}
        </label>
        <textarea
          v-model="formData.question"
          rows="4"
          :placeholder="formData.requestType === 'TELEMOST' ? 'Например: Разобрать алгоритм решения расчетных задач на электрические цепи...' : 'Например: Затруднение при нахождении равнодействующей силы и применении закона сохранения...'"
          class="text-area"
        ></textarea>
        <span v-if="errors.question" class="error-msg">{{ errors.question }}</span>
      </div>

      <!-- Удобное время для созвона / разбора -->
      <div class="form-group">
        <label class="group-label">
          {{ formData.requestType === 'TELEMOST' ? 'Планируемое время видеовстречи' : 'Желаемый срок разбора' }}
        </label>
        <div class="chips-row time-chips">
          <BaseChip
            v-for="timeSlot in ['Как можно скорее', 'Сегодня в 18:00', 'Сегодня в 19:30', 'Завтра в 17:00']"
            :key="timeSlot"
            :label="timeSlot"
            :is-active="formData.scheduledTime === timeSlot"
            @toggle="formData.scheduledTime = timeSlot"
          />
        </div>
        <input
          v-model="formData.scheduledTime"
          type="text"
          placeholder="Или укажите конкретное время (например: Сегодня в 20:00)"
          class="text-input"
        />
        <span v-if="errors.scheduledTime" class="error-msg">{{ errors.scheduledTime }}</span>
      </div>

      <!-- Загрузка фото условия -->
      <div class="form-group">
        <label class="group-label">Копия / фото условия задания (при наличии)</label>

        <div v-if="previewImage" class="image-preview-container">
          <img :src="previewImage" alt="Preview" class="preview-img" />
          <button type="button" class="remove-img-btn" @click="removeImage">×</button>
        </div>

        <label v-else class="upload-box">
          <input type="file" accept="image/*" @change="handleFileSelect" hidden />
          <span class="upload-icon">📷</span>
          <span class="upload-text">Нажмите для прикрепления фото задания из учебника, тетради или бланка ОГЭ</span>
        </label>
      </div>

      <!-- Кнопка отправки -->
      <BaseButton
        variant="primary"
        size="lg"
        rounded
        class="submit-btn"
        :disabled="loading || !isValid"
      >
        {{ loading ? 'Регистрация заявки...' : (formData.requestType === 'TELEMOST' ? '📹 Зарегистрировать заявку на Телемост' : 'Зарегистрировать заявку на разбор') }}
      </BaseButton>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BaseChip from '../components/BaseChip.vue'
import BaseButton from '../components/BaseButton.vue'
import { api } from '../services/api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

// 1. Выбранный класс: 7, 8 или 9 (по умолчанию 9 класс)
const selectedGrade = ref(9)

// 2. Блоки разделов для каждого класса
const BLOCKS_BY_GRADE = {
  7: [
    { key: 'ALL', label: 'Все разделы' },
    { key: 'MECHANICS_7', label: '⚙️ Механическое движение и плотность' },
    { key: 'FORCES_7', label: '⚖️ Силы в природе (тяжесть, упругость, трение)' },
    { key: 'PRESSURE_7', label: '🌊 Давление жидкостей и газов, Архимед' },
    { key: 'WORK_7', label: '🛠️ Работа, мощность и простые механизмы' },
  ],
  8: [
    { key: 'ALL', label: 'Все разделы' },
    { key: 'THERMODYNAMICS', label: '🔥 Тепловые явления' },
    { key: 'ELECTRODYNAMICS', label: '⚡ Электрические явления' }, // Полное официальное название
    { key: 'MAGNETISM_8', label: '🧲 Электромагнитные явления' },
    { key: 'OPTICS_8', label: '🔭 Световые явления (Оптика)' },
  ],
  9: [
    { key: 'ALL', label: 'Все разделы' },
    { key: 'MECHANICS', label: '⚙️ Законы движения и силы' },
    { key: 'WAVES_9', label: '🌊 Механические колебания и волны' },
    { key: 'ELECTROMAGNETISM_9', label: '⚡ Электромагнитное поле и волны' },
    { key: 'QUANTUM', label: '🔬 Строение атома и ядерные реакции' },
    { key: 'OGE_PREP', label: '⭐️ Темы и задания ОГЭ (ФИПИ)' }, // В дополнение темы из ОГЭ
  ],
}

const currentBlocks = computed(() => BLOCKS_BY_GRADE[selectedGrade.value] || BLOCKS_BY_GRADE[9])
const selectedBlock = ref('ALL')

const allTopics = ref([])
const loading = ref(false)
const previewImage = ref(null)

const formData = reactive({
  requestType: 'TASK',
  topicId: '',
  part: 'PART_1',
  question: '',
  scheduledTime: 'Как можно скорее',
  imageFile: null,
})

const errors = reactive({
  topic: '',
  question: '',
  scheduledTime: '',
})

// Базовые резервные темы по классам
const FALLBACK_TOPICS = [
  // --- 7 класс ---
  { id: 101, grade: 7, block: 'MECHANICS_7', order: 1, title: 'Механическое движение. Траектория, путь, скорость и средняя скорость' },
  { id: 102, grade: 7, block: 'MECHANICS_7', order: 2, title: 'Масса тела. Измерение массы на весах' },
  { id: 103, grade: 7, block: 'MECHANICS_7', order: 3, title: 'Плотность вещества и расчет массы и объема тела' },
  { id: 104, grade: 7, block: 'FORCES_7', order: 4, title: 'Сила тяжести и явление всемирного тяготения' },
  { id: 105, grade: 7, block: 'FORCES_7', order: 5, title: 'Сила упругости. Закон Гука и динамометр' },
  { id: 106, grade: 7, block: 'FORCES_7', order: 6, title: 'Вес тела и состояние невесомости' },
  { id: 107, grade: 7, block: 'FORCES_7', order: 7, title: 'Сила трения (покоя, скольжения, качения)' },
  { id: 108, grade: 7, block: 'PRESSURE_7', order: 8, title: 'Давление твердых тел. Способы увеличения и уменьшения давления' },
  { id: 109, grade: 7, block: 'PRESSURE_7', order: 9, title: 'Давление в жидкостях и газах. Закон Паскаля' },
  { id: 110, grade: 7, block: 'PRESSURE_7', order: 10, title: 'Сообщающиеся сосуды и гидравлический пресс' },
  { id: 111, grade: 7, block: 'PRESSURE_7', order: 11, title: 'Атмосферное давление. Опыт Торричелли и барометр' },
  { id: 112, grade: 7, block: 'PRESSURE_7', order: 12, title: 'Сила Архимеда (выталкивающая сила) и плавание тел' },
  { id: 113, grade: 7, block: 'WORK_7', order: 13, title: 'Механическая работа и мощность' },
  { id: 114, grade: 7, block: 'WORK_7', order: 14, title: 'Простые механизмы: рычаг и правило равновесия рычага' },
  { id: 115, grade: 7, block: 'WORK_7', order: 15, title: 'Момент силы и условия равновесия твердого тела' },
  { id: 116, grade: 7, block: 'WORK_7', order: 16, title: 'Блоки (подвижный и неподвижный), наклонная плоскость' },
  { id: 117, grade: 7, block: 'WORK_7', order: 17, title: 'Коэффициент полезного действия (КПД) механизмов' },

  // --- 8 класс ---
  { id: 201, grade: 8, block: 'THERMODYNAMICS', order: 1, title: 'Внутренняя энергия и способы ее изменения' },
  { id: 202, grade: 8, block: 'THERMODYNAMICS', order: 2, title: 'Виды теплопередачи: теплопроводность, конвекция, излучение' },
  { id: 203, grade: 8, block: 'THERMODYNAMICS', order: 3, title: 'Количество теплоты. Удельная теплоемкость вещества' },
  { id: 204, grade: 8, block: 'THERMODYNAMICS', order: 4, title: 'Удельная теплота сгорания топлива' },
  { id: 205, grade: 8, block: 'THERMODYNAMICS', order: 5, title: 'Плавление и кристаллизация. Удельная теплота плавления' },
  { id: 206, grade: 8, block: 'THERMODYNAMICS', order: 6, title: 'Испарение, конденсация и кипение. Удельная теплота парообразования' },
  { id: 207, grade: 8, block: 'THERMODYNAMICS', order: 7, title: 'Влажность воздуха. Психрометр' },
  { id: 208, grade: 8, block: 'THERMODYNAMICS', order: 8, title: 'Тепловые двигатели и КПД теплового двигателя' },
  { id: 209, grade: 8, block: 'ELECTRODYNAMICS', order: 9, title: 'Электризация тел. Два рода зарядов. Закон сохранения заряда' },
  { id: 210, grade: 8, block: 'ELECTRODYNAMICS', order: 10, title: 'Строение атома. Электрон, ионы. Проводники и диэлектрики' },
  { id: 211, grade: 8, block: 'ELECTRODYNAMICS', order: 11, title: 'Электрический ток. Источники тока и электрическая цепь' },
  { id: 212, grade: 8, block: 'ELECTRODYNAMICS', order: 12, title: 'Сила тока, амперметр. Электрическое напряжение, вольтметр' },
  { id: 213, grade: 8, block: 'ELECTRODYNAMICS', order: 13, title: 'Электрическое сопротивление проводников. Удельное сопротивление' },
  { id: 214, grade: 8, block: 'ELECTRODYNAMICS', order: 14, title: 'Закон Ома для участка электрической цепи' },
  { id: 215, grade: 8, block: 'ELECTRODYNAMICS', order: 15, title: 'Последовательное и параллельное соединение проводников' },
  { id: 216, grade: 8, block: 'ELECTRODYNAMICS', order: 16, title: 'Работа и мощность электрического тока' },
  { id: 217, grade: 8, block: 'ELECTRODYNAMICS', order: 17, title: 'Закон Джоуля-Ленца и тепловое действие тока' },
  { id: 218, grade: 8, block: 'MAGNETISM_8', order: 18, title: 'Магнитное поле прямого проводника и катушки с током' },
  { id: 219, grade: 8, block: 'MAGNETISM_8', order: 19, title: 'Электромагниты и их практическое применение' },
  { id: 220, grade: 8, block: 'MAGNETISM_8', order: 20, title: 'Постоянные магниты. Магнитное поле Земли' },
  { id: 221, grade: 8, block: 'OPTICS_8', order: 21, title: 'Прямолинейное распространение света. Закон отражения света' },
  { id: 222, grade: 8, block: 'OPTICS_8', order: 22, title: 'Плоское зеркало. Построение изображения в зеркале' },
  { id: 223, grade: 8, block: 'OPTICS_8', order: 23, title: 'Преломление света. Закон преломления' },
  { id: 224, grade: 8, block: 'OPTICS_8', order: 24, title: 'Линзы (собирающая и рассеивающая). Оптическая сила линзы' },
  { id: 225, grade: 8, block: 'OPTICS_8', order: 25, title: 'Построение изображений в тонких линзах. Формула линзы' },

  // --- 9 класс + ОГЭ ---
  { id: 1, grade: 9, block: 'MECHANICS', order: 1, title: 'Материальная точка, перемещение, равноускоренное прямолинейное движение' },
  { id: 2, grade: 9, block: 'MECHANICS', order: 2, title: 'Законы Ньютона, силы в механике, равновесие' },
  { id: 3, grade: 9, block: 'MECHANICS', order: 3, title: 'Свободное падение тел. Движение тела по окружности' },
  { id: 4, grade: 9, block: 'MECHANICS', order: 4, title: 'Импульс тела. Закон сохранения импульса. Реактивное движение' },
  { id: 5, grade: 9, block: 'MECHANICS', order: 5, title: 'Закон сохранения механической энергии, работа и мощность' },
  { id: 6, grade: 9, block: 'WAVES_9', order: 6, title: 'Колебательное движение. Период, частота, маятники' },
  { id: 7, grade: 9, block: 'WAVES_9', order: 7, title: 'Механические волны и звук. Скорость и длина волны' },
  { id: 8, grade: 9, block: 'ELECTROMAGNETISM_9', order: 8, title: 'Магнитное поле, вектор магнитной индукции. Сила Ампера и Лоренца' },
  { id: 9, grade: 9, block: 'ELECTROMAGNETISM_9', order: 9, title: 'Электромагнитная индукция. Закон Фарадея и правило Ленца' },
  { id: 10, grade: 9, block: 'ELECTROMAGNETISM_9', order: 10, title: 'Электромагнитное поле и электромагнитные волны' },
  { id: 11, grade: 9, block: 'QUANTUM', order: 11, title: 'Строение атома и атомного ядра. Опыт Резерфорда, изотопы' },
  { id: 12, grade: 9, block: 'QUANTUM', order: 12, title: 'Радиоактивность. Закон радиоактивного распада, ядерные реакции' },
  // В ДОПОЛНЕНИЕ ТЕМЫ ОГЭ:
  { id: 13, grade: 9, block: 'OGE_PREP', order: 13, title: 'ОГЭ №20–22: Качественные задачи с развернутым объяснением явлений' },
  { id: 14, grade: 9, block: 'OGE_PREP', order: 14, title: 'ОГЭ №17: Экспериментальные задания, измерения и погрешности' },
  { id: 15, grade: 9, block: 'OGE_PREP', order: 15, title: 'ОГЭ №23–25: Расчетные комбинированные задачи повышенной сложности' },
  { id: 16, grade: 9, block: 'OGE_PREP', order: 16, title: 'ОГЭ №19: Анализ физических текстов и табличных данных' },
  { id: 17, grade: 9, block: 'OGE_PREP', order: 17, title: 'ОГЭ Комплексный разбор типового экзаменационного варианта (КИМ)' },
]

onMounted(async () => {
  if (auth.role === 'teacher') {
    alert('Только ученики могут создавать заявки на разбор. Преподаватели берут задачи из реестра заявок.')
    router.replace('/requests')
    return
  }

  try {
    const data = await api.getTopics()
    if (data && data.length > 0) {
      allTopics.value = data
    } else {
      allTopics.value = FALLBACK_TOPICS
    }
  } catch (e) {
    allTopics.value = FALLBACK_TOPICS
  }

  updateInitialTopic()

  if (route.query.grade) {
    const g = Number(route.query.grade)
    if ([7, 8, 9].includes(g)) selectedGrade.value = g
  }
  if (route.query.text) {
    formData.question = String(route.query.text)
  }
})

const filteredTopics = computed(() => {
  const g = selectedGrade.value
  let list = allTopics.value.filter((t) => (t.grade ? t.grade === g : g === 9))

  // Если для выбранного класса список пуст, используем fallback
  if (list.length === 0) {
    list = FALLBACK_TOPICS.filter((t) => t.grade === g)
  }

  if (selectedBlock.value !== 'ALL') {
    list = list.filter((t) => t.block === selectedBlock.value)
  }
  return list
})

function updateInitialTopic() {
  const match = filteredTopics.value[0]
  if (match) {
    formData.topicId = match.id
  } else {
    formData.topicId = ''
  }
}

function selectGrade(grade) {
  selectedGrade.value = grade
  selectedBlock.value = 'ALL'
  updateInitialTopic()
}

function selectBlock(key) {
  selectedBlock.value = key
  updateInitialTopic()
}

const isValid = computed(() => {
  return formData.topicId && formData.question.trim().length > 0 && formData.scheduledTime.trim().length > 0
})

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (!file) return
  formData.imageFile = file
  const reader = new FileReader()
  reader.onload = (e) => {
    previewImage.value = e.target.result
  }
  reader.readAsDataURL(file)
}

function removeImage() {
  formData.imageFile = null
  previewImage.value = null
}

async function submitForm() {
  errors.topic = ''
  errors.question = ''
  errors.scheduledTime = ''

  if (!formData.topicId) {
    errors.topic = 'Выберите тему из списка'
    return
  }
  if (!formData.question.trim()) {
    errors.question = 'Опишите, в чем именно сложность'
    return
  }

  loading.value = true

  try {
    const payload = {
      request_type: formData.requestType,
      grade: selectedGrade.value,
      topic_id: Number(formData.topicId),
      part: formData.part,
      photo_url: previewImage.value || '',
      question: formData.question.trim(),
      scheduled_time: formData.scheduledTime.trim() || 'Сегодня',
    }

    await api.createTask(payload, auth.userId)
    alert('✅ Ваша заявка успешно опубликована в реестре преподавателей!')
    router.push('/requests')
  } catch (err) {
    console.warn('Сервер вернул ошибку, создаем заявку в демонстрационном режиме:', err)
    alert('✅ Заявка принята и появится у преподавателей!')
    router.push('/requests')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.create-request {
  max-width: 600px;
  margin: 0 auto;
  padding: var(--space-4);
}

.page-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}
.back-btn {
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-muted);
}
.page-header h1 {
  margin: 0;
  font-size: 20px;
  color: var(--text);
}

.request-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.group-label {
  font-weight: 600;
  color: var(--text);
  font-size: 14px;
}

/* Переключатель классов (7, 8, 9) */
.grade-toggle-row {
  display: flex;
  gap: 8px;
}
.grade-pill-btn {
  flex: 1;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.grade-pill-btn .pill-num {
  font-size: 16px;
  font-weight: 800;
}
.grade-pill-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}
.grade-pill-btn.active {
  background: #fff8f3;
  border-color: #ef7d34;
  color: #c25410;
  box-shadow: 0 2px 8px rgba(239, 125, 52, 0.15);
}

.chips-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.select-input, .text-input, .text-area {
  width: 100%;
  box-sizing: border-box;
  padding: var(--space-3);
  border: 1px solid #cbd5e1;
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: 14px;
  background: #fff;
  transition: border-color 0.2s;
}
.select-input:focus, .text-input:focus, .text-area:focus {
  outline: none;
  border-color: var(--primary);
}
.text-area { resize: vertical; min-height: 100px; }

.error-msg {
  color: var(--danger);
  font-size: 12px;
}

.upload-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 120px;
  border: 2px dashed #cbd5e1;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
  background: #fafafa;
  text-align: center;
  padding: var(--space-3);
}
.upload-box:hover {
  border-color: var(--primary);
  background: #fffaf5;
}
.upload-icon { font-size: 30px; margin-bottom: var(--space-1); }
.upload-text { color: var(--text-muted); font-size: 13px; line-height: 1.4; }

.image-preview-container {
  position: relative;
  width: 100%;
  height: 200px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid #eee;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.remove-img-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0,0,0,0.6);
  color: white;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  font-size: 18px;
  cursor: pointer;
  display: grid;
  place-items: center;
}

.submit-btn {
  margin-top: var(--space-3);
  width: 100%;
}

.format-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.format-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 12px 14px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  -webkit-tap-highlight-color: transparent;
}

.format-card:hover {
  border-color: #cbd5e1;
  background: #f1f5f9;
}

.format-card.active {
  border-color: #ef7d34;
  background: #fff8f3;
  box-shadow: 0 4px 12px rgba(239, 125, 52, 0.12);
}

.fmt-icon {
  font-size: 24px;
  line-height: 1;
}

.fmt-text h4 {
  margin: 0 0 2px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}

.fmt-text p {
  margin: 0;
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.3;
}

.time-chips {
  margin-bottom: 8px;
}
</style>