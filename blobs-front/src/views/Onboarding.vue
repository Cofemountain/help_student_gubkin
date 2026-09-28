<template>
  <div class="onb-wrapper">
    <!-- ВЫНОСИМ КНОПКУ СЮДА, ЧТОБЫ ОНА БЫЛА ПО ВСЕМУ ЭКРАНУ -->
    <button class="skip" @click="skip">Пропустить</button>

    <div class="onb-card">
      <div class="stage">
        <svg viewBox="0 0 120 120" width="120" height="120" aria-hidden="true">
          <path d="M60 8 C90 8 112 30 112 60 C112 95 88 112 60 112 C30 112 8 92 8 60 C8 30 30 8 60 8 Z" fill="var(--ink)"/>
          <circle cx="46" cy="58" r="6" fill="#fff"/><circle cx="74" cy="58" r="6" fill="#fff"/>
        </svg>
        <h1 class="title">{{ slides[idx].title }}</h1>
        <p class="text">{{ slides[idx].text }}</p>
      </div>

      <div class="footer">
        <div class="dots">
          <span v-for="(s, i) in slides" :key="i" class="dot" :class="{ on: i === idx }"></span>
        </div>
        <BaseButton variant="primary" size="lg" class="cta" rounded @click="next">
          {{ isLast ? 'Начать' : 'Далее' }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import BaseButton from '../components/BaseButton.vue' // Не забудь импорт компонента кнопки!

const router = useRouter()

// Данные слайдов
const slides = [
  { title: 'Blobs — взаимопомощь по математике',
    text: 'Застрял на домашке? Не мучайся один: опиши задачу — и преподаватель поможет.' },
  { title: 'Как это работает',
    text: 'Ученик кидает заявку → преподаватель нажимает «Взять задачу» → вы дописываетесь в личку и решаете пример.' },
  { title: 'Преподавателям',
    text: 'Помогай, зарабатывай очки и расти в званиях. Первая помощь — уже опыт.' },
]

const idx = ref(0) // Текущий индекс слайда
const isLast = computed(() => idx.value === slides.length - 1)

function next() {
  if (isLast.value) router.push('/login') // На последнем слайде идем на вход
  else idx.value++                        // Иначе листаем дальше
}

function skip() {
  router.push('/login')                   // "Пропустить" тоже ведет на вход
}
</script>

<style scoped>
/* --- БАЗА (для телефона): fullscreen --- */
.onb-wrapper {
  min-height: 100vh;
  box-sizing: border-box;
  background: var(--bg); /* Белый фон на мобилке */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
  font-family: var(--font);
}

.onb-card {
  width: 100%;
  max-width: 480px; /* Чуть шире формы, так как тут текст заголовков длиннее */
  display: flex;
  flex-direction: column;
  gap: var(--space-6); /* Воздух между артом, текстом и футером */
}

.skip {
  /* Позиционируем абсолютно относительно wrapper'a */
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);

  border: 0; background: transparent; cursor: pointer;
  color: var(--text-muted);
  font-size: 16px;
  font-weight: 500;
  padding: var(--space-4);
  z-index: 10; /* Чтобы была поверх контента */
}

.stage {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; gap: var(--space-5);
}

.art {
  display:grid; place-items:center; width:160px; height:160px;
  border-radius:50%; background:var(--surface);
}

.title { margin: 0 0 var(--space-2); font-size: 26px; line-height: 1.2; color: var(--text); }
.text  { margin: 0; color: var(--text-muted); max-width: 36ch; line-height: 1.5; }

.footer { display: flex; flex-direction: column; gap: var(--space-5); align-items: center; }
.dots { display: flex; gap: var(--space-2); }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #d8d3c8; transition: background .2s; }
.dot.on { background: var(--primary); }
.cta { width: 100%; max-width: 320px; }

/* --- ПК ВЕРСИЯ: Превращаем в "Окно" по центру серого фона --- */
@media (min-width: 768px) {
  .onb-wrapper {
    background: var(--bg-canvas); /* Серый фон рабочего стола */
    padding: 0;
  }

  .onb-card {
    width: 480px;           /* Фиксированная ширина окна */
    max-width: none;
    background: #fff;       /* Белая подложка самого окна */
    border-radius: 24px;    /* Красивые скругленные углы */
    box-shadow: 0 20px 50px rgba(0,0,0,0.1); /* Тень для объема */
    padding: var(--space-6); /* Внутренний воздух окна */
    gap: var(--space-7);     /* Больше воздуха между блоками в окне */

    /* Важно: убираем skip из потока или позиционируем абсолютно,
       чтобы он не толкал контент вниз на ПК */
    position: relative;
  }

  .skip {
    position: absolute;
    top: var(--space-4);
    right: var(--space-4);
    margin-bottom: 0;
  }
}
</style>