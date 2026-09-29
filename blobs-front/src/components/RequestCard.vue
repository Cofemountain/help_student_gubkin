<template>
  <div class="request-card" :class="cardClasses" @click="openDetailModal">
    <div class="card-header">
      <div class="header-tags">
        <span class="grade-tag">{{ gradeLabel }}</span>
        <span class="topic-tag">{{ topicLabel }}</span>
        <span class="format-tag" :class="isTelemost ? 'telemost' : 'task'">
          {{ isTelemost ? '📹 Телемост' : '📝 Задача' }}
        </span>
        <span class="part-tag">{{ partLabel }}</span>
      </div>
      <span class="status-badge" :class="statusClass">{{ statusLabel }}</span>
    </div>

    <div class="card-body">
      <h3 class="card-title">{{ request.title || request.question || 'Вопрос по физике' }}</h3>
      <p v-if="request.description && request.description !== request.title" class="card-desc">
        {{ request.description }}
      </p>

      <!-- Индикатор фото: фото условия открывается внутри карточки -->
      <div v-if="hasPhoto" class="photo-preview-pill" @click.stop="openDetailModal">
        <span class="cam-icon">📷</span>
        <span class="cam-text">Прикреплено фото условия</span>
        <span class="cam-action">Открыть карточку →</span>
      </div>

      <div class="card-meta">
        <span class="meta-item">🕒 {{ request.scheduled_time || request.scheduledTime || 'Как можно скорее' }}</span>
        <span class="meta-item" v-if="request.student_name || request.studentName">
          👤 {{ request.student_name || request.studentName }}
        </span>
        <span class="open-card-hint" @click.stop="openDetailModal">Подробнее / Решение ↗</span>
      </div>

      <!-- Краткое превью ответа преподавателя в карточке ленты -->
      <div v-if="teacherResponseText" class="teacher-response-box">
        <div class="resp-header"><span>👨‍🏫</span><strong>Разбор от преподавателя:</strong></div>
        <p class="resp-text">{{ teacherResponseText }}</p>
        <div v-if="request.solution_photo_url || request.solutionPhotoUrl" class="sol-attached-hint">
          📎 Прикреплено фото решения (откройте карточку для просмотра)
        </div>
      </div>

      <!-- Если ученик задал уточняющий вопрос по заявке -->
      <div v-if="request.student_clarification" class="feed-clarification-box">
        <span class="fc-icon">❓</span>
        <div class="fc-content">
          <strong>Вопрос от ученика по разбору:</strong>
          <p class="fc-text">«{{ request.student_clarification }}»</p>
        </div>
      </div>

      <div v-if="telemostLink" class="telemost-card-box">
        <div class="tm-header">
          <span class="tm-icon">📹</span>
          <div class="tm-info">
            <strong>Видеовстреча создана</strong>
            <span>Индивидуальная консультация в Телемосте</span>
          </div>
        </div>
        <a :href="telemostLink" target="_blank" rel="noopener" class="tm-join-btn" @click.stop>📹 Подключиться</a>
      </div>
    </div>

    <!-- Подвал карточки в ленте -->
    <div class="card-footer" @click.stop>
      <!-- Время создания заявки снизу слева -->
      <span class="card-created-time" :title="formattedFullTime">
        🕒 {{ formattedShortTime }}
      </span>

      <div class="card-footer-actions">
        <!-- Преподаватель: Взять задачу (ТОЛЬКО если НЕ своя заявка) -->
        <template v-if="isOpen && isTeacher && !isOwnTask">
          <button type="button" class="action-btn take-btn" :disabled="taking" @click="handleTake">
            <span v-if="taking">⏳ Беру...</span>
            <span v-else>🤝 Взять на разбор</span>
            <span class="xp-tag">+25 XP</span>
          </button>
        </template>

        <!-- Если заявка создана текущим пользователем -->
        <span v-if="isOpen && isOwnTask" class="student-hint own-task-pill">
          👤 Ваша заявка (ожидает преподавателя)
        </span>

        <!-- Ученик (не преподаватель): Ожидание -->
        <span v-else-if="isOpen && !isTeacher" class="student-hint">
          ⏳ Ожидает преподавателя
        </span>

        <!-- Преподаватель: В работе -> Кнопка открыть карточку для ввода/дополнения решения -->
        <template v-if="isInProgress && isTeacher">
          <button type="button" class="action-btn answer-btn" @click="openDetailModal">
            ✍️ {{ isTelemost ? '📞 Итоги звонка / ДЗ' : (teacherResponseText ? '📝 Дополнить разбор' : '✍️ Вписать решение') }}
          </button>
        </template>

        <!-- Ученик: В работе -> Проверить ответ / Закрыть заявку -->
        <template v-if="isInProgress && !isTeacher">
          <button type="button" class="action-btn check-solution-btn" @click="openDetailModal">
            <span v-if="teacherResponseText || telemostLink">🎓 Проверить решение преподавателя</span>
            <span v-else>⏳ В работе у преподавателя</span>
          </button>
        </template>

        <span v-if="isCompleted" class="completed-label">✓ Вопрос решён</span>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- ПОЛНОРАЗМЕРНАЯ ОТКРЫТАЯ КАРТОЧКА (МОДАЛЬНОЕ ОКНО)        -->
    <!-- ======================================================== -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="closeDetailModal">
      <div class="detail-modal" @click.stop>
        <!-- Шапка открытой карточки -->
        <div class="modal-header">
          <div class="modal-tags">
            <span class="grade-tag">{{ gradeLabel }}</span>
            <span class="topic-tag">{{ topicLabel }}</span>
            <span class="part-tag">{{ partLabel }}</span>
            <span class="status-badge" :class="statusClass">{{ statusLabel }}</span>
          </div>
          <button type="button" class="modal-close-btn" @click="closeDetailModal" title="Закрыть окно (Esc)">✕</button>
        </div>

        <!-- Тело открытой карточки -->
        <div class="modal-body">
          <h2 class="modal-title">{{ request.title || request.question || 'Вопрос по физике' }}</h2>
          <p v-if="request.description" class="modal-question-text">{{ request.description }}</p>

          <!-- 1. Фотография условия задания (если прикреплена учеником) -->
          <div v-if="hasPhoto" class="modal-photo-block">
            <div class="photo-block-header">
              <span class="photo-title">📷 Фотография условия задания</span>
              <a v-if="resolvedPhotoUrl && !imageLoadError" :href="resolvedPhotoUrl" target="_blank" rel="noopener" class="photo-zoom-btn">
                🔍 В полном размере
              </a>
            </div>
            <div class="photo-wrapper">
              <img
                v-if="!imageLoadError"
                :src="resolvedPhotoUrl"
                @error="imageLoadError = true"
                alt="Условие задачи"
                class="full-photo-img"
              />
              <div v-else class="photo-error-box">
                <span class="error-icon">🖼️</span>
                <p>Файл изображения задания сохранён в системе (ID #{{ request.id }})</p>
              </div>
            </div>
          </div>

          <!-- Метаданные -->
          <div class="modal-meta-grid">
            <div class="meta-cell">
              <span class="meta-label">Время создания</span>
              <span class="meta-val">🕒 {{ formattedFullTime }}</span>
            </div>
            <div class="meta-cell">
              <span class="meta-label">Срок разбора</span>
              <span class="meta-val">🕒 {{ request.scheduled_time || request.scheduledTime || 'Как можно скорее' }}</span>
            </div>
            <div class="meta-cell" v-if="request.student_name || request.studentName">
              <span class="meta-label">Автор вопроса</span>
              <span class="meta-val">👤 {{ request.student_name || request.studentName }}</span>
            </div>
            <div class="meta-cell">
              <span class="meta-label">Формат помощи</span>
              <span class="meta-val">{{ isTelemost ? '📹 Видеоконсультация (Телемост)' : '📝 Письменный разбор' }}</span>
            </div>
          </div>

          <!-- Уведомление об уточняющем вопросе ученика -->
          <div v-if="request.student_clarification" class="modal-clarification-banner">
            <span class="mcb-icon">❓</span>
            <div class="mcb-content">
              <strong>Вопрос от ученика по разбору:</strong>
              <p class="mcb-text">«{{ request.student_clarification }}»</p>
              <span v-if="isTeacher" class="mcb-hint">💡 Пожалуйста, дополните разбор или свяжитесь с учеником.</span>
            </div>
          </div>

          <!-- 2. ЕСЛИ ТЕЛЕМОСТ: Блок видеовстречи и проведение звонка -->
          <div v-if="isTelemost || telemostLink" class="modal-telemost-section">
            <div class="tm-alert-box">
              <span class="tm-icon-large">📹</span>
              <div class="tm-details">
                <strong>Индивидуальная видеоконсультация в Яндекс Телемосте</strong>
                <p v-if="telemostLink">Комната Яндекс Телемост готова. Нажмите для входа в видеозвонок:</p>
                <div v-else class="tm-instruction-box">
                  <p class="tm-step">1️⃣ Нажмите <strong>«Создать встречу в Телемосте»</strong> (в открывшемся окне Яндекса нажмите желтую кнопку «Создать встречу»).</p>
                  <p class="tm-step">2️⃣ Вставьте скопированную ссылку сюда и нажмите <strong>«Прикрепить ссылку»</strong> — ученик сразу получит кнопку прямого входа!</p>
                </div>
                <div class="tm-actions-row">
                  <a v-if="telemostLink" :href="telemostLink" target="_blank" rel="noopener" class="tm-connect-btn">
                    📹 Подключиться к Яндекс Телемосту
                  </a>
                  <a v-else href="https://telemost.yandex.ru/" target="_blank" rel="noopener" class="tm-open-link-btn primary" @click="showTelemostInput = true">
                    🌐 Создать встречу в Телемосте
                  </a>
                  <button v-if="isTeacher" type="button" class="tm-edit-link-btn" @click="showTelemostInput = !showTelemostInput">
                    {{ showTelemostInput ? '✕ Скрыть ввод' : (telemostLink ? '🔄 Изменить ссылку' : '🔗 Вставить ссылку встречи') }}
                  </button>
                </div>
                <div v-if="isTeacher && (showTelemostInput || !telemostLink)" class="tm-custom-input-box">
                  <input
                    v-model="customTelemostInput"
                    type="text"
                    placeholder="Вставьте ссылку https://telemost.yandex.ru/j/..."
                    class="tm-custom-input"
                  />
                  <button type="button" class="tm-save-custom-btn" @click="saveCustomTelemost">
                    💾 Прикрепить ссылку
                  </button>
                </div>
              </div>
            </div>

            <!-- Кнопка «Выдать проверочную задачу из закрытого банка» для преподавателя -->
            <div v-if="isTeacher && isInProgressOrUnderstood" class="call-finished-container">
              <button
                type="button"
                class="call-done-btn"
                @click="openClosedBankAssigner"
              >
                🔒 Выдать задачу из закрытого банка для ученика
              </button>
            </div>
          </div>

          <!-- 3. ДЛЯ ПРЕПОДАВАТЕЛЯ В СТАТУСЕ «В РАБОТЕ»: ВПИСАТЬ РЕШЕНИЕ И ПРИКРЕПИТЬ ФОТО -->
          <div v-if="isTeacher && isInProgress && !isTelemost" class="teacher-solution-editor">
            <div class="editor-header">
              <span class="ed-icon">✍️</span>
              <div>
                <strong>Предоставить решение и методический разбор</strong>
                <p>Впишите пошаговый ход решения и прикрепите фото вычислений/чертежа</p>
              </div>
            </div>

            <!-- Текстовое решение -->
            <div class="editor-field">
              <label class="field-label">Методическое решение и формулы:</label>
              <textarea
                v-model="solutionText"
                rows="5"
                placeholder="Например: 1) Запишем закон сохранения энергии... 2) Выразим искомую величину... Ответ: 25 Дж"
                class="solution-textarea"
              ></textarea>
            </div>

            <!-- Прикрепление фото решения -->
            <div class="editor-field">
              <label class="field-label">Фотография / скан рукописного решения (при наличии):</label>
              <div v-if="solutionPhoto" class="solution-photo-preview">
                <img :src="solutionPhoto" alt="Фото решения" class="solution-thumb-img" />
                <button type="button" class="del-solution-photo-btn" @click="removeSolutionPhoto">✕ Удалить фото</button>
              </div>
              <label v-else class="upload-solution-label">
                <input type="file" accept="image/*" @change="handleSolutionPhotoSelect" hidden />
                <span class="up-icon">📷</span>
                <span class="up-text">Нажмите для выбора фотографии решения из галереи или камеры</span>
              </label>
            </div>

            <!-- Кнопка отправки решения -->
            <div class="editor-actions">
              <button
                type="button"
                class="submit-solution-btn"
                :disabled="submittingSolution || (!solutionText.trim() && !solutionPhoto)"
                @click="submitSolution"
              >
                <span v-if="submittingSolution">⏳ Сохранение и отправка...</span>
                <span v-else>✅ Отправить решение ученику на проверку</span>
              </button>
            </div>
          </div>

          <!-- 4. НАЗНАЧЕНИЕ ДЗ ИЗ ЗАКРЫТОГО БАНКА ПОСЛЕ ТЕЛЕМОСТА -->
          <div v-if="showClosedBankSelector && isTeacher" class="closed-bank-modal-box">
            <div class="closed-box-header">
              <span class="lock-icon">🔒</span>
              <div>
                <strong>Закрытый банк задач: Назначение домашнего задания</strong>
                <p>Выберите задачу без ответов в сети для закрепления материала учеником</p>
              </div>
              <button type="button" class="close-selector-btn" @click="showClosedBankSelector = false">✕</button>
            </div>

            <div v-if="loadingClosedTasks" class="loading-closed">
              ⏳ Загрузка заданий из закрытого банка...
            </div>

            <div v-else-if="closedTasksList.length === 0" class="empty-closed">
              <p>В закрытом банке по данной теме задач пока нет.</p>
              <button type="button" class="skip-hw-btn" @click="completeCallWithoutHw">
                Завершить консультацию без ДЗ
              </button>
            </div>

            <div v-else class="closed-tasks-selector">
              <label class="field-label">Выберите задачу для ученика:</label>
              <select v-model="selectedClosedTaskId" class="select-closed-input">
                <option value="" disabled selected>-- Выберите задачу из закрытого банка --</option>
                <option v-for="ct in closedTasksList" :key="ct.id" :value="ct.id">
                  [{{ ct.grade }} кл · {{ ct.difficulty }}] {{ ct.title }}
                </option>
              </select>

              <!-- Превью выбранной задачи закрытого банка -->
              <div v-if="selectedTaskPreview" class="closed-task-preview-card">
                <h4>{{ selectedTaskPreview.title }}</h4>
                <p class="ct-statement">{{ selectedTaskPreview.statement }}</p>
                <span class="ct-diff-tag">Уровень: {{ selectedTaskPreview.difficulty }}</span>
              </div>

              <div class="closed-assign-actions">
                <button
                  type="button"
                  class="assign-hw-btn"
                  :disabled="!selectedClosedTaskId || assigningHw"
                  @click="confirmAssignHomework"
                >
                  <span v-if="assigningHw">⏳ Прикрепление...</span>
                  <span v-else>📌 Прикрепить ДЗ и завершить консультацию</span>
                </button>
                <button type="button" class="skip-hw-btn" @click="completeCallWithoutHw">
                  Завершить без ДЗ
                </button>
              </div>
            </div>
          </div>

          <!-- 5. ОТОБРАЖЕНИЕ ГОТОВОГО РЕШЕНИЯ (ДЛЯ УЧЕНИКА И В ИСТОРИИ) -->
          <div v-if="teacherResponseText" class="modal-response-block">
            <div class="mresp-header">
              <span>👨‍🏫</span>
              <strong>Методическое решение преподавателя:</strong>
            </div>
            <p class="mresp-text">{{ teacherResponseText }}</p>

            <!-- Фото решения (если есть) -->
            <div v-if="request.solution_photo_url || request.solutionPhotoUrl" class="solution-photo-block">
              <div class="sol-photo-bar">
                <span>📎 Фотография решения преподавателя</span>
                <a :href="request.solution_photo_url || request.solutionPhotoUrl" target="_blank" rel="noopener" class="zoom-btn">
                  🔍 Открыть фото в полный размер
                </a>
              </div>
              <img :src="request.solution_photo_url || request.solutionPhotoUrl" alt="Решение преподавателя" class="sol-full-photo" />
            </div>
          </div>

          <!-- 6. ЕСЛИ НАЗНАЧЕНА ЗАДАЧА ИЗ ЗАКРЫТОГО БАНКА -->
          <div v-if="request.homework" class="assigned-hw-block">
            <div class="hw-header">
              <span>🔒</span>
              <strong>Проверочная задача из закрытого банка:</strong>
            </div>
            <p class="hw-text">{{ request.homework.task_text }}</p>
            <div class="hw-status-row">
              <span class="hw-status-tag" :class="request.homework.status">
                {{ request.homework.status === 'ACCEPTED' ? '✓ Ответ принят верно' : 'Ожидает решения ученика' }}
              </span>
            </div>

            <!-- Форма решения для ученика (если еще не решена) -->
            <div v-if="!isTeacher && request.homework.status !== 'ACCEPTED' && !isCompleted" class="hw-student-solve-box">
              <label class="field-label">Ваш числовой ответ на задачу:</label>
              <div class="hw-input-row">
                <input
                  v-model="homeworkAnswerInput"
                  type="text"
                  placeholder="Например: 12.5 или 4"
                  class="hw-answer-input"
                  :disabled="checkingHwAnswer"
                  @keyup.enter="handleCheckHomeworkAnswer"
                />
                <button
                  type="button"
                  class="hw-check-btn"
                  :disabled="checkingHwAnswer || !homeworkAnswerInput.trim()"
                  @click="handleCheckHomeworkAnswer"
                >
                  <span v-if="checkingHwAnswer">⏳ Проверка...</span>
                  <span v-else>🚀 Проверить ответ</span>
                </button>
              </div>
              <p v-if="hwFeedbackMsg" class="hw-feedback-msg" :class="{ success: hwFeedbackSuccess, error: !hwFeedbackSuccess }">
                {{ hwFeedbackMsg }}
              </p>
            </div>
          </div>

          <!-- БЛОК ДЛЯ ПРЕПОДАВАТЕЛЯ: ВЫДАЧА ЗАДАЧИ ИЗ ЗАКРЫТОГО БАНКА -->
          <div v-if="isTeacher && isInProgressOrUnderstood && !request.homework" class="teacher-understood-alert">
            <div class="tua-header">
              <span class="tua-icon">🎓</span>
              <div>
                <strong>{{ isUnderstood ? 'Ученик подтвердил понимание темы!' : 'Закрепление темы (Закрытый банк)' }}</strong>
                <p>Выдайте проверочную задачу из закрытого банка. Только после верного решения учеником заявка будет завершена, и обоим начислятся баллы (+150 XP преподавателю / +100 XP ученику).</p>
              </div>
            </div>
            <button
              v-if="!showClosedBankSelector"
              type="button"
              class="call-done-btn"
              @click="openClosedBankAssigner"
            >
              🔒 Выбрать задачу из закрытого банка для ученика
            </button>
          </div>

          <!-- 7. БЛОК ПРОВЕРКИ И ПОДТВЕРЖДЕНИЯ УЧЕНИКОМ (ЕСЛИ ДЗ ЕЩЕ НЕ ВЫДАНО) -->
          <div v-if="!isTeacher && (isInProgress || isUnderstood) && !request.homework && (teacherResponseText || telemostLink)" class="student-review-decision-card">
            <div class="srd-header">
              <span class="srd-icon">🎓</span>
              <div>
                <strong>Разбор предоставлен преподавателем</strong>
                <p>Ознакомьтесь с объяснением. Если вам всё понятно — подтвердите это, чтобы преподаватель выдал контрольную задачу из закрытого банка. Если остались вопросы — продолжите диалог.</p>
              </div>
            </div>

            <div class="srd-actions">
              <button
                v-if="!isUnderstood"
                type="button"
                class="srd-confirm-btn"
                :disabled="closingTask"
                @click="handleStudentUnderstood"
              >
                <span v-if="closingTask">⏳ Сохранение...</span>
                <span v-else>💡 Всё понятно, готов к задаче</span>
              </button>
              <div v-else class="understood-badge-pill">
                ✓ Вы подтвердили, что всё понятно (преподаватель подбирает задачу...)
              </div>
              <button
                type="button"
                class="srd-clarify-btn"
                @click="toggleClarifyForm"
              >
                ❓ Не понял / Продолжить диалог
              </button>
            </div>

            <!-- Форма для повторного вопроса ученика по этой же заявке -->
            <div v-if="showClarifyForm" class="clarify-form-box">
              <label class="clarify-input-label">Что именно осталось непонятно? (Формула, шаг решения или чертеж):</label>
              <textarea
                v-model="clarificationInput"
                rows="3"
                class="clarify-input-area"
                placeholder="Например: Не понял переход от 2-й строки к 3-й, откуда взялся коэффициент 0.5?"
              ></textarea>
              <div class="clarify-btn-row">
                <button
                  type="button"
                  class="clarify-submit-btn"
                  :disabled="submittingClarify || !clarificationInput.trim()"
                  @click="handleSendClarify"
                >
                  <span v-if="submittingClarify">⏳ Отправка вопроса...</span>
                  <span v-else>📨 Отправить вопрос преподавателю</span>
                </button>
                <button type="button" class="clarify-cancel-btn" @click="showClarifyForm = false">
                  Отмена
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Подвал модального окна: только кнопка «Взять на разбор» если заявка открыта -->
        <div class="modal-footer" v-if="isOpen && isTeacher && !isOwnTask">
          <button type="button" class="action-btn take-btn" :disabled="taking" @click="handleTake">
            <span v-if="taking">⏳ Беру...</span>
            <span v-else>🤝 Взять на разбор</span>
            <span class="xp-tag">+25 XP</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { api } from '../services/api'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  request: { type: Object, required: true },
  viewerRole: { type: String, default: 'teacher' },
})
const emit = defineEmits(['take', 'updated'])
const auth = useAuthStore()

// Модальное окно деталей
const showDetailModal = ref(false)
const imageLoadError = ref(false)
const taking = ref(false)

// Форма письменного решения
const solutionText = ref(props.request.teacher_response || props.request.teacherResponse || '')
const solutionPhoto = ref(props.request.solution_photo_url || props.request.solutionPhotoUrl || null)
const submittingSolution = ref(false)

// Закрытый банк задач для ДЗ после Телемоста
const showClosedBankSelector = ref(false)
const loadingClosedTasks = ref(false)
const closedTasksList = ref([])
const selectedClosedTaskId = ref('')
const assigningHw = ref(false)

// Определяем, является ли зритель преподавателем
const isTeacher = computed(() => {
  if (props.viewerRole === 'student') return false
  if (props.viewerRole === 'teacher') return true
  return auth.role === 'teacher'
})

// Проверка: создал ли эту заявку текущий пользователь (человек не может брать заявку сам от себя)
const isOwnTask = computed(() => {
  const myUserId = auth.userId ? String(auth.userId) : null
  const myTgId = auth.telegramId ? String(auth.telegramId) : myUserId

  const studentId = props.request.student_id ? String(props.request.student_id) : (props.request.student?.id ? String(props.request.student.id) : null)
  const studentTgId = props.request.student?.telegram_id ? String(props.request.student.telegram_id) : (props.request.student_tg_id ? String(props.request.student_tg_id) : (props.request.studentTgId ? String(props.request.studentTgId) : null))

  if (myUserId && studentId && myUserId === studentId) return true
  if (myTgId && studentTgId && myTgId === studentTgId) return true

  const authorName = (props.request.student_name || props.request.studentName || props.request.student?.first_name || '').trim().toLowerCase()
  const myName = (auth.userName || '').trim().toLowerCase()
  if (authorName && myName && authorName === myName) return true

  return false
})

const isTelemost = computed(() => {
  const t = (props.request.request_type || props.request.requestType || '').toUpperCase()
  return t === 'TELEMOST' || t === 'SESSION' || !!props.request.telemost_url || !!props.request.telemostUrl
})

const teacherResponseText = computed(() => props.request.teacher_response || props.request.teacherResponse || '')
const telemostLink = computed(() => {
  let url = props.request.telemost_url || props.request.telemostUrl || ''
  if (url && url.includes('jit.si')) {
    const code = 7000000000 + (props.request.id * 10007) % 2000000000
    url = `https://telemost.yandex.ru/j/${code}`
  }
  return url
})
const formattedShortTime = computed(() => {
  const raw = props.request.created_at || props.request.createdAt
  if (!raw) return 'Недавно'
  try {
    const d = new Date(raw)
    if (isNaN(d.getTime())) return 'Недавно'
    const now = new Date()
    const isToday = d.toDateString() === now.toDateString()
    const hours = String(d.getHours()).padStart(2, '0')
    const mins = String(d.getMinutes()).padStart(2, '0')
    if (isToday) {
      return `Создано сегодня в ${hours}:${mins}`
    }
    const day = String(d.getDate()).padStart(2, '0')
    const month = String(d.getMonth() + 1).padStart(2, '0')
    return `Создано ${day}.${month} в ${hours}:${mins}`
  } catch {
    return 'Недавно'
  }
})

const formattedFullTime = computed(() => {
  const raw = props.request.created_at || props.request.createdAt
  if (!raw) return 'Время создания не указано'
  try {
    const d = new Date(raw)
    if (isNaN(d.getTime())) return 'Время не указано'
    return d.toLocaleString('ru-RU', {
      day: '2-digit',
      month: 'long',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return 'Время не указано'
  }
})

const showTelemostInput = ref(false)
const customTelemostInput = ref('')

const rawPhotoUrl = computed(() => props.request.photo_url || props.request.photoUrl || '')
const hasPhoto = computed(() => {
  const u = rawPhotoUrl.value
  return !!u && u.trim().length > 0 && u !== 'null' && u !== 'undefined'
})

const resolvedPhotoUrl = computed(() => {
  const u = rawPhotoUrl.value
  if (!u) return ''
  if (u.startsWith('data:image/') || u.startsWith('http://') || u.startsWith('https://')) {
    return u
  }
  if (u.startsWith('uploads/')) {
    return '/' + u
  }
  return u
})

const isOpen = computed(() => {
  const s = (props.request.status || '').toUpperCase()
  return s === 'OPEN' || s === 'NEW' || !s
})
const isInProgress = computed(() => {
  const s = (props.request.status || '').toUpperCase()
  return s === 'IN_PROGRESS' || s === 'ACCEPTED'
})
const isUnderstood = computed(() => {
  const s = (props.request.status || '').toUpperCase()
  return s === 'UNDERSTOOD'
})
const isHwIssued = computed(() => {
  const s = (props.request.status || '').toUpperCase()
  return s === 'HW_ISSUED' || !!props.request.homework
})
const isInProgressOrUnderstood = computed(() => {
  const s = (props.request.status || '').toUpperCase()
  return s === 'IN_PROGRESS' || s === 'ACCEPTED' || s === 'UNDERSTOOD' || s === 'HW_ISSUED'
})
const isCompleted = computed(() => {
  const s = (props.request.status || '').toUpperCase()
  return s === 'COMPLETED' || s === 'RESOLVED'
})

const statusLabel = computed(() => {
  const s = (props.request.status || '').toUpperCase()
  if (s === 'OPEN' || s === 'NEW') return 'Открыта'
  if (s === 'UNDERSTOOD') return '💡 Всё понятно (ждёт ДЗ)'
  if (s === 'HW_ISSUED') return '🔒 Решает ДЗ'
  if (s === 'IN_PROGRESS' || s === 'ACCEPTED') {
    if (props.request.student_clarification) return '❓ Есть вопрос ученика'
    if (teacherResponseText.value || telemostLink.value) return '⏳ На проверке'
    return 'В работе'
  }
  if (s === 'COMPLETED' || s === 'RESOLVED') return 'Решена'
  return 'Открыта'
})
const statusClass = computed(() => {
  const s = (props.request.status || '').toUpperCase()
  if (s === 'OPEN' || s === 'NEW') return 'status-open'
  if (s === 'UNDERSTOOD' || s === 'HW_ISSUED') return 'status-progress'
  if (s === 'IN_PROGRESS' || s === 'ACCEPTED') return 'status-progress'
  if (s === 'COMPLETED' || s === 'RESOLVED') return 'status-done'
  return 'status-open'
})

const gradeLabel = computed(() => {
  const g = props.request.grade || props.request.topic?.grade || 9
  if (g === 7) return '7 класс'
  if (g === 8) return '8 класс'
  return '9 класс (ОГЭ)'
})

const partLabel = computed(() => {
  const g = props.request.grade || props.request.topic?.grade || 9
  const p = props.request.part || 'PART_1'
  if (g === 9) {
    return p === 'PART_2' ? 'Часть 2 ОГЭ' : 'Часть 1 ОГЭ'
  }
  return p === 'PART_2' ? 'Повышенный уровень' : 'Базовый уровень'
})

const BLOCK_LABELS = {
  MECHANICS: '⚙️ Механика',
  THERMODYNAMICS: '🔥 Тепловые явления',
  ELECTRODYNAMICS: '⚡ Электрические явления',
  QUANTUM: '🔬 Квантовые явления',
  PART_2_ADVANCED: '⭐️ Часть 2 ОГЭ',
  MECHANICS_7: '⚙️ Механика (7 кл)',
  FORCES_7: '⚖️ Силы в природе (7 кл)',
  PRESSURE_7: '🌊 Давление и Архимед (7 кл)',
  WORK_7: '🛠️ Простые механизмы (7 кл)',
  MAGNETISM_8: '🧲 Электромагнетизм (8 кл)',
  OPTICS_8: '🔭 Оптика (8 кл)',
  WAVES_9: '🌊 Колебания и волны (9 кл)',
  ELECTROMAGNETISM_9: '⚡ Электромагнитное поле (9 кл)',
  OGE_PREP: '⭐️ Подготовка к ОГЭ',
}

const topicLabel = computed(() => {
  const title = props.request.topic_title || props.request.topic?.title
  if (title) return title
  const block = (props.request.block || props.request.subject || '').toUpperCase()
  return BLOCK_LABELS[block] || props.request.subject || 'Физика'
})

const cardClasses = computed(() => ({
  'is-urgent': props.request.is_urgent || props.request.urgent,
  'is-completed': isCompleted.value,
  'is-in-progress': isInProgress.value,
}))



// Навигация и закрытие модалки
function openDetailModal() {
  imageLoadError.value = false
  showDetailModal.value = true
}

function closeDetailModal() {
  showDetailModal.value = false
  showClosedBankSelector.value = false
  showClarifyForm.value = false
}

function handleKeydown(e) {
  if (e.key === 'Escape' && showDetailModal.value) {
    closeDetailModal()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// Быстрая комната Телемост (Яндекс Телемост)
function generateQuickRoom() {
  const roomCode = 7000000000 + (props.request.id * 10007) % 2000000000
  const link = `https://telemost.yandex.ru/j/${roomCode}`
  props.request.telemost_url = link
  props.request.telemostUrl = link
  api.submitReview(props.request.id, { telemost_url: link, status: 'IN_PROGRESS' }, auth.userId)
}

async function saveCustomTelemost() {
  const link = customTelemostInput.value.trim()
  if (!link) return
  if (!link.startsWith('http://') && !link.startsWith('https://')) {
    window.alert('⚠️ Введите корректную ссылку, например https://telemost.yandex.ru/j/...')
    return
  }
  props.request.telemost_url = link
  props.request.telemostUrl = link
  await api.submitReview(props.request.id, { telemost_url: link, status: 'IN_PROGRESS' }, auth.userId)
  showTelemostInput.value = false
  window.alert('✅ Ссылка на Яндекс Телемост успешно сохранена!')
  emit('updated')
}

// Взять задачу преподавателю
async function handleTake() {
  if (isOwnTask.value) {
    window.alert('⚠️ Преподаватель не может взять на разбор собственную заявку!')
    return
  }
  taking.value = true
  try {
    await api.acceptTask(props.request.id, auth.userId)
    props.request.status = 'in_progress'
    auth.addXp(25)
    window.alert('🎉 Вы взяли заявку на разбор (+25 XP)! Подготовьте разбор или видеовстречу.')
    emit('updated')
  } catch (e) {
    const msg = e?.message || ''
    if (msg.includes('собственн') || msg.includes('Тьютор не может') || msg.includes('не может взять')) {
      window.alert('⚠️ Преподаватель не может взять на разбор собственную заявку!')
    } else {
      props.request.status = 'in_progress'
      emit('take', props.request)
    }
  } finally {
    taking.value = false
  }
}

// Работа с фото решения преподавателя
function handleSolutionPhotoSelect(event) {
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    solutionPhoto.value = e.target.result
  }
  reader.readAsDataURL(file)
}

function removeSolutionPhoto() {
  solutionPhoto.value = null
}

// Отправка письменного решения задачи преподавателем (заявка остается IN_PROGRESS для проверки учеником)
async function submitSolution() {
  submittingSolution.value = true
  try {
    const payload = {
      teacher_response: solutionText.value.trim(),
      solution_photo_url: solutionPhoto.value || '',
      status: 'IN_PROGRESS',
    }
    await api.submitReview(props.request.id, payload, auth.userId)
    props.request.teacher_response = payload.teacher_response
    props.request.teacherResponse = payload.teacher_response
    props.request.solution_photo_url = payload.solution_photo_url
    props.request.solutionPhotoUrl = payload.solution_photo_url
    props.request.status = 'in_progress'
    alert('✅ Решение сохранено и отправлено ученику! Заявка будет закрыта, когда ученик подтвердит, что всё понятно.')
    closeDetailModal()
    emit('updated')
  } catch (err) {
    props.request.teacher_response = solutionText.value.trim()
    props.request.status = 'in_progress'
    alert('✅ Решение отправлено ученику на рассмотрение!')
    closeDetailModal()
    emit('updated')
  } finally {
    submittingSolution.value = false
  }
}

// Открытие блока выбора ДЗ из закрытого банка
async function openClosedBankAssigner() {
  showClosedBankSelector.value = true
  loadingClosedTasks.value = true
  try {
    const grade = props.request.grade || 9
    const data = await api.getClosedBankTasks(grade)
    if (data && data.length > 0) {
      closedTasksList.value = data
      selectedClosedTaskId.value = data[0].id
    } else {
      // Резервная загрузка всех закрытых задач
      const allData = await api.getClosedBankTasks()
      closedTasksList.value = allData || []
      if (allData && allData.length > 0) {
        selectedClosedTaskId.value = allData[0].id
      }
    }
  } catch (e) {
    console.warn('Не удалось загрузить закрытый банк:', e)
    closedTasksList.value = []
  } finally {
    loadingClosedTasks.value = false
  }
}

const selectedTaskPreview = computed(() => {
  if (!selectedClosedTaskId.value) return null
  return closedTasksList.value.find((t) => t.id === Number(selectedClosedTaskId.value))
})

// Назначение ДЗ из закрытого банка
async function confirmAssignHomework() {
  if (!selectedClosedTaskId.value) return
  assigningHw.value = true
  try {
    const res = await api.assignBankHomework(selectedClosedTaskId.value, props.request.id, auth.userId)
    await api.submitReview(props.request.id, {
      telemost_url: telemostLink.value,
      teacher_response: props.request.teacher_response || 'Разбор проведен. Назначена контрольная задача из закрытого банка.',
      status: 'HW_ISSUED',
    }, auth.userId)

    props.request.status = 'HW_ISSUED'
    props.request.homework = {
      id: res.homework_id,
      bank_task_id: res.bank_task_id,
      task_text: res.task_text || selectedTaskPreview.value?.statement || 'Контрольная задача из закрытого банка',
      status: 'PENDING'
    }
    alert('🔒 Задача из закрытого банка успешно назначена! Ученик получил уведомление.')
    showClosedBankSelector.value = false
    emit('updated')
  } catch (err) {
    console.error('Ошибка назначения ДЗ:', err)
    props.request.status = 'HW_ISSUED'
    alert('✅ Контрольная задача назначена ученику!')
    showClosedBankSelector.value = false
    emit('updated')
  } finally {
    assigningHw.value = false
  }
}

// Завершение звонка без ДЗ
async function completeCallWithoutHw() {
  try {
    await api.submitReview(props.request.id, {
      telemost_url: telemostLink.value,
      teacher_response: 'Видеоконсультация в Яндекс Телемосте успешно проведена.',
      status: 'IN_PROGRESS',
    }, auth.userId)

    props.request.status = 'in_progress'
    alert('✅ Видеоконсультация проведена! Ожидается подтверждение понимания от ученика.')
    showClosedBankSelector.value = false
    emit('updated')
  } catch (err) {
    props.request.status = 'in_progress'
    showClosedBankSelector.value = false
    emit('updated')
  }
}

// --- УЧЕНИК: ПОДТВЕРЖДЕНИЕ ЗАКРЫТИЯ ИЛИ ПОВТОРНЫЙ ВОПРОС ПО ЗАЯВКЕ ---
const closingTask = ref(false)
const showClarifyForm = ref(false)
const clarificationInput = ref('')
const submittingClarify = ref(false)

function toggleClarifyForm() {
  showClarifyForm.value = !showClarifyForm.value
}

// Ученик подтверждает понимание -> статус UNDERSTOOD (заявка НЕ закрывается сразу, преподаватель выдает задачу из закрытого банка)
async function handleStudentUnderstood() {
  closingTask.value = true
  try {
    const studentTgId = auth.telegramId || auth.userId
    await api.markTaskUnderstood(props.request.id, studentTgId)
    props.request.status = 'UNDERSTOOD'
    alert('💡 Отлично! Вы подтвердили, что всё понятно. Преподаватель получил уведомление и выдаст вам задачу из закрытого банка для закрепления материала.')
    emit('updated')
  } catch (err) {
    console.error('Ошибка отметки понимания:', err)
    props.request.status = 'UNDERSTOOD'
    alert('💡 Статус обновлен! Преподаватель подбирает контрольную задачу.')
    emit('updated')
  } finally {
    closingTask.value = false
  }
}

// Ученик вводит ответ на проверочную задачу из закрытого банка
const homeworkAnswerInput = ref('')
const checkingHwAnswer = ref(false)
const hwFeedbackMsg = ref('')
const hwFeedbackSuccess = ref(false)

async function handleCheckHomeworkAnswer() {
  if (!homeworkAnswerInput.value.trim()) return
  checkingHwAnswer.value = true
  hwFeedbackMsg.value = ''
  try {
    const studentTgId = auth.telegramId || auth.userId
    const res = await api.checkTaskHomework(props.request.id, homeworkAnswerInput.value.trim(), studentTgId)
    if (res.is_correct) {
      hwFeedbackSuccess.value = true
      hwFeedbackMsg.value = res.detail || '🎉 Верно! Задача решена правильно (+100 XP)!'
      if (props.request.homework) {
        props.request.homework.status = 'ACCEPTED'
      }
      props.request.status = 'COMPLETED'
      auth.addXp(100)
      alert('🎉 Поздравляем! Задача из закрытого банка решена верно! Заявка успешно закрыта, вам начислено +100 XP!')
      emit('updated')
    } else {
      hwFeedbackSuccess.value = false
      hwFeedbackMsg.value = res.detail || '❌ Неверный ответ. Попробуйте пересчитать еще раз!'
    }
  } catch (err) {
    console.error('Ошибка проверки ДЗ:', err)
    hwFeedbackSuccess.value = false
    hwFeedbackMsg.value = err?.message || 'Ошибка связи с сервером при проверке ответа.'
  } finally {
    checkingHwAnswer.value = false
  }
}

// Ученик задает уточняющий вопрос по этой же заявке
async function handleSendClarify() {
  if (!clarificationInput.value.trim()) return
  submittingClarify.value = true
  try {
    const studentTgId = auth.telegramId || auth.userId
    await api.clarifyTask(props.request.id, clarificationInput.value.trim(), studentTgId)
    props.request.student_clarification = clarificationInput.value.trim()
    alert('📨 Ваш вопрос отправлен преподавателю! Он получит уведомление и дополнит ответ.')
    showClarifyForm.value = false
    clarificationInput.value = ''
    emit('updated')
  } catch (err) {
    console.error('Ошибка отправки вопроса:', err)
    props.request.student_clarification = clarificationInput.value.trim()
    alert('📨 Вопрос отправлен преподавателю!')
    showClarifyForm.value = false
    clarificationInput.value = ''
    emit('updated')
  } finally {
    submittingClarify.value = false
  }
}

// Алиас для обратной совместимости
function confirmCompleted() {
  handleStudentUnderstood()
}
</script>

<style scoped>
.request-card {
  background: #ffffff;
  border: 1.5px solid #e2e8f0;
  border-radius: 16px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  box-sizing: border-box;
  width: 100%;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s, transform 0.15s;
}
.request-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 14px rgba(0,0,0,0.07);
}
.request-card.is-urgent { border-left: 4px solid #f59e0b; }
.request-card.is-completed { background: #fafbfc; }
.request-card.is-in-progress { border-color: #93c5fd; box-shadow: 0 0 0 3px rgba(59,130,246,0.07); }

.card-header { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
.header-tags { display: flex; gap: 5px; align-items: center; flex-wrap: wrap; }
.grade-tag { background: #fef3c7; color: #92400e; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 100px; }
.topic-tag { background: #e0e7ff; color: #3730a3; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 100px; }
.format-tag { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 100px; }
.format-tag.telemost { background: #fee2e2; color: #b91c1c; }
.format-tag.task { background: #e0f2fe; color: #0369a1; }
.part-tag { background: #f1f5f9; color: #475569; font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 100px; }
.status-badge { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 100px; white-space: nowrap; }
.status-badge.status-open { background: #dcfce7; color: #15803d; }
.status-badge.status-progress { background: #fef3c7; color: #b45309; }
.status-badge.status-done { background: #f1f5f9; color: #64748b; }

.card-body { display: flex; flex-direction: column; gap: 8px; }
.card-title { margin: 0; font-size: 15px; font-weight: 700; color: #0f172a; line-height: 1.4; word-break: break-word; }
.card-desc { margin: 0; font-size: 13px; color: #475569; line-height: 1.45; word-break: break-word; }

/* Индикатор фото в ленте */
.photo-preview-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  width: fit-content;
}
.photo-preview-pill:hover { background: #f1f5f9; border-color: #94a3b8; }
.cam-icon { font-size: 14px; }
.cam-text { font-size: 11px; font-weight: 600; color: #475569; }
.cam-action { font-size: 11px; font-weight: 700; color: #3b82f6; }

.card-meta { display: flex; gap: 12px; font-size: 12px; color: #94a3b8; flex-wrap: wrap; align-items: center; }
.meta-item { white-space: nowrap; }
.open-card-hint { margin-left: auto; color: #6366f1; font-weight: 600; font-size: 11px; cursor: pointer; }
.open-card-hint:hover { text-decoration: underline; }

.teacher-response-box { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; padding: 10px 12px; }
.resp-header { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #166534; margin-bottom: 4px; }
.resp-text { margin: 0; font-size: 13px; line-height: 1.5; color: #14532d; white-space: pre-wrap; }
.sol-attached-hint { margin-top: 4px; font-size: 11px; color: #15803d; font-weight: 600; }

.telemost-card-box { background: #eff6ff; border: 1.5px solid #93c5fd; border-radius: 10px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.tm-header { display: flex; align-items: center; gap: 8px; }
.tm-icon { font-size: 18px; }
.tm-info { display: flex; flex-direction: column; }
.tm-info strong { font-size: 12px; color: #1e3a8a; }
.tm-info span { font-size: 11px; color: #64748b; }
.tm-join-btn { background: #3b82f6; color: white; text-decoration: none; font-size: 12px; font-weight: 700; padding: 5px 12px; border-radius: 100px; }

.feed-clarification-box {
  background: #fffbeb;
  border: 1.5px solid #fde68a;
  border-radius: 10px;
  padding: 8px 12px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.fc-icon { font-size: 16px; line-height: 1.2; }
.fc-content strong { font-size: 11px; color: #92400e; display: block; margin-bottom: 2px; }
.fc-text { margin: 0; font-size: 12px; color: #78350f; font-style: italic; }

.check-solution-btn {
  background: #4f46e5;
  color: white;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
}
.check-solution-btn:hover { background: #4338ca; }

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  border-top: 1px solid #f1f5f9;
  padding-top: 10px;
  flex-wrap: wrap;
}
.card-created-time {
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f8fafc;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}
.card-footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-left: auto;
}
.action-btn { border: none; font-family: inherit; font-size: 12px; font-weight: 700; padding: 8px 14px; border-radius: 100px; cursor: pointer; transition: all 0.15s ease; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
.take-btn { background: #ef7d34; color: white; box-shadow: 0 2px 8px rgba(239,125,52,0.35); }
.take-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.answer-btn { background: #6366f1; color: white; box-shadow: 0 2px 8px rgba(99,102,241,0.25); }
.chat-btn { background: #f1f5f9; color: #334155; border: 1.5px solid #e2e8f0; }
.complete-btn { background: #10b981; color: white; box-shadow: 0 2px 8px rgba(16,185,129,0.25); }
.xp-tag { background: rgba(255,255,255,0.25); font-size: 10px; padding: 1px 5px; border-radius: 100px; }
.student-hint { font-size: 12px; color: #94a3b8; font-weight: 500; }
.own-task-pill {
  background: #f8fafc;
  color: #475569;
  border: 1px dashed #cbd5e1;
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
}
.completed-label { font-size: 12px; color: #10b981; font-weight: 700; }

/* ========================================================= */
/* СТИЛИ МОДАЛЬНОГО ОКНА ДЛЯ ОТКРЫТОЙ КАРТОЧКИ               */
/* ========================================================= */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(5px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  box-sizing: border-box;
}

.detail-modal {
  background: #ffffff;
  width: 100%;
  max-width: 620px;
  max-height: 90vh;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.28);
  overflow: hidden;
  animation: modalPop 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalPop {
  from { opacity: 0; transform: scale(0.96) translateY(12px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.modal-tags { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.modal-close-btn {
  background: #f1f5f9;
  border: none;
  font-size: 18px;
  font-weight: 700;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  transition: all 0.15s;
  flex-shrink: 0;
}
.modal-close-btn:hover { background: #e2e8f0; color: #0f172a; }

.modal-body {
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-title { margin: 0; font-size: 18px; font-weight: 700; color: #0f172a; line-height: 1.4; }
.modal-question-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: #334155;
  white-space: pre-wrap;
  background: #f8fafc;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

/* Фото условия */
.modal-photo-block { display: flex; flex-direction: column; gap: 8px; }
.photo-block-header { display: flex; justify-content: space-between; align-items: center; }
.photo-title { font-size: 13px; font-weight: 700; color: #1e293b; }
.photo-zoom-btn { font-size: 12px; color: #3b82f6; text-decoration: none; font-weight: 600; }
.photo-zoom-btn:hover { text-decoration: underline; }
.photo-wrapper {
  border-radius: 12px;
  overflow: hidden;
  border: 1.5px solid #cbd5e1;
  background: #f8fafc;
  max-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.full-photo-img { width: 100%; height: auto; max-height: 300px; object-fit: contain; display: block; }
.photo-error-box { padding: 20px; display: flex; flex-direction: column; align-items: center; gap: 6px; color: #64748b; text-align: center; }
.photo-error-box .error-icon { font-size: 28px; }
.photo-error-box p { margin: 0; font-size: 12px; }

.modal-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  background: #f8fafc;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
}
.meta-cell { display: flex; flex-direction: column; gap: 2px; }
.meta-label { font-size: 11px; color: #94a3b8; font-weight: 500; }
.meta-val { font-size: 13px; color: #1e293b; font-weight: 600; }

/* БЛОК ВВОДА РЕШЕНИЯ ПРЕПОДАВАТЕЛЕМ */
.teacher-solution-editor {
  background: #fff8f3;
  border: 1.5px solid #fed7aa;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.editor-header { display: flex; align-items: flex-start; gap: 10px; }
.ed-icon { font-size: 24px; line-height: 1; }
.editor-header strong { font-size: 14px; color: #9a3412; }
.editor-header p { margin: 2px 0 0; font-size: 12px; color: #c2410c; }

.editor-field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: 12px; font-weight: 700; color: #475569; }

.solution-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border: 1.5px solid #fdba74;
  border-radius: 10px;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.5;
  background: #ffffff;
  outline: none;
  resize: vertical;
}
.solution-textarea:focus { border-color: #ea580c; box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.15); }

.upload-solution-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: #ffffff;
  border: 1.5px dashed #fdba74;
  border-radius: 10px;
  cursor: pointer;
  color: #9a3412;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.15s;
}
.upload-solution-label:hover { background: #fffaf5; border-color: #ea580c; }
.up-icon { font-size: 18px; }

.solution-photo-preview {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.solution-thumb-img {
  width: 100%;
  max-height: 200px;
  object-fit: contain;
  border-radius: 10px;
  border: 1px solid #fed7aa;
  background: white;
}
.del-solution-photo-btn {
  align-self: flex-start;
  background: #fee2e2;
  color: #991b1b;
  border: none;
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.submit-solution-btn {
  background: #ea580c;
  color: white;
  border: none;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  padding: 12px 18px;
  border-radius: 100px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(234, 88, 12, 0.25);
  transition: all 0.15s;
  width: 100%;
}
.submit-solution-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.submit-solution-btn:active:not(:disabled) { transform: scale(0.98); }

/* БЛОК ТЕЛЕМОСТА И ИТОГОВ ЗВОНКА */
.modal-telemost-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.tm-alert-box {
  background: #eff6ff;
  border: 1.5px solid #93c5fd;
  border-radius: 14px;
  padding: 14px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.tm-icon-large { font-size: 28px; line-height: 1; }
.tm-details strong { font-size: 14px; color: #1e3a8a; }
.tm-details p { margin: 4px 0 10px; font-size: 12px; color: #475569; }
.tm-actions-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.tm-connect-btn {
  background: #3b82f6;
  color: white;
  text-decoration: none;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 16px;
  border-radius: 100px;
}
.tm-create-btn {
  background: #2563eb;
  color: white;
  border: none;
  font-size: 12px;
  font-weight: 700;
  padding: 8px 14px;
  border-radius: 100px;
  cursor: pointer;
}
.tm-instruction-box {
  background: #ffffff;
  border-radius: 8px;
  padding: 8px 12px;
  margin: 6px 0 10px;
  border-left: 3px solid #3b82f6;
  border: 1px solid #bfdbfe;
}
.tm-step {
  margin: 4px 0 !important;
  font-size: 12px !important;
  color: #1e293b !important;
  line-height: 1.4 !important;
}
.tm-open-link-btn.primary {
  background: #2563eb;
  color: white;
  border: none;
  font-weight: 700;
}
.tm-edit-link-btn {
  background: transparent;
  color: #2563eb;
  border: 1px solid #93c5fd;
  font-size: 12px;
  font-weight: 600;
  padding: 7px 12px;
  border-radius: 100px;
  cursor: pointer;
}
.tm-custom-input-box {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  width: 100%;
}
.tm-custom-input {
  flex: 1;
  padding: 8px 12px;
  border: 1.5px solid #93c5fd;
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  background: white;
}
.tm-save-custom-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.call-finished-container { margin-top: 4px; }
.call-done-btn {
  background: #0284c7;
  color: white;
  border: none;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  padding: 11px 16px;
  border-radius: 100px;
  cursor: pointer;
  box-shadow: 0 3px 10px rgba(2, 132, 199, 0.25);
  width: 100%;
}
.call-done-btn:active { transform: scale(0.98); }

/* ЗАКРЫТЫЙ БАНК: НАЗНАЧЕНИЕ ДЗ */
.closed-bank-modal-box {
  background: #f8faff;
  border: 2px solid #818cf8;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.12);
}
.closed-box-header { display: flex; align-items: flex-start; gap: 10px; }
.lock-icon { font-size: 24px; line-height: 1; }
.closed-box-header strong { font-size: 14px; color: #312e81; }
.closed-box-header p { margin: 2px 0 0; font-size: 12px; color: #4338ca; }
.close-selector-btn {
  margin-left: auto;
  background: rgba(99, 102, 241, 0.1);
  border: none;
  font-size: 13px;
  color: #4338ca;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  cursor: pointer;
}

.select-closed-input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px;
  border: 1.5px solid #c7d2fe;
  border-radius: 10px;
  font-family: inherit;
  font-size: 13px;
  background: white;
}

.closed-task-preview-card {
  background: white;
  border: 1px solid #e0e7ff;
  border-radius: 10px;
  padding: 12px;
  margin-top: 8px;
}
.closed-task-preview-card h4 { margin: 0 0 6px; font-size: 13px; color: #1e1b4b; }
.ct-statement { margin: 0 0 6px; font-size: 12px; color: #334155; line-height: 1.4; }
.ct-diff-tag { font-size: 10px; font-weight: 700; color: #4f46e5; background: #eef2ff; padding: 2px 6px; border-radius: 100px; }

.closed-assign-actions { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
.assign-hw-btn {
  background: #4f46e5;
  color: white;
  border: none;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  padding: 11px 16px;
  border-radius: 100px;
  cursor: pointer;
  box-shadow: 0 3px 10px rgba(79, 70, 229, 0.3);
}
.assign-hw-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.skip-hw-btn {
  background: #f1f5f9;
  border: none;
  color: #475569;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  padding: 8px;
  border-radius: 100px;
  cursor: pointer;
}

/* ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ РАЗБОРА */
.modal-response-block { background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 12px; padding: 14px; }
.mresp-header { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #166534; margin-bottom: 6px; }
.mresp-text { margin: 0; font-size: 14px; line-height: 1.55; color: #14532d; white-space: pre-wrap; }

.solution-photo-block { margin-top: 10px; border-top: 1px dashed #86efac; padding-top: 8px; }
.sol-photo-bar { display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 700; color: #166534; margin-bottom: 6px; }
.sol-photo-bar .zoom-btn { font-size: 11px; color: #2563eb; text-decoration: none; }
.sol-full-photo { width: 100%; max-height: 320px; object-fit: contain; border-radius: 8px; border: 1px solid #bbf7d0; background: white; }

/* БАННЕР УТОЧНЕНИЯ В МОДАЛЬНОМ ОКНЕ */
.modal-clarification-banner {
  background: #fffbeb;
  border: 1.5px solid #fde68a;
  border-radius: 12px;
  padding: 12px 14px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.mcb-icon { font-size: 20px; line-height: 1; }
.mcb-content strong { font-size: 13px; color: #92400e; display: block; margin-bottom: 3px; }
.mcb-text { margin: 0; font-size: 13px; color: #78350f; font-style: italic; line-height: 1.45; }
.mcb-hint { display: block; margin-top: 6px; font-size: 11px; color: #b45309; font-weight: 600; }

/* БЛОК ПРОВЕРКИ И РЕШЕНИЯ ДЛЯ УЧЕНИКА */
.student-review-decision-card {
  background: #f8faff;
  border: 2px solid #818cf8;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.12);
}
.srd-header { display: flex; align-items: flex-start; gap: 10px; }
.srd-icon { font-size: 24px; line-height: 1; }
.srd-header strong { font-size: 14px; color: #312e81; }
.srd-header p { margin: 3px 0 0; font-size: 12px; color: #4338ca; line-height: 1.4; }

.srd-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.srd-confirm-btn {
  background: #10b981;
  color: white;
  border: none;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  padding: 11px 18px;
  border-radius: 100px;
  cursor: pointer;
  box-shadow: 0 3px 10px rgba(16, 185, 129, 0.3);
  transition: all 0.15s;
  flex: 1;
  min-width: 200px;
}
.srd-confirm-btn:hover:not(:disabled) { background: #059669; }
.srd-confirm-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.srd-clarify-btn {
  background: #ffffff;
  color: #4338ca;
  border: 1.5px solid #c7d2fe;
  font-family: inherit;
  font-size: 13px;
  font-weight: 700;
  padding: 11px 18px;
  border-radius: 100px;
  cursor: pointer;
  transition: all 0.15s;
}
.srd-clarify-btn:hover { background: #eef2ff; border-color: #818cf8; }

.clarify-form-box {
  background: #ffffff;
  border: 1.5px solid #c7d2fe;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}
.clarify-input-label { font-size: 12px; font-weight: 700; color: #312e81; }
.clarify-input-area {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border: 1.5px solid #c7d2fe;
  border-radius: 8px;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.45;
  outline: none;
  resize: vertical;
}
.clarify-input-area:focus { border-color: #4f46e5; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15); }
.clarify-btn-row { display: flex; gap: 8px; align-items: center; }
.clarify-submit-btn {
  background: #4f46e5;
  color: white;
  border: none;
  font-family: inherit;
  font-size: 12px;
  font-weight: 700;
  padding: 9px 16px;
  border-radius: 100px;
  cursor: pointer;
  transition: all 0.15s;
}
.clarify-submit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.clarify-cancel-btn {
  background: #f1f5f9;
  color: #475569;
  border: none;
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  padding: 9px 14px;
  border-radius: 100px;
  cursor: pointer;
}

.clarify-toggle-btn {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}
.clarify-toggle-btn:hover { background: #fecaca; }

.modal-footer {
  padding: 14px 20px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  align-items: center;
  background: #fafafa;
}
.close-modal-btn {
  background: #f1f5f9;
  color: #475569;
  font-weight: 700;
  border: 1px solid #cbd5e1;
}
.close-modal-btn:hover { background: #e2e8f0; color: #0f172a; }

/* Закрытый банк: проверочная задача и решение учеником */
.assigned-hw-block {
  background: #fefce8;
  border: 2px solid #facc15;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.hw-header { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #854d0e; font-weight: 700; }
.hw-text { margin: 0; font-size: 13px; line-height: 1.5; color: #713f12; white-space: pre-wrap; }
.hw-status-row { display: flex; gap: 8px; align-items: center; }
.hw-status-tag { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 100px; background: #fed7aa; color: #9a3412; }
.hw-status-tag.ACCEPTED { background: #dcfce7; color: #166534; }

.hw-student-solve-box {
  margin-top: 8px;
  background: #ffffff;
  border: 1.5px solid #fde047;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.hw-input-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.hw-answer-input {
  flex: 1;
  min-width: 140px;
  padding: 10px 14px;
  border: 1.5px solid #cbd5e1;
  border-radius: 10px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  outline: none;
}
.hw-answer-input:focus { border-color: #eab308; box-shadow: 0 0 0 3px rgba(234, 179, 8, 0.2); }
.hw-check-btn {
  background: #eab308;
  color: #713f12;
  font-family: inherit;
  font-weight: 800;
  font-size: 13px;
  border: none;
  border-radius: 10px;
  padding: 10px 18px;
  cursor: pointer;
  transition: all 0.15s;
}
.hw-check-btn:hover:not(:disabled) { background: #ca8a04; color: #ffffff; }
.hw-check-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.hw-feedback-msg { margin: 0; font-size: 12px; font-weight: 700; padding: 6px 10px; border-radius: 8px; }
.hw-feedback-msg.success { background: #dcfce7; color: #166534; }
.hw-feedback-msg.error { background: #fee2e2; color: #991b1b; }

/* Уведомление преподавателя об ответе «Всё понятно» */
.teacher-understood-alert {
  background: #f0fdf4;
  border: 2px solid #4ade80;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.tua-header { display: flex; align-items: flex-start; gap: 10px; }
.tua-icon { font-size: 24px; line-height: 1; }
.tua-header strong { font-size: 14px; color: #166534; display: block; }
.tua-header p { margin: 4px 0 0; font-size: 12px; color: #15803d; line-height: 1.45; }

.understood-badge-pill {
  background: #dcfce7;
  color: #166534;
  font-size: 12px;
  font-weight: 700;
  padding: 10px 16px;
  border-radius: 100px;
  border: 1px solid #86efac;
}
</style>
