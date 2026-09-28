<template>
  <div class="login-wrapper">
    <!-- Единый контейнер для всего контента -->
    <div class="login-container">

      <!-- Блок бренда (лого + название) -->
      <header class="brand-section">
        <svg viewBox="0 0 120 120" width="64" height="64" aria-hidden="true">
          <path d="M60 8 C90 8 112 30 112 60 C112 95 88 112 60 112 C30 112 8 92 8 60 C8 30 30 8 60 8 Z" fill="var(--ink)"/>
          <circle cx="46" cy="58" r="6" fill="#fff"/><circle cx="74" cy="58" r="6" fill="#fff"/>
        </svg>
        <h1>Blobs</h1>
        <p class="sub">Образовательная платформа взаимопомощи</p>
      </header>

      <!-- Форма входа -->
      <form class="form-section" @submit.prevent="submit">
        <h2>И снова привет!</h2>
        <p class="hint">Мы счастливы увидеть вас снова. Введите ваш email и пароль.</p>

        <BaseInput v-model="email" label="Email" type="email" placeholder="you@mail.ru" :error="errors.email" />
        <BaseInput v-model="password" label="Пароль" type="password" placeholder="••••••••" :error="errors.password" />

        <button type="submit" class="forgot-link" @click.prevent="recover">Забыли пароль?</button>

        <BaseButton variant="primary" size="lg" class="submit-btn" rounded :disabled="loading">
          {{ loading ? 'Входим…' : 'Войти' }}
        </BaseButton>

        <div class="divider"><span>или</span></div>

        <div class="quick-login-grid">
          <button type="button" class="quick-btn" @click="quickLogin('student')">
            🎓 Войти как Ученик
          </button>
          <button type="button" class="quick-btn" @click="quickLogin('teacher')">
            👨‍🏫 Войти как Преподаватель
          </button>
        </div>

        <router-link to="/register" class="secondary-btn">Создать аккаунт</router-link>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import BaseInput from '../components/BaseInput.vue'
import BaseButton from '../components/BaseButton.vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const errors = reactive({ email: '', password: '' })
const loading = ref(false)

function validate() {
  errors.email = ''
  errors.password = ''
  let ok = true
  if (!email.value.trim()) { errors.email = 'Введите email'; ok = false }
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) { errors.email = 'Некорректный email'; ok = false }
  if (!password.value) { errors.password = 'Введите пароль'; ok = false }
  else if (password.value.length < 6) { errors.password = 'Минимум 6 символов'; ok = false }
  return ok
}

async function submit() {
  if (!validate()) return
  loading.value = true
  try {
    // === МОК вместо реального API ===
    await new Promise(r => setTimeout(r, 700))
    const mockRole = email.value.toLowerCase().startsWith('t') ? 'teacher' : 'student'
    auth.login(mockRole, 'mock-token-' + Date.now())
    // ===================================
    router.push('/')
  } finally {
    loading.value = false
  }
}

function quickLogin(role) {
  auth.login(role, 'quick-token-' + Date.now(), 'user-' + role, {
    first_name: role === 'teacher' ? 'Преподаватель' : 'Ученик'
  })
  router.push('/')
}

function recover() { alert('Восстановление пароля появится позже') }
</script>

<style scoped>
/* --- ОБЩИЕ СТИЛИ --- */
.login-wrapper {
  min-height: 100vh;
  box-sizing: border-box;
  background: var(--bg); /* Белый фон на мобилке */
  display: flex;
  align-items: center; /* Вертикальное центрирование */
  justify-content: center; /* Горизонтальное центрирование */
  padding: var(--space-5);
  font-family: var(--font);
}

.login-container {
  width: 100%;
  max-width: 400px; /* Ограничиваем ширину для читаемости */
  display: flex;
  flex-direction: column;
  gap: var(--space-6); /* Расстояние между лого и формой */
}

/* --- БЛОК БРЕНДА --- */
.brand-section {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}
.brand-section h1 {
  margin: 0;
  font-size: 24px;
  color: var(--text);
  font-weight: 700;
}
.sub {
  margin: 0;
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.4;
}

/* --- ФОРМА --- */
.form-section {
  width: 100%;
  /* На мобилке убираем рамку и тень, делаем плоский дизайн */
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4); /* Ритм между элементами формы */
}

.form-section h2 {
  margin: 0 0 var(--space-1);
  font-size: 20px;
  color: var(--text);
  text-align: left; /* Заголовок слева, как принято в формах */
}
.hint {
  margin: 0 0 var(--space-2);
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.4;
  text-align: left;
}

.forgot-link {
  align-self: flex-start; /* Прижимаем к левому краю */
  border: 0;
  background: transparent;
  color: var(--text-muted);
  font: inherit;
  cursor: pointer;
  padding: 0;
  font-size: 13px;
  margin-top: calc(var(--space-1) * -1); /* Подтягиваем ближе к полю пароля */
}
.forgot-link:hover { color: var(--text); }

.submit-btn {
  width: 100%;
  margin-top: var(--space-2);
}

.divider {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin: var(--space-2) 0;
  color: var(--text-muted);
  font-size: 13px;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e6e1d6;
}

.quick-login-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
}

.quick-btn {
  padding: var(--space-3) var(--space-2);
  border: 1px dashed var(--border);
  background: var(--surface);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: var(--ink);
  transition: all 0.2s;
  text-align: center;
}
.quick-btn:hover {
  border-color: var(--primary);
  background: #fff8ef;
}

.secondary-btn {
  display: block;
  text-align: center;
  padding: var(--space-3);
  border: 1px solid var(--ink);
  border-radius: var(--radius-pill);
  color: var(--ink);
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
}
.secondary-btn:hover {
  background: var(--surface);
}

/* --- ПК ВЕРСИЯ: Превращаем в "Окно" --- */
@media (min-width: 768px) {
  .login-wrapper {
    background: var(--bg-canvas); /* Серый фон рабочего стола */
    padding: 0;
  }

  .login-container {
    width: 420px;           /* Фиксированная ширина окна */
    max-width: none;
    background: #fff;       /* Белая подложка самого окна */
    border-radius: 24px;    /* Красивые скругленные углы */
    box-shadow: 0 20px 50px rgba(0,0,0,0.1); /* Тень для объема */
    padding: var(--space-7); /* Больше внутреннего воздуха */
    gap: var(--space-7);     /* Больше расстояния между блоками */
  }

  /* Внутри окна форма остается плоской, так как фон уже белый */
  .form-section {
    background: transparent;
    border: none;
    box-shadow: none;
  }

  /* Логотип можно чуть уменьшить для баланса */
  .brand-section svg { width: 56px; height: 56px; }
}
</style>