import { createApp } from 'vue'
import App from './App.vue'
import { router } from './router'
import './styles/tokens.css'
import { createPinia } from 'pinia'
import { useToastStore } from './stores/toast'

const app = createApp(App)
const pinia = createPinia()

app.use(router)
app.use(pinia)
app.mount('#app')

// Перехват браузерного alert для отображения стильных пуш-уведомлений платформы
const toast = useToastStore(pinia)
window.alert = (message) => {
  if (!message) return
  const str = String(message)
  if (str.includes('✅') || str.includes('🎉') || str.includes('успешно') || str.includes('Отлично')) {
    toast.success(str.replace(/^[✅🎉]\s*/, ''))
  } else if (str.includes('❌') || str.includes('Ошибка') || str.includes('ошибку')) {
    toast.error(str.replace(/^❌\s*/, ''))
  } else if (str.includes('⚠️') || str.includes('Внимание') || str.includes('Только ученики') || str.includes('не можете')) {
    toast.warning(str.replace(/^⚠️\s*/, ''))
  } else {
    toast.info(str.replace(/^[ℹ️📨]\s*/, ''))
  }
}

