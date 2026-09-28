<template>
  <div class="register-wrapper">
    <div class="register-container">
      <header class="brand-section">
        <svg viewBox="0 0 120 120" width="56" height="56" aria-hidden="true">
          <path d="M60 8 C90 8 112 30 112 60 C112 95 88 112 60 112 C30 112 8 92 8 60 C8 30 30 8 60 8 Z" fill="var(--ink)"/>
          <circle cx="46" cy="58" r="6" fill="#fff"/><circle cx="74" cy="58" r="6" fill="#fff"/>
        </svg>
        <h1>Создать аккаунт</h1>
        <p class="sub">Присоединяйтесь к платформе Blobs</p>
      </header>

      <form class="form-section" @submit.prevent="submit">
        <div class="role-selector">
          <button
            type="button"
            class="role-btn"
            :class="{ active: selectedRole === 'student' }"
            @click="selectedRole = 'student'"
          >
            🎓 Я Ученик
          </button>
          <button
            type="button"
            class="role-btn"
            :class="{ active: selectedRole === 'teacher' }"
            @click="selectedRole = 'teacher'"
          >
            👨‍🏫 Я Преподаватель
          </button>
        </div>

        <BaseInput
          v-model="name"
          label="Ваше имя"
          type="text"
          placeholder="Александр"
          :error="errors.name"
        />

        <BaseInput
          v-model="email"
          label="Email"
          type="email"
          placeholder="alex@mail.ru"
          :error="errors.email"
        />

        <BaseInput
          v-model="password"
          label="Пароль"
          type="password"
          placeholder="Минимум 6 символов"
          :error="errors.password"
        />

        <BaseButton variant="primary" size="lg" class="submit-btn" rounded :disabled="loading">
          {{ loading ? 'Регистрация…' : 'Зарегистрироваться' }}
        </BaseButton>

        <div class="divider"><span>или</span></div>

        <router-link to="/login" class="secondary-btn">Уже есть аккаунт? Войти</router-link>
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

const selectedRole = ref('student')
const name = ref('')
const email = ref('')
const password = ref('')
const errors = reactive({ name: '', email: '', password: '' })
const loading = ref(false)

function validate() {
  errors.name = ''
  errors.email = ''
  errors.password = ''
  let ok = true

  if (!name.value.trim()) {
    errors.name = 'Введите ваше имя'
    ok = false
  }
  if (!email.value.trim()) {
    errors.email = 'Введите email'
    ok = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    errors.email = 'Некорректный email'
    ok = false
  }
  if (!password.value) {
    errors.password = 'Введите пароль'
    ok = false
  } else if (password.value.length < 6) {
    errors.password = 'Минимум 6 символов'
    ok = false
  }
  return ok
}

async function submit() {
  if (!validate()) return
  loading.value = true

  try {
    await new Promise(r => setTimeout(r, 600))
    auth.login(
      selectedRole.value,
      'mock-reg-token-' + Date.now(),
      'user-' + Date.now(),
      { first_name: name.value.trim() }
    )
    router.push('/')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-wrapper {
  min-height: 100vh;
  box-sizing: border-box;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
  font-family: var(--font);
}

.register-container {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

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
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.role-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-2);
  background: var(--surface);
  padding: 4px;
  border-radius: var(--radius-pill);
}

.role-btn {
  padding: var(--space-2) var(--space-3);
  border: none;
  background: transparent;
  border-radius: var(--radius-pill);
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  color: var(--text-muted);
  transition: all 0.2s;
}
.role-btn.active {
  background: #fff;
  color: var(--ink);
  box-shadow: var(--shadow-sm);
}

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

@media (min-width: 768px) {
  .register-wrapper {
    background: var(--bg-canvas);
    padding: 0;
  }
  .register-container {
    background: #fff;
    border-radius: 24px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.1);
    padding: var(--space-7);
  }
}
</style>
