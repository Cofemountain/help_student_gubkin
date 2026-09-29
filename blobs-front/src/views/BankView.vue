<template>
  <div class="bank-view">
    <!-- Шапка банка задач и базы знаний -->
    <header class="bank-hero">
      <div class="hero-info">
        <span class="bank-badge">📚 Банк заданий и База знаний • Физика</span>
        <h1>Банк задач и решений</h1>
        <p class="subtitle">
          Изучайте подробные методические разборы задач из сборника А. В. Перышкина с формулами и чертежами или тренируйтесь в экзаменационном практикуме.
        </p>
      </div>

      <!-- Статистика -->
      <div class="hero-stats">
        <div class="stat-pill highlight">
          <span class="val">{{ solvedTasks.length }}</span>
          <span class="lbl">Разобрано задач</span>
        </div>
        <div class="stat-pill">
          <span class="val">{{ practiceSolvedCount }}</span>
          <span class="lbl">Решено в тесте</span>
        </div>
        <div class="stat-pill xp-pill">
          <span class="val">+{{ earnedXp }} XP</span>
          <span class="lbl">Получено опыта</span>
        </div>
      </div>
    </header>

    <!-- Переключатель режимов: База знаний (Решённые задачи) vs Тренажёр -->
    <div class="mode-tabs">
      <button
        type="button"
        class="mode-tab-btn"
        :class="{ active: activeMode === 'solved' }"
        @click="activeMode = 'solved'"
      >
        <span class="tab-icon">💡</span>
        <span class="tab-title-full">База разобранных задач</span>
        <span class="tab-title-short">Разборы</span>
        <span class="tab-counter">{{ solvedTasks.length }}</span>
      </button>
      <button
        type="button"
        class="mode-tab-btn"
        :class="{ active: activeMode === 'practice' }"
        @click="activeMode = 'practice'"
      >
        <span class="tab-icon">🎯</span>
        <span class="tab-title-full">Открытый практикум</span>
        <span class="tab-title-short">Практикум</span>
        <span class="tab-badge-xp">+15 XP</span>
      </button>
      <button
        v-if="auth.role === 'teacher'"
        type="button"
        class="mode-tab-btn"
        :class="{ active: activeMode === 'closed' }"
        @click="switchModeToClosed"
      >
        <span class="tab-icon">🔒</span>
        <span class="tab-title-full">Закрытый банк задач</span>
        <span class="tab-title-short">Закрытый банк</span>
        <span class="tab-badge-xp closed-xp">+25 XP</span>
      </button>
    </div>

    <!-- ============================================================ -->
    <!-- РЕЖИМ 1: БАЗА РАЗОБРАННЫХ ЗАДАЧ (РЕШЁННЫЕ ЗАЯВКИ С РАЗБОРАМИ) -->
    <!-- ============================================================ -->
    <section v-if="activeMode === 'solved'" class="solved-section">
      <!-- Поисковая строка -->
      <div class="search-container">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="Поиск по условию, формулам, закону или теме..."
            @input="onSearchInput"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="clear-search-btn"
            title="Очистить поиск"
            @click="clearSearch"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- Фильтры: Класс и Тематические разделы -->
      <div class="filters-panel">
        <div class="filter-group">
          <span class="filter-label">Класс:</span>
          <div class="grade-chips">
            <button
              class="chip-btn"
              :class="{ active: selectedGrade === null }"
              @click="selectGrade(null)"
            >
              Все классы
            </button>
            <button
              v-for="g in [7, 8, 9]"
              :key="g"
              class="chip-btn"
              :class="{ active: selectedGrade === g }"
              @click="selectGrade(g)"
            >
              {{ g }} класс
            </button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-label">Раздел физики:</span>
          <div class="block-chips">
            <button
              class="chip-btn sm"
              :class="{ active: selectedBlock === null }"
              @click="selectBlock(null)"
            >
              Все темы
            </button>
            <button
              v-for="b in blocks"
              :key="b.key"
              class="chip-btn sm"
              :class="{ active: selectedBlock === b.key }"
              @click="selectBlock(b.key)"
            >
              {{ b.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Индикатор загрузки -->
      <div v-if="loadingSolved" class="loader-box">
        <div class="spinner"></div>
        <p>Загрузка разобранных задач из банка...</p>
      </div>

      <!-- Пустое состояние -->
      <div v-else-if="filteredSolvedTasks.length === 0" class="empty-box">
        <div class="empty-icon">📂</div>
        <h3>Разобранных задач не найдено</h3>
        <p v-if="searchQuery || selectedGrade || selectedBlock">
          По вашему запросу нет готовых решений. Попробуйте изменить фильтры или сбросить поиск.
        </p>
        <p v-else>
          В банке пока нет завершенных разборов.
        </p>
        <button
          v-if="searchQuery || selectedGrade || selectedBlock"
          type="button"
          class="reset-filters-btn"
          @click="resetFilters"
        >
          Сбросить все фильтры
        </button>
      </div>

      <!-- Список карточек разобранных задач -->
      <div v-else class="solved-tasks-grid">
        <article
          v-for="task in filteredSolvedTasks"
          :key="task.id"
          class="solved-card"
          @click="openSolutionModal(task)"
        >
          <!-- Шапка карточки -->
          <div class="sc-header">
            <div class="sc-tags">
              <span class="tag-grade">{{ getGradeLabel(task.grade) }}</span>
              <span class="tag-topic">{{ getTopicTitle(task) }}</span>
              <span class="tag-part">{{ getPartLabel(task) }}</span>
            </div>
            <span class="verified-badge">
              <span class="v-icon">✓</span> Разбор готов
            </span>
          </div>

          <!-- Источник / Автор задачи -->
          <div class="sc-author-pill">
            <span class="book-icon-sm">📖</span>
            <span class="author-text">Автор: А. В. Перышкин («Сборник задач по физике 7–9 кл.»)</span>
          </div>

          <!-- Условие задачи -->
          <div class="sc-statement-block">
            <h3 class="sc-title">
              {{ task.question || 'Задание по физике' }}
            </h3>

            <!-- Превью фото условия задачи, если прикреплено -->
            <div
              v-if="hasConditionPhoto(task)"
              class="condition-photo-pill"
              @click.stop="openLightbox(getPhotoUrl(task.photo_url), 'Иллюстрация к условию задачи #' + task.id)"
            >
              <div class="cpp-thumb">
                <img :src="getPhotoUrl(task.photo_url)" alt="Условие" />
              </div>
              <div class="cpp-info">
                <span class="cpp-label">📷 Прикреплена схема / рисунок к условию</span>
                <span class="cpp-action">Смотреть в полном размере ↗</span>
              </div>
            </div>
          </div>

          <!-- Короткое превью разбора -->
          <div class="sc-solution-preview">
            <div class="preview-tutor-row">
              <span class="system-icon">🤖</span>
              <strong class="tutor-name">Разбор: Система</strong>
              <span class="sol-date">{{ formatDateTime(task.updated_at || task.created_at) }}</span>
            </div>
            <p class="preview-snippet">
              {{ getSolutionSnippet(task.teacher_response) }}
            </p>
          </div>

          <!-- Кнопка перехода к читабельному полному разбору -->
          <div class="sc-footer" @click.stop>
            <button
              type="button"
              class="open-solution-btn"
              @click="openSolutionModal(task)"
            >
              <span>📖 Читать методический разбор</span>
              <span class="btn-arrow">→</span>
            </button>
            <span class="task-id-badge">#{{ task.id }}</span>
          </div>
        </article>
      </div>
    </section>

    <!-- ============================================================ -->
    <!-- РЕЖИМ 2: ЭКЗАМЕНАЦИОННЫЙ ПРАКТИКУМ ФИПИ (ТРЕНАЖЁР)           -->
    <!-- ============================================================ -->
    <section v-else-if="activeMode === 'practice'" class="practice-section">
      <!-- Поисковая строка Открытого практикума -->
      <div class="search-container">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input
            v-model="practiceSearchQuery"
            type="text"
            class="search-input"
            placeholder="Поиск по условию, формулам, закону или теме..."
          />
          <button
            v-if="practiceSearchQuery"
            type="button"
            class="clear-search-btn"
            title="Очистить поиск"
            @click="practiceSearchQuery = ''"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- Фильтры тренажера -->
      <div class="filters-panel">
        <div class="filter-group">
          <span class="filter-label">Класс:</span>
          <div class="grade-chips">
            <button
              class="chip-btn"
              :class="{ active: practiceGrade === null }"
              @click="selectPracticeGrade(null)"
            >
              Все классы
            </button>
            <button
              v-for="g in [7, 8, 9]"
              :key="g"
              class="chip-btn"
              :class="{ active: practiceGrade === g }"
              @click="selectPracticeGrade(g)"
            >
              {{ g }} класс
            </button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-label">Раздел:</span>
          <div class="block-chips">
            <button
              class="chip-btn sm"
              :class="{ active: practiceBlock === null }"
              @click="selectPracticeBlock(null)"
            >
              Все темы
            </button>
            <button
              v-for="b in blocks"
              :key="b.key"
              class="chip-btn sm"
              :class="{ active: practiceBlock === b.key }"
              @click="selectPracticeBlock(b.key)"
            >
              {{ b.label }}
            </button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-label">Сложность:</span>
          <div class="diff-chips">
            <button
              class="chip-btn xs"
              :class="{ active: selectedDifficulty === null }"
              @click="selectedDifficulty = null"
            >
              Все
            </button>
            <button
              v-for="d in ['Базовый', 'Средний', 'Сложный']"
              :key="d"
              class="chip-btn xs"
              :class="{ active: selectedDifficulty === d }"
              @click="selectedDifficulty = d"
            >
              {{ d }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="loadingPractice" class="loader-box">
        <div class="spinner"></div>
        <p>Загрузка задач практикума...</p>
      </div>

      <div v-else-if="filteredPracticeTasks.length === 0" class="empty-box">
        <p>По выбранным фильтрам тренировочных задач пока нет.</p>
      </div>

      <div v-else class="tasks-list">
        <div
          v-for="task in filteredPracticeTasks"
          :key="task.id"
          class="task-card"
          :class="{ 'is-solved': solvedMap[task.id] }"
        >
          <div class="task-header">
            <div class="task-tags">
              <span class="tag-grade">{{ task.grade }} класс</span>
              <span class="tag-diff" :class="(task.difficulty || '').toLowerCase()">{{ task.difficulty }}</span>
              <span class="tag-topic">{{ task.topic_title }}</span>
              <span class="tag-author">
                {{ getTaskAuthor(task).includes('Камзеева') || getTaskAuthor(task).includes('ФИПИ') ? '🏛️' : '📖' }} {{ getTaskAuthor(task) }}
              </span>
            </div>
            <span v-if="solvedMap[task.id]" class="solved-badge">✓ Решено (+15 XP)</span>
          </div>

          <h3 class="task-title">{{ task.title }}</h3>
          <p class="task-statement">{{ task.statement }}</p>

          <!-- Блок проверки ответа -->
          <div class="answer-box">
            <div v-if="!solvedMap[task.id]" class="input-row">
              <input
                v-model="answers[task.id]"
                type="text"
                placeholder="Ваш ответ (число)..."
                class="answer-input"
                @keyup.enter="checkPracticeTask(task)"
              />
              <button
                type="button"
                class="check-btn"
                :disabled="checking[task.id] || !answers[task.id]"
                @click="checkPracticeTask(task)"
              >
                {{ checking[task.id] ? '...' : 'Проверить' }}
              </button>
            </div>

            <!-- Результат проверки -->
            <div
              v-if="results[task.id]"
              class="result-message"
              :class="{ success: results[task.id].is_correct, error: !results[task.id].is_correct }"
            >
              {{ results[task.id].message }}
            </div>

            <!-- Подсказка / Решение -->
            <div class="task-actions-row">
              <button
                v-if="task.hint && !showHint[task.id]"
                type="button"
                class="hint-btn"
                @click="showHint[task.id] = true"
              >
                💡 Подсказка
              </button>
              <p v-if="showHint[task.id]" class="hint-text">
                <strong>Подсказка:</strong> {{ task.hint }}
              </p>

              <button
                type="button"
                class="create-req-from-task-btn"
                @click="createRequestFromTask(task)"
                title="Сформировать заявку на разбор по этой задаче"
              >
                ✍️ Сформировать заявку
              </button>

              <button
                v-if="solvedMap[task.id] && !showSolution[task.id]"
                type="button"
                class="solution-btn"
                @click="showSolution[task.id] = true"
              >
                📖 Показать подробное решение
              </button>
              <div v-if="showSolution[task.id]" class="solution-text">
                <strong>Эталонное решение:</strong>
                <p>{{ task.solution || results[task.id]?.solution || 'Решение доступно в материалах темы.' }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================ -->
    <!-- РЕЖИМ 3: ЗАКРЫТЫЙ БАНК ЗАДАЧ (АНТИ-ГДЗ, ДЗ И ПРОВЕРОЧНЫЕ)    -->
    <!-- ============================================================ -->
    <section v-if="activeMode === 'closed'" class="practice-section closed-section">
      <div class="closed-banner-alert">
        <span class="cba-icon">🔒</span>
        <div class="cba-content">
          <strong>Закрытый банк задач ОГЭ и контрольных заданий</strong>
          <p>Задачи без готовых решений в сети из сборников А. В. Перышкина и ФИПИ Е. Е. Камзеевой. Решайте самостоятельно для проверки своих сил (+25 XP) или сформируйте заявку на консультацию с преподавателем.</p>
        </div>
      </div>

      <!-- Поисковая строка Закрытого банка -->
      <div class="search-container">
        <div class="search-box">
          <span class="search-icon">🔍</span>
          <input
            v-model="closedSearchQuery"
            type="text"
            class="search-input"
            placeholder="Поиск проверочных задач по формулам, теме или номеру..."
          />
          <button
            v-if="closedSearchQuery"
            type="button"
            class="clear-search-btn"
            title="Очистить поиск"
            @click="closedSearchQuery = ''"
          >
            ✕
          </button>
        </div>
      </div>

      <div class="practice-filters">
        <div class="filter-group">
          <span class="filter-label">Класс:</span>
          <div class="grade-chips">
            <button
              class="chip-btn"
              :class="{ active: closedGrade === null }"
              @click="selectClosedGrade(null)"
            >
              Все классы
            </button>
            <button
              v-for="g in [7, 8, 9]"
              :key="g"
              class="chip-btn"
              :class="{ active: closedGrade === g }"
              @click="selectClosedGrade(g)"
            >
              {{ g }} класс
            </button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-label">Раздел:</span>
          <div class="block-chips">
            <button
              class="chip-btn sm"
              :class="{ active: closedBlock === null }"
              @click="selectClosedBlock(null)"
            >
              Все темы
            </button>
            <button
              v-for="b in blocks"
              :key="b.key"
              class="chip-btn sm"
              :class="{ active: closedBlock === b.key }"
              @click="selectClosedBlock(b.key)"
            >
              {{ b.label }}
            </button>
          </div>
        </div>

        <div class="filter-group">
          <span class="filter-label">Сложность:</span>
          <div class="diff-chips">
            <button
              class="chip-btn xs"
              :class="{ active: selectedClosedDifficulty === null }"
              @click="selectedClosedDifficulty = null"
            >
              Все
            </button>
            <button
              v-for="d in ['Базовый', 'Средний', 'Повышенный']"
              :key="d"
              class="chip-btn xs"
              :class="{ active: selectedClosedDifficulty === d }"
              @click="selectedClosedDifficulty = d"
            >
              {{ d }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="loadingClosed" class="loader-box">
        <div class="spinner"></div>
        <p>Загрузка задач из закрытого банка...</p>
      </div>

      <div v-else-if="filteredClosedTasks.length === 0" class="empty-box">
        <p>В закрытом банке по выбранным фильтрам пока нет задач.</p>
      </div>

      <div v-else class="tasks-list">
        <div
          v-for="task in filteredClosedTasks"
          :key="task.id"
          class="task-card closed-task-card"
          :class="{ 'is-solved': closedSolvedMap[task.id] }"
        >
          <div class="task-header">
            <div class="task-tags">
              <span class="tag-grade">{{ task.grade }} класс</span>
              <span class="tag-diff" :class="(task.difficulty || '').toLowerCase()">{{ task.difficulty }}</span>
              <span class="tag-topic">{{ task.topic_title }}</span>
              <span class="tag-author">
                {{ getTaskAuthor(task).includes('Камзеева') || getTaskAuthor(task).includes('ФИПИ') ? '🏛️' : '📖' }} {{ getTaskAuthor(task) }}
              </span>
            </div>
            <span v-if="closedSolvedMap[task.id]" class="solved-badge closed-solved">✓ Решено верно (+25 XP)</span>
          </div>

          <h3 class="task-title">{{ task.title }}</h3>
          <p class="task-statement">{{ task.statement }}</p>

          <!-- Блок проверки ответа на закрытую задачу -->
          <div class="answer-box">
            <div v-if="!closedSolvedMap[task.id]" class="input-row">
              <input
                v-model="closedAnswers[task.id]"
                type="text"
                placeholder="Ваш числовой ответ..."
                class="answer-input"
                @keyup.enter="checkClosedTask(task)"
              />
              <button
                type="button"
                class="check-btn closed-check-btn"
                :disabled="closedChecking[task.id] || !closedAnswers[task.id]"
                @click="checkClosedTask(task)"
              >
                {{ closedChecking[task.id] ? '...' : 'Проверить ответ' }}
              </button>
            </div>

            <!-- Результат проверки -->
            <div
              v-if="closedResults[task.id]"
              class="result-message"
              :class="{ success: closedResults[task.id].is_correct, error: !closedResults[task.id].is_correct }"
            >
              {{ closedResults[task.id].message }}
            </div>

            <!-- Подсказка / Решение / Сформировать заявку -->
            <div class="task-actions-row">
              <button
                v-if="task.hint && !closedShowHint[task.id]"
                type="button"
                class="hint-btn"
                @click="closedShowHint[task.id] = true"
              >
                💡 Подсказка
              </button>
              <p v-if="closedShowHint[task.id]" class="hint-text">
                <strong>Подсказка:</strong> {{ task.hint }}
              </p>

              <button
                type="button"
                class="create-req-from-task-btn"
                @click="createRequestFromTask(task)"
                title="Сформировать заявку на разбор по этой задаче"
              >
                ✍️ Сформировать заявку
              </button>

              <button
                v-if="closedSolvedMap[task.id] && !closedShowSolution[task.id]"
                type="button"
                class="solution-btn"
                @click="closedShowSolution[task.id] = true"
              >
                📖 Показать авторское решение
              </button>
              <div v-if="closedShowSolution[task.id]" class="solution-text">
                <strong>Эталонное решение и ход вычислений:</strong>
                <p>{{ task.solution || closedResults[task.id]?.solution || 'Решение доступно после проверки.' }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================ -->
    <!-- БОЛЬШОЕ ЧИТАБЕЛЬНОЕ МОДАЛЬНОЕ ОКНО РАЗБОРА ЗАДАЧИ             -->
    <!-- ============================================================ -->
    <div
      v-if="activeSolutionTask"
      class="solution-modal-overlay"
      @click.self="closeSolutionModal"
    >
      <div class="solution-modal">
        <!-- Шапка окна -->
        <div class="sm-header">
          <div class="sm-tags">
            <span class="tag-grade">{{ getGradeLabel(activeSolutionTask.grade) }}</span>
            <span class="tag-topic">{{ getTopicTitle(activeSolutionTask) }}</span>
            <span class="tag-part">{{ getPartLabel(activeSolutionTask) }}</span>
            <span class="sm-verified-pill">✓ Проверенный разбор</span>
          </div>
          <button
            type="button"
            class="sm-close-btn"
            title="Закрыть разбор (Esc)"
            @click="closeSolutionModal"
          >
            ✕
          </button>
        </div>

        <div class="sm-body">
          <!-- Источник: А. В. Перышкин -->
          <div class="sm-author-banner">
            <span class="book-badge-icon">📖</span>
            <div class="author-info">
              <strong>Автор задачи: А. В. Перышкин</strong>
              <span>«Сборник задач по физике. 7–9 классы», издательство «Экзамен»</span>
            </div>
          </div>

          <!-- Блок условия задания -->
          <div class="sm-task-box">
            <h2 class="sm-task-title">
              {{ activeSolutionTask.question }}
            </h2>

            <!-- Реальная иллюстрация из книги -->
            <div
              v-if="hasConditionPhoto(activeSolutionTask)"
              class="sm-photo-container"
            >
              <div class="sm-photo-header">
                <span>📷 Иллюстрация / схема к задаче из сборника Перышкина</span>
                <button
                  type="button"
                  class="photo-zoom-link"
                  @click="openLightbox(getPhotoUrl(activeSolutionTask.photo_url), 'Иллюстрация к задаче #' + activeSolutionTask.id)"
                >
                  🔍 В полный размер
                </button>
              </div>
              <div
                class="sm-img-wrapper"
                @click="openLightbox(getPhotoUrl(activeSolutionTask.photo_url), 'Иллюстрация к задаче #' + activeSolutionTask.id)"
              >
                <img
                  :src="getPhotoUrl(activeSolutionTask.photo_url)"
                  alt="Иллюстрация к задаче"
                  class="sm-illustration"
                />
              </div>
            </div>
          </div>

          <!-- Методический разбор: Система -->
          <div class="sm-solution-card">
            <div class="sm-solution-header">
              <div class="system-author-row">
                <span class="sys-robot-icon">🤖</span>
                <div class="sys-info">
                  <strong class="sys-title">Методический разбор: Система</strong>
                  <span class="sys-subtitle">Автоматизированная база знаний платформы ОГЭ Физика</span>
                </div>
              </div>
            </div>

            <!-- Текст решения с красивым форматированием (без \n) -->
            <div class="sm-solution-body">
              <div
                class="clean-solution-text"
                v-html="renderSolutionHtml(activeSolutionTask.teacher_response)"
              ></div>
            </div>
          </div>
        </div>

        <!-- Подвал окна -->
        <div class="sm-footer">
          <button
            type="button"
            class="sm-btn-close"
            @click="closeSolutionModal"
          >
            Закрыть окно
          </button>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- МОДАЛЬНОЕ ОКНО LIGHTBOX (ПРОСМОТР ФОТО В ПОЛНОМ РАЗМЕРЕ)    -->
    <!-- ============================================================ -->
    <div
      v-if="lightbox.isOpen"
      class="lightbox-overlay"
      @click.self="closeLightbox"
    >
      <div class="lightbox-modal">
        <div class="lightbox-header">
          <span class="lightbox-title">{{ lightbox.title }}</span>
          <div class="lightbox-actions">
            <a
              :href="lightbox.imageUrl"
              target="_blank"
              rel="noopener"
              class="lightbox-ext-link"
              title="Открыть в новой вкладке"
            >
              ↗ В новой вкладке
            </a>
            <button
              type="button"
              class="lightbox-close-btn"
              title="Закрыть (Esc)"
              @click="closeLightbox"
            >
              ✕
            </button>
          </div>
        </div>
        <div class="lightbox-body">
          <img :src="lightbox.imageUrl" :alt="lightbox.title" class="lightbox-img" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

// Режим: 'solved' (База разобранных задач), 'practice' (Открытый банк) или 'closed' (Закрытый банк для преподавателей)
const activeMode = ref('solved')

function getTaskAuthor(task) {
  if (!task) return 'А. В. Пёрышкин'
  if (task.author && task.author.trim()) return task.author.trim()
  const g = task.grade || 7
  if (g === 9 || (task.topic_title && task.topic_title.includes('ОГЭ')) || (task.title && task.title.includes('ОГЭ'))) {
    return 'ФИПИ (ОГЭ, Е. Е. Камзеева)'
  }
  return 'А. В. Пёрышкин'
}

const blocks = [
  { key: 'MECHANICS', label: '⚙️ Механика' },
  { key: 'THERMODYNAMICS', label: '🔥 Тепловые явления' },
  { key: 'ELECTRODYNAMICS', label: '⚡ Электрические явления' },
  { key: 'QUANTUM', label: '🔬 Квантовые' },
  { key: 'PART_2_ADVANCED', label: '⭐️ 2-я часть ОГЭ' },
]

// --- Состояние для Базы разобранных задач ---
const solvedTasks = ref([])
const loadingSolved = ref(true)
const searchQuery = ref('')
const selectedGrade = ref(null)
const selectedBlock = ref(null)

// Активная задача для большого модального окна разбора
const activeSolutionTask = ref(null)

function openSolutionModal(task) {
  activeSolutionTask.value = task
}

function closeSolutionModal() {
  activeSolutionTask.value = null
}

// --- Состояние для Практикума (Тренажера) ---
const practiceTasks = ref([])
const loadingPractice = ref(false)
const practiceSearchQuery = ref('')
const practiceGrade = ref(null)
const practiceBlock = ref(null)
const selectedDifficulty = ref(null)
const answers = reactive({})
const checking = reactive({})
const results = reactive({})
const solvedMap = reactive({})
const showHint = reactive({})
const showSolution = reactive({})
const practiceSolvedCount = ref(0)
const earnedXp = ref(0)

// --- Lightbox модальное окно для фотографий ---
const lightbox = reactive({
  isOpen: false,
  imageUrl: '',
  title: '',
})

function openLightbox(url, title = 'Просмотр изображения') {
  if (!url) return
  lightbox.imageUrl = url
  lightbox.title = title
  lightbox.isOpen = true
}

function closeLightbox() {
  lightbox.isOpen = false
  lightbox.imageUrl = ''
}

function handleKeydown(e) {
  if (e.key === 'Escape') {
    if (lightbox.isOpen) {
      closeLightbox()
    } else if (activeSolutionTask.value) {
      closeSolutionModal()
    }
  }
}

onMounted(() => {
  if (auth.role !== 'teacher' && activeMode.value === 'closed') {
    activeMode.value = 'practice'
  }
  window.addEventListener('keydown', handleKeydown)
  loadSolvedTasks()
  loadPracticeTasks()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

// --- Загрузка решённых заявок из API ---
let searchDebounceTimer = null
function onSearchInput() {
  clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    loadSolvedTasks()
  }, 350)
}

function clearSearch() {
  searchQuery.value = ''
  loadSolvedTasks()
}

function resetFilters() {
  searchQuery.value = ''
  selectedGrade.value = null
  selectedBlock.value = null
  loadSolvedTasks()
}

function selectGrade(grade) {
  selectedGrade.value = grade
  loadSolvedTasks()
}

function selectBlock(blockKey) {
  selectedBlock.value = blockKey
  loadSolvedTasks()
}

async function loadSolvedTasks() {
  loadingSolved.value = true
  try {
    const data = await api.getSolvedBankTasks(
      selectedGrade.value,
      selectedBlock.value,
      searchQuery.value
    )
    solvedTasks.value = data || []
  } catch (err) {
    console.error('Ошибка загрузки разобранных задач:', err)
    solvedTasks.value = []
  } finally {
    loadingSolved.value = false
  }
}

// Фильтрованные решённые задачи (клиентская дополнительная фильтрация)
const filteredSolvedTasks = computed(() => {
  return solvedTasks.value
})

// Хелперы для отображения данных разобранных задач
function getGradeLabel(grade) {
  if (grade === 7) return '7 класс'
  if (grade === 8) return '8 класс'
  return '9 класс (ОГЭ)'
}

function getPartLabel(task) {
  const isPart2 = task.part === 'PART_2'
  if (task.grade === 9) {
    return isPart2 ? 'Часть 2 ОГЭ' : 'Часть 1 ОГЭ'
  }
  return isPart2 ? 'Повышенный уровень' : 'Базовый уровень'
}

function getTopicTitle(task) {
  if (task.topic?.title) return task.topic.title
  const blockMap = {
    MECHANICS: '⚙️ Механика',
    THERMODYNAMICS: '🔥 Тепловые явления',
    ELECTRODYNAMICS: '⚡ Электрические явления',
    QUANTUM: '🔬 Квантовые явления',
    PART_2_ADVANCED: '⭐️ Часть 2 ОГЭ',
    PRESSURE_7: '🌊 Давление жидкостей',
    WORK_7: '🛠️ Простые механизмы',
  }
  const b = task.topic?.block || task.block
  return blockMap[b] || 'Физика'
}

function hasConditionPhoto(task) {
  const p = task.photo_url
  return !!(p && p.trim().length > 0 && p !== 'null' && p !== 'undefined')
}

function hasSolutionPhoto(task) {
  const s = task.solution_photo_url
  return !!(s && s.trim().length > 0 && s !== 'null' && s !== 'undefined')
}

function getPhotoUrl(url) {
  if (!url) return ''
  if (url.startsWith('data:image/') || url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  if (url.startsWith('uploads/')) {
    return '/' + url
  }
  return url
}

function formatDateTime(dtStr) {
  if (!dtStr) return 'Недавно'
  try {
    const d = new Date(dtStr)
    return d.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
    })
  } catch {
    return 'Недавно'
  }
}

// Превью текста решения для карточки (2-3 строки)
function getSolutionSnippet(rawText) {
  if (!rawText) return 'Нажмите, чтобы открыть подробное пошаговое решение.'
  const clean = rawText.replace(/\\n/g, '\n').trim()
  const lines = clean.split('\n').filter((l) => l.trim().length > 0)
  // Ищем строку с решением или формулой
  const firstMeaningful = lines.find(
    (l) => !l.startsWith('📖') && !l.startsWith('Дано') && !l.startsWith('•')
  ) || lines[0] || ''
  return firstMeaningful.length > 120 ? firstMeaningful.slice(0, 120) + '...' : firstMeaningful
}

// Красивый рендеринг текста решения в читабельном окне
function renderSolutionHtml(rawText) {
  if (!rawText) return '<p>Методический разбор подготавливается.</p>'

  // Убираем литеральные \n если они были экранированы
  let text = String(rawText).replace(/\\n/g, '\n').trim()

  // Экранирование HTML
  text = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Разделяем на параграфы
  const lines = text.split('\n')
  const htmlParts = []

  let inSection = false
  for (let line of lines) {
    line = line.trim()
    if (!line) {
      htmlParts.push('<div class="spacer"></div>')
      continue
    }

    if (line.startsWith('📖 Автор') || line.startsWith('📖 Источник')) {
      // Уже отображается в верхней плашке
      continue
    } else if (line.startsWith('Дано:')) {
      htmlParts.push('<div class="sol-section-header">📋 Дано:</div>')
    } else if (line.startsWith('Решение:')) {
      htmlParts.push('<div class="sol-section-header">✏️ Пошаговое решение:</div>')
    } else if (line.startsWith('Ответ:')) {
      htmlParts.push(`<div class="sol-answer-callout"><strong>${line}</strong></div>`)
    } else if (line.startsWith('•')) {
      htmlParts.push(`<div class="sol-dano-item">${line}</div>`)
    } else if (/^[0-9]+\)/.test(line)) {
      htmlParts.push(`<div class="sol-step-item"><strong>${line.slice(0, 3)}</strong> ${line.slice(3)}</div>`)
    } else {
      htmlParts.push(`<div class="sol-text-line">${line}</div>`)
    }
  }

  return htmlParts.join('')
}

// --- Логика Практикума (Тренажера) ---
function selectPracticeGrade(g) {
  practiceGrade.value = g
  loadPracticeTasks()
}

function selectPracticeBlock(b) {
  practiceBlock.value = b
  loadPracticeTasks()
}

async function loadPracticeTasks() {
  loadingPractice.value = true
  try {
    const data = await api.getOpenBankTasks(practiceGrade.value, practiceBlock.value)
    practiceTasks.value = data || []
  } catch (e) {
    console.warn('Не удалось загрузить задачи практикума:', e)
    practiceTasks.value = []
  } finally {
    loadingPractice.value = false
  }
}

const filteredPracticeTasks = computed(() => {
  let list = practiceTasks.value
  if (selectedDifficulty.value) {
    list = list.filter(
      (t) => (t.difficulty || '').toLowerCase() === selectedDifficulty.value.toLowerCase()
    )
  }
  const q = (practiceSearchQuery.value || '').trim().toLowerCase()
  if (q) {
    list = list.filter((t) => {
      const title = (t.title || '').toLowerCase()
      const statement = (t.statement || '').toLowerCase()
      const topic = (t.topic_title || '').toLowerCase()
      const author = (t.author || '').toLowerCase()
      return title.includes(q) || statement.includes(q) || topic.includes(q) || author.includes(q)
    })
  }
  return list
})

async function checkPracticeTask(task) {
  const ans = answers[task.id]
  if (!ans || checking[task.id]) return

  checking[task.id] = true
  try {
    const studentTgId = auth.telegramId || auth.userId
    const res = await api.checkAnswer(task.id, ans, studentTgId)
    results[task.id] = res

    if (res.is_correct) {
      solvedMap[task.id] = true
      practiceSolvedCount.value += 1
      earnedXp.value += 15
      auth.addXp(15, 'bank_solved')
      showSolution[task.id] = true
    }
  } catch (e) {
    console.error('Ошибка проверки:', e)
    const normUser = String(ans).trim().toLowerCase().replace(',', '.')
    const normTarget = String(task.answer || '').trim().toLowerCase().replace(',', '.')
    const isCorrect = normUser === normTarget

    results[task.id] = {
      is_correct: isCorrect,
      message: isCorrect
        ? '🎉 Верно! Ответ совпал с эталоном (+15 XP).'
        : '❌ Ответ не совпадает с эталоном. Попробуйте пересчитать или используйте подсказку.',
      solution: task.solution,
    }

    if (isCorrect) {
      solvedMap[task.id] = true
      practiceSolvedCount.value += 1
      earnedXp.value += 15
      auth.addXp(15, 'bank_solved')
      showSolution[task.id] = true
    }
  } finally {
    checking[task.id] = false
  }
}

// --- Логика Закрытого банка задач ---
const closedTasks = ref([])
const loadingClosed = ref(false)
const closedSearchQuery = ref('')
const closedGrade = ref(null)
const closedBlock = ref(null)
const selectedClosedDifficulty = ref(null)
const closedAnswers = reactive({})
const closedChecking = reactive({})
const closedResults = reactive({})
const closedSolvedMap = reactive({})
const closedShowHint = reactive({})
const closedShowSolution = reactive({})

function switchModeToClosed() {
  if (auth.role !== 'teacher') {
    activeMode.value = 'practice'
    return
  }
  activeMode.value = 'closed'
  if (closedTasks.value.length === 0) {
    loadClosedTasks()
  }
}

function selectClosedGrade(g) {
  closedGrade.value = g
  loadClosedTasks()
}

function selectClosedBlock(b) {
  closedBlock.value = b
  loadClosedTasks()
}

async function loadClosedTasks() {
  loadingClosed.value = true
  try {
    const data = await api.getClosedBankTasksForStudents(closedGrade.value, closedBlock.value)
    closedTasks.value = data || []
  } catch (e) {
    console.warn('Не удалось загрузить задачи закрытого банка:', e)
    closedTasks.value = []
  } finally {
    loadingClosed.value = false
  }
}

const filteredClosedTasks = computed(() => {
  let list = closedTasks.value
  if (selectedClosedDifficulty.value) {
    list = list.filter(
      (t) => (t.difficulty || '').toLowerCase() === selectedClosedDifficulty.value.toLowerCase()
    )
  }
  const q = (closedSearchQuery.value || '').trim().toLowerCase()
  if (q) {
    list = list.filter((t) => {
      const title = (t.title || '').toLowerCase()
      const statement = (t.statement || '').toLowerCase()
      const topic = (t.topic_title || '').toLowerCase()
      const author = (t.author || '').toLowerCase()
      return title.includes(q) || statement.includes(q) || topic.includes(q) || author.includes(q)
    })
  }
  return list
})

async function checkClosedTask(task) {
  const ans = closedAnswers[task.id]
  if (!ans || closedChecking[task.id]) return

  closedChecking[task.id] = true
  try {
    const studentTgId = auth.telegramId || auth.userId
    const res = await api.checkAnswer(task.id, ans, studentTgId)
    closedResults[task.id] = res

    if (res.is_correct) {
      closedSolvedMap[task.id] = true
      practiceSolvedCount.value += 1
      earnedXp.value += 25
      auth.addXp(25, 'closed_bank_solved')
      closedShowSolution[task.id] = true
    }
  } catch (e) {
    console.error('Ошибка проверки задачи закрытого банка:', e)
    const normUser = String(ans).trim().toLowerCase().replace(',', '.')
    const normTarget = String(task.answer || '').trim().toLowerCase().replace(',', '.')
    const isCorrect = normUser === normTarget

    closedResults[task.id] = {
      is_correct: isCorrect,
      message: isCorrect
        ? '🎉 Верно! Задача из закрытого банка решена (+25 XP)!'
        : '❌ Ответ не совпадает с эталоном. Попробуйте пересчитать или обратитесь за помощью к преподавателю.',
      solution: task.solution,
    }

    if (isCorrect) {
      closedSolvedMap[task.id] = true
      practiceSolvedCount.value += 1
      earnedXp.value += 25
      auth.addXp(25, 'closed_bank_solved')
      closedShowSolution[task.id] = true
    }
  } finally {
    closedChecking[task.id] = false
  }
}

function createRequestFromTask(task) {
  const authorText = task.author ? ` (Источник: ${task.author})` : ''
  const queryText = `[${task.title}] ${task.statement}${authorText}`
  router.push({
    path: '/create-request',
    query: {
      grade: task.grade,
      block: task.block,
      text: queryText,
    }
  })
}
</script>

<style scoped>
.bank-view {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 0 4px calc(130px + env(safe-area-inset-bottom, 24px));
}

/* ШАПКА */
.bank-hero {
  background: linear-gradient(135deg, #111827 0%, #1e293b 60%, #0f172a 100%);
  color: white;
  padding: 20px 24px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.bank-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(8px);
  color: #fbbf24;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.03em;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  border: 1px solid rgba(251, 191, 36, 0.3);
  margin-bottom: var(--space-2);
}

.hero-info h1 {
  margin: 0 0 6px 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.01em;
}

.subtitle {
  margin: 0;
  font-size: 13.5px;
  opacity: 0.88;
  line-height: 1.45;
  color: #cbd5e1;
}

.hero-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.stat-pill {
  flex: 1;
  min-width: 110px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  text-align: center;
  display: flex;
  flex-direction: column;
}

.stat-pill.highlight {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
}
.stat-pill.highlight .val {
  color: #60a5fa;
}

.stat-pill.xp-pill {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.4);
}
.stat-pill.xp-pill .val {
  color: #fbbf24;
}

.stat-pill .val {
  font-size: 20px;
  font-weight: 800;
}
.stat-pill .lbl {
  font-size: 10.5px;
  opacity: 0.75;
  margin-top: 2px;
}

/* ПЕРЕКЛЮЧАТЕЛЬ РЕЖИМОВ */
.mode-tabs {
  display: flex;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 4px;
  border-radius: var(--radius-lg);
  gap: 4px;
  width: 100%;
  box-sizing: border-box;
}

.mode-tab-btn {
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 8px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.tab-title-full {
  display: inline;
}

.tab-title-short {
  display: none;
}

.mode-tab-btn:hover {
  color: #0f172a;
  background: rgba(255, 255, 255, 0.6);
}

.mode-tab-btn.active {
  background: white;
  color: #0f172a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.tab-icon {
  font-size: 16px;
}

.tab-counter {
  background: #e2e8f0;
  color: #1e293b;
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: var(--radius-pill);
}

.mode-tab-btn.active .tab-counter {
  background: #3b82f6;
  color: white;
}

.tab-badge-xp {
  background: #fef3c7;
  color: #b45309;
  font-size: 11px;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: var(--radius-pill);
  border: 1px solid #fde68a;
}

@media (max-width: 640px) {
  .mode-tabs {
    gap: 3px;
    padding: 3px;
  }
  .mode-tab-btn {
    padding: 8px 4px;
    font-size: 11px;
    gap: 3px;
  }
  .tab-title-full {
    display: none;
  }
  .tab-title-short {
    display: inline;
    font-size: 11px;
    font-weight: 700;
  }
  .tab-badge-xp, .tab-counter {
    font-size: 9.5px;
    padding: 1px 4px;
  }
  .tab-icon {
    font-size: 13px;
  }
}

/* СЕКЦИИ И ПОИСК */
.solved-section,
.practice-section,
.closed-section {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.search-container {
  margin-top: 2px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  background: white;
  border: 1.5px solid #cbd5e1;
  border-radius: var(--radius-md);
  padding: 2px 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-box:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.search-icon {
  font-size: 15px;
  color: #64748b;
  margin-right: 8px;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 11px 0;
  font-size: 14px;
  color: #0f172a;
  outline: none;
}

.search-input::placeholder {
  color: #94a3b8;
}

.clear-search-btn {
  background: #e2e8f0;
  border: none;
  color: #475569;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.clear-search-btn:hover {
  background: #cbd5e1;
  color: #0f172a;
}

/* ФИЛЬТРЫ */
.filters-panel,
.practice-filters {
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: #f8fafc;
  padding: 16px 18px;
  border-radius: var(--radius-lg);
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
}

.filter-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  font-weight: 700;
  color: #475569;
  min-width: 80px;
}

.grade-chips, .block-chips, .diff-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip-btn {
  background: white;
  border: 1px solid #cbd5e1;
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chip-btn:hover {
  border-color: #94a3b8;
  color: #0f172a;
}

.chip-btn.active {
  background: #0f172a;
  border-color: #0f172a;
  color: white;
}

.chip-btn.sm {
  font-size: 11.5px;
  padding: 4px 10px;
}

.chip-btn.xs {
  font-size: 11px;
  padding: 3px 9px;
}

/* КАРТОЧКА РАЗОБРАННОЙ ЗАДАЧИ В СПИСКЕ */
.solved-tasks-grid {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.solved-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
  display: flex;
  flex-direction: column;
  gap: 14px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.solved-card:hover {
  transform: translateY(-2px);
  border-color: #93c5fd;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.08);
}

.sc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.sc-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.tag-grade {
  background: #e0e7ff;
  color: #3730a3;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}

.tag-topic {
  background: #f1f5f9;
  color: #334155;
  font-size: 11.5px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}

.tag-part {
  background: #fef3c7;
  color: #92400e;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}

.verified-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: var(--radius-pill);
}

.v-icon {
  color: #059669;
  font-weight: 800;
}

/* АВТОР / ИСТОЧНИК */
.sc-author-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f8fafc;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border-left: 3px solid #6366f1;
}

.book-icon-sm {
  font-size: 13px;
}

.author-text {
  font-size: 11.5px;
  font-weight: 600;
  color: #475569;
}

/* УСЛОВИЕ */
.sc-statement-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sc-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.45;
}

/* ПРЕВЬЮ ФОТО */
.condition-photo-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-md);
  padding: 6px 10px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.condition-photo-pill:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.cpp-thumb {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: white;
  border: 1px solid #cbd5e1;
  flex-shrink: 0;
}

.cpp-thumb img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.cpp-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.cpp-label {
  font-size: 12px;
  font-weight: 700;
  color: #1e293b;
}

.cpp-action {
  font-size: 11px;
  color: #3b82f6;
  font-weight: 600;
}

/* ПРЕВЬЮ РАЗБОРА В КАРТОЧКЕ */
.sc-solution-preview {
  background: #f8fafc;
  border-left: 3px solid #10b981;
  padding: 8px 12px;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-tutor-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
}

.system-icon {
  font-size: 13px;
}

.preview-tutor-row strong {
  color: #0f172a;
}

.sol-date {
  color: #94a3b8;
  margin-left: auto;
}

.preview-snippet {
  margin: 0;
  font-size: 12.5px;
  color: #334155;
  line-height: 1.4;
}

/* ПОДВАЛ КАРТОЧКИ */
.sc-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #f1f5f9;
  padding-top: 10px;
}

.open-solution-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #0f172a;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: var(--radius-md);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.open-solution-btn:hover {
  background: #2563eb;
  transform: translateX(2px);
}

.btn-arrow {
  transition: transform 0.15s;
}
.open-solution-btn:hover .btn-arrow {
  transform: translateX(3px);
}

.task-id-badge {
  font-size: 11px;
  color: #94a3b8;
  font-family: monospace;
}

/* ============================================================ */
/* БОЛЬШОЕ ЧИТАБЕЛЬНОЕ МОДАЛЬНОЕ ОКНО РАЗБОРА                   */
/* ============================================================ */
.solution-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(5px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  animation: fadeIn 0.2s ease;
}

.solution-modal {
  background: white;
  border-radius: var(--radius-xl, 16px);
  max-width: 760px;
  width: 100%;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.sm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.sm-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.sm-verified-pill {
  background: #ecfdf5;
  color: #047857;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  border: 1px solid #a7f3d0;
}

.sm-close-btn {
  background: #e2e8f0;
  border: none;
  color: #475569;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.sm-close-btn:hover {
  background: #cbd5e1;
  color: #0f172a;
}

.sm-body {
  padding: 20px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* БАННЕР АВТОРА */
.sm-author-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-left: 4px solid #4f46e5;
  padding: 10px 14px;
  border-radius: var(--radius-md);
}

.book-badge-icon {
  font-size: 24px;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-info strong {
  font-size: 13.5px;
  color: #1e293b;
}

.author-info span {
  font-size: 12px;
  color: #64748b;
}

/* УСЛОВИЕ В МОДАЛКЕ */
.sm-task-box {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-lg);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sm-task-title {
  margin: 0;
  font-size: 16.5px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.5;
}

.sm-photo-container {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.sm-photo-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f1f5f9;
  font-size: 11.5px;
  font-weight: 700;
  color: #475569;
  border-bottom: 1px solid #e2e8f0;
}

.photo-zoom-link {
  background: transparent;
  border: none;
  color: #2563eb;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
}
.photo-zoom-link:hover {
  text-decoration: underline;
}

.sm-img-wrapper {
  padding: 16px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-in;
}

.sm-illustration {
  max-width: 100%;
  max-height: 260px;
  object-fit: contain;
}

/* БОЛЬШОЙ БЛОК МЕТОДИЧЕСКОГО РАЗБОРА */
.sm-solution-card {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-left: 5px solid #10b981;
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sm-solution-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 12px;
}

.system-author-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sys-robot-icon {
  font-size: 26px;
}

.sys-info {
  display: flex;
  flex-direction: column;
}

.sys-title {
  font-size: 14.5px;
  font-weight: 800;
  color: #0f172a;
}

.sys-subtitle {
  font-size: 11.5px;
  color: #64748b;
}

.sm-solution-body {
  font-size: 14.5px;
  line-height: 1.65;
  color: #1e293b;
}

/* Стили читабельного текста решения */
.clean-solution-text :deep(.sol-section-header) {
  font-size: 14px;
  font-weight: 800;
  color: #1e293b;
  margin-top: 10px;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.clean-solution-text :deep(.sol-dano-item) {
  font-family: inherit;
  padding-left: 8px;
  margin-bottom: 2px;
  color: #334155;
  font-weight: 500;
}

.clean-solution-text :deep(.sol-step-item) {
  margin: 6px 0;
  padding-left: 4px;
  color: #0f172a;
}

.clean-solution-text :deep(.sol-text-line) {
  margin: 4px 0;
}

.clean-solution-text :deep(.sol-answer-callout) {
  background: #ecfdf5;
  border: 1.5px solid #10b981;
  color: #065f46;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  margin-top: 14px;
  font-size: 14px;
}

.clean-solution-text :deep(.spacer) {
  height: 6px;
}

.sm-sol-photo {
  background: white;
  border: 1px solid #cbd5e1;
  border-radius: var(--radius-md);
  padding: 10px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.sm-sol-photo img {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
}

.sm-footer {
  display: flex;
  justify-content: flex-end;
  padding: 14px 20px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}

.sm-btn-close {
  background: #0f172a;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.sm-btn-close:hover {
  background: #334155;
}

/* ТРЕНАЖЕР / ПРАКТИКУМ */
.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.task-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card.is-solved {
  border-color: #a7f3d0;
  background: #f0fdf4;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag-diff {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: var(--radius-pill);
  background: #e2e8f0;
  color: #475569;
}

.tag-diff.базовый {
  background: #dcfce7;
  color: #166534;
}

.tag-diff.средний {
  background: #fef9c3;
  color: #854d0e;
}

.tag-diff.сложный {
  background: #fee2e2;
  color: #991b1b;
}

.solved-badge {
  background: #059669;
  color: white;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}

.tag-author {
  background: #ede9fe;
  color: #5b21b6;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  border: 1px solid #ddd6fe;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  white-space: nowrap;
}

.task-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.task-statement {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: #334155;
}

.answer-box {
  background: #f8fafc;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  box-sizing: border-box;
}

.input-row {
  display: flex;
  align-items: stretch;
  gap: 8px;
  width: 100%;
  box-sizing: border-box;
}

.answer-input {
  flex: 1 1 0%;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  padding: 9px 12px;
  border: 1.5px solid #cbd5e1;
  border-radius: var(--radius-sm);
  font-size: 14px;
  outline: none;
  background: #ffffff;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.answer-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.check-btn {
  flex-shrink: 0;
  white-space: nowrap;
  background: #0f172a;
  color: white;
  border: none;
  padding: 9px 16px;
  border-radius: var(--radius-sm);
  font-size: 13.5px;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}
.check-btn:hover:not(:disabled) {
  background: #1e293b;
}
.check-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .task-card {
    padding: 14px 14px;
  }
  .answer-box {
    padding: 10px 10px;
  }
}

.result-message {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
}
.result-message.success {
  background: #dcfce7;
  color: #166534;
}
.result-message.error {
  background: #fee2e2;
  color: #991b1b;
}

.task-actions-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hint-btn, .solution-btn {
  background: transparent;
  border: 1px solid #cbd5e1;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  align-self: flex-start;
}

.hint-text {
  margin: 0;
  font-size: 12.5px;
  color: #b45309;
  background: #fffbeb;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
}

.solution-text {
  background: white;
  border: 1px solid #cbd5e1;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  line-height: 1.5;
}

/* ЗАГРУЗКА И ПУСТОТА */
.loader-box, .empty-box {
  background: white;
  border: 1px dashed #cbd5e1;
  border-radius: var(--radius-lg);
  padding: 40px 20px;
  text-align: center;
  color: #64748b;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 36px;
}

.empty-box h3 {
  margin: 0;
  font-size: 17px;
  color: #0f172a;
}

.empty-box p {
  margin: 0;
  font-size: 13px;
  max-width: 440px;
  line-height: 1.5;
}

.reset-filters-btn {
  background: #0f172a;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
}

/* LIGHTBOX MODAL */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(6px);
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  animation: fadeIn 0.2s ease;
}

.lightbox-modal {
  background: #1e293b;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
}

.lightbox-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: #0f172a;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.lightbox-title {
  color: white;
  font-size: 13px;
  font-weight: 600;
}

.lightbox-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lightbox-ext-link {
  color: #60a5fa;
  font-size: 12px;
  text-decoration: none;
  font-weight: 600;
}
.lightbox-ext-link:hover {
  text-decoration: underline;
}

.lightbox-close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.lightbox-close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.lightbox-body {
  padding: 16px;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f172a;
}

.lightbox-img {
  max-width: 100%;
  max-height: 75vh;
  object-fit: contain;
  border-radius: var(--radius-sm);
  background: white;
  padding: 4px;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 640px) {
  .hero-stats {
    flex-direction: column;
  }
  .mode-tab-btn {
    font-size: 12px;
    padding: 8px 10px;
  }
  .filter-label {
    min-width: 100%;
  }
  .sc-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .solution-modal {
    max-height: 96vh;
  }
  .sm-body {
    padding: 14px 16px;
  }
}

/* ЗАКРЫТЫЙ БАНК И АВТОРСТВО */
.closed-banner-alert {
  background: #fefce8;
  border: 1.5px solid #facc15;
  border-radius: var(--radius-md);
  padding: 14px 18px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: var(--space-3);
}
.cba-icon {
  font-size: 24px;
  line-height: 1;
}
.cba-content strong {
  display: block;
  font-size: 14px;
  color: #854d0e;
  margin-bottom: 3px;
}
.cba-content p {
  margin: 0;
  font-size: 12.5px;
  color: #713f12;
  line-height: 1.45;
}

.closed-badge {
  background: #fef08a !important;
  color: #854d0e !important;
  font-weight: 800 !important;
}

.tag-author {
  background: #f8fafc;
  color: #1e293b;
  font-weight: 700;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.closed-task-card {
  border-left: 4px solid #eab308 !important;
}

.closed-solved {
  background: #fef08a !important;
  color: #854d0e !important;
  font-weight: 800;
}

.closed-check-btn {
  background: #eab308 !important;
  color: #713f12 !important;
  font-weight: 800;
}
.closed-check-btn:hover:not(:disabled) {
  background: #ca8a04 !important;
  color: white !important;
}

.create-req-from-task-btn {
  background: #f0fdf4;
  color: #166534;
  border: 1.5px solid #bbf7d0;
  font-family: inherit;
  font-size: 12px;
  font-weight: 700;
  padding: 7px 14px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
}
.create-req-from-task-btn:hover {
  background: #dcfce7;
  border-color: #86efac;
}
</style>
