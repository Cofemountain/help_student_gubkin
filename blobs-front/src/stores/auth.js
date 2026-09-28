import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { initMaxApp } from '../services/maxBridge'
import { getUserTitle, calculateOgeLevel, getAllAchievements } from '../services/gamification'
import { api } from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  // 1. Инициализация адаптера МАКС с парсингом реальных данных пользователя
  const maxEnv = initMaxApp()

  const userId = ref(localStorage.getItem('blobs_userId') || maxEnv.user.id)
  const role = ref(localStorage.getItem('blobs_role') || maxEnv.roleFromUrl || null)
  const token = ref(localStorage.getItem('blobs_token') || `max-session-${userId.value}`)
  const botActivated = ref(localStorage.getItem('blobs_botActivated') === 'true' || true)
  const xp = ref(Number(localStorage.getItem('blobs_xp')) || 250)

  // 2. Инициализация профиля: приоритет отдается реальным данным из МАКС
  const initialUser = (() => {
    try {
      const saved = localStorage.getItem('blobs_userData')
      if (saved) {
        const parsed = JSON.parse(saved)
        // Если в МАКС переданы свежие имя/фото, объединяем их
        return {
          ...parsed,
          ...(maxEnv.user.photoUrl ? { photoUrl: maxEnv.user.photoUrl, avatar_url: maxEnv.user.photoUrl } : {}),
          ...(maxEnv.user.firstName && maxEnv.user.firstName !== 'Пользователь' ? { firstName: maxEnv.user.firstName, first_name: maxEnv.user.firstName } : {}),
          ...(maxEnv.user.lastName ? { lastName: maxEnv.user.lastName, last_name: maxEnv.user.lastName } : {}),
          ...(maxEnv.user.username ? { username: maxEnv.user.username } : {}),
        }
      }
    } catch {}

    return {
      id: maxEnv.user.id,
      firstName: maxEnv.user.firstName,
      first_name: maxEnv.user.firstName,
      lastName: maxEnv.user.lastName,
      last_name: maxEnv.user.lastName,
      username: maxEnv.user.username,
      photoUrl: maxEnv.user.photoUrl,
      avatar_url: maxEnv.user.photoUrl,
    }
  })()

  const userData = ref(initialUser)

  // 3. Вычисляемые поля для отображения в интерфейсе
  const userName = computed(() => {
    return userData.value?.firstName || userData.value?.first_name || 'Обучающийся'
  })

  const userLastName = computed(() => {
    return userData.value?.lastName || userData.value?.last_name || ''
  })

  const userFullName = computed(() => {
    const fn = userData.value?.firstName || userData.value?.first_name || ''
    const ln = userData.value?.lastName || userData.value?.last_name || ''
    if (fn && ln) return `${fn} ${ln}`
    return fn || (role.value === 'teacher' ? 'Преподаватель физики' : 'Обучающийся')
  })

  const userUsername = computed(() => {
    const u = userData.value?.username || ''
    if (['alex_student', 'alex_oge9', 'physics_tutor'].includes(u)) return ''
    return u.replace(/^@/, '')
  })

  const userAvatar = computed(() => {
    return userData.value?.photoUrl || userData.value?.photo_url || userData.value?.avatar_url || null
  })

  // Стильный двухбуквенный инициал для аватара, если у пользователя нет фото
  const userInitials = computed(() => {
    const fn = userData.value?.firstName || userData.value?.first_name || ''
    const ln = userData.value?.lastName || userData.value?.last_name || ''
    if (fn && ln) return (fn.charAt(0) + ln.charAt(0)).toUpperCase()
    if (fn) return fn.slice(0, 2).toUpperCase()
    return role.value === 'teacher' ? 'ПР' : 'ОГЭ'
  })

  // 4. Геймификация
  const currentTitle = computed(() => getUserTitle(role.value || 'student', xp.value))
  const ogeLevel = computed(() => calculateOgeLevel(xp.value))
  const achievements = computed(() => getAllAchievements(role.value || 'student', xp.value))

  // 5. Синхронизация профиля с Backend API
  async function syncWithBackend() {
    try {
      const payload = {
        telegram_id: Number(userId.value),
        first_name: userName.value,
        last_name: userLastName.value || null,
        username: userData.value?.username || null,
        avatar_url: userAvatar.value || null,
      }
      const serverUser = await api.syncUser(payload)
      if (serverUser) {
        if (serverUser.xp !== undefined && serverUser.xp !== null) {
          xp.value = serverUser.xp
          localStorage.setItem('blobs_xp', String(serverUser.xp))
        }
        if (serverUser.avatar_url && !userData.value.photoUrl) {
          userData.value.photoUrl = serverUser.avatar_url
          userData.value.avatar_url = serverUser.avatar_url
          localStorage.setItem('blobs_userData', JSON.stringify(userData.value))
        }
      }
    } catch (e) {
      console.warn('Фоновая синхронизация с сервером:', e)
    }
  }

  // 6. Управление сессией и ролью (сохраняет реальные имя и фото пользователя)
  function login(newRole, newToken = null, newUserId = null, newUser = null) {
    role.value = newRole
    if (newUserId) userId.value = String(newUserId)
    if (newUser) {
      userData.value = { ...userData.value, ...newUser }
    }
    if (newToken) token.value = newToken

    localStorage.setItem('blobs_role', newRole || '')
    localStorage.setItem('blobs_token', token.value)
    localStorage.setItem('blobs_userId', String(userId.value))
    localStorage.setItem('blobs_userData', JSON.stringify(userData.value))
    localStorage.setItem('blobs_xp', String(xp.value))

    syncWithBackend()
  }

  function selectRole(newRole) {
    login(newRole)
  }

  async function switchRole(newRole) {
    role.value = newRole
    localStorage.setItem('blobs_role', newRole)
    try {
      await api.updateRole(Number(userId.value), newRole === 'teacher' ? 'tutor' : 'student')
    } catch (e) {
      console.warn('Не удалось обновить роль на сервере:', e)
    }
    syncWithBackend()
  }

  function addXp(amount, reason = '') {
    xp.value += amount
    localStorage.setItem('blobs_xp', String(xp.value))
    return {
      newXp: xp.value,
      title: getUserTitle(role.value, xp.value),
    }
  }

  function setBotActive() {
    botActivated.value = true
    localStorage.setItem('blobs_botActivated', 'true')
  }

  function logout() {
    role.value = null
    token.value = null
    localStorage.removeItem('blobs_role')
    localStorage.removeItem('blobs_token')
  }

  // Запуск фоновой синхронизации при входе
  syncWithBackend()

  return {
    userId,
    role,
    token,
    botActivated,
    userData,
    userName,
    userLastName,
    userFullName,
    userUsername,
    userAvatar,
    userInitials,
    xp,
    currentTitle,
    ogeLevel,
    achievements,
    syncWithBackend,
    login,
    selectRole,
    switchRole,
    addXp,
    setBotActive,
    logout,
  }
})