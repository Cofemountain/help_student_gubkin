/**
 * MAX Mini App Bridge
 * Адаптер для интеграции с российским мессенджером МАКС (MAX Mini App).
 * Извлекает реальные данные пользователя: ID, имя, фамилию, @username и аватар/фото профиля.
 */

function parseUserDataJson(raw) {
  if (!raw) return null
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(decodeURIComponent(raw)) : raw
    if (parsed && typeof parsed === 'object') {
      const id = parsed.id || parsed.user_id
      const firstName = parsed.first_name || parsed.firstName || ''
      const lastName = parsed.last_name || parsed.lastName || ''
      const username = (parsed.username || parsed.nick || parsed.nickname || '').replace(/^@/, '')
      const photoUrl = parsed.photo_url || parsed.avatar_url || parsed.avatar || parsed.full_avatar_url || null
      return {
        id: id ? String(id) : null,
        firstName,
        lastName,
        username,
        photoUrl,
      }
    }
  } catch (e) {
    try {
      const parsed = JSON.parse(raw)
      return {
        id: parsed.id ? String(parsed.id) : null,
        firstName: parsed.first_name || '',
        lastName: parsed.last_name || '',
        username: (parsed.username || '').replace(/^@/, ''),
        photoUrl: parsed.photo_url || parsed.avatar_url || null,
      }
    } catch {}
  }
  return null
}

function extractFromQueryString(qs) {
  if (!qs) return null
  try {
    const clean = qs.replace(/^[#?]/, '')
    const params = new URLSearchParams(clean)

    // Проверяем вложенный WebAppData / tgWebAppData
    const nestedData = params.get('WebAppData') || params.get('tgWebAppData') || params.get('web_app_data')
    if (nestedData) {
      const nestedParams = new URLSearchParams(decodeURIComponent(nestedData))
      const userJson = nestedParams.get('user')
      if (userJson) {
        const u = parseUserDataJson(userJson)
        if (u) return u
      }
    }

    // Проверяем прямой параметр ?user=...
    const directUser = params.get('user')
    if (directUser) {
      const u = parseUserDataJson(directUser)
      if (u) return u
    }

    // Проверяем отдельные query-параметры
    const userId = params.get('user_id') || params.get('id')
    const firstName = params.get('first_name') || params.get('name') || ''
    const lastName = params.get('last_name') || ''
    const username = (params.get('username') || params.get('nick') || '').replace(/^@/, '')
    const photoUrl = params.get('photo_url') || params.get('avatar_url') || params.get('avatar') || null

    if (userId || firstName || username || photoUrl) {
      return {
        id: userId ? String(userId) : null,
        firstName,
        lastName,
        username,
        photoUrl,
      }
    }
  } catch (e) {
    console.warn('Ошибка при разборе query/hash строки:', e)
  }
  return null
}

export function initMaxApp() {
  const urlSearch = window.location.search || ''
  const urlHash = window.location.hash || ''

  // 1. Попытка получить глобальный объект WebApp МАКС / Telegram
  const maxWebApp = window.WebApp || window.Telegram?.WebApp || window.Max?.WebApp || null

  if (maxWebApp) {
    try {
      maxWebApp.ready?.()
      maxWebApp.expand?.()
    } catch (e) {
      console.warn('Не удалось вызвать ready/expand у WebApp:', e)
    }
  }

  // 2. Сбор данных из всех возможных источников
  let parsedUser = null

  // А) window.WebApp.initDataUnsafe.user (официальный SDK МАКС)
  if (maxWebApp?.initDataUnsafe?.user) {
    parsedUser = parseUserDataJson(maxWebApp.initDataUnsafe.user)
  }

  // Б) window.WebApp.initData (сырая строка параметров)
  if (!parsedUser && maxWebApp?.initData) {
    parsedUser = extractFromQueryString(maxWebApp.initData)
  }

  // В) location.hash (#WebAppData=... или #tgWebAppData=...)
  if (!parsedUser && urlHash) {
    parsedUser = extractFromQueryString(urlHash)
  }

  // Г) sessionStorage (кэш самого SDK МАКС)
  if (!parsedUser) {
    try {
      const sessionData = sessionStorage.getItem('WebAppData') || sessionStorage.getItem('tgWebAppData')
      if (sessionData) {
        parsedUser = extractFromQueryString(sessionData)
      }
    } catch {}
  }

  // Д) URL search params (?user_id=...&first_name=...)
  if (!parsedUser && urlSearch) {
    parsedUser = extractFromQueryString(urlSearch)
  }

  // Е) Кэш предыдущего успешного входа в localStorage
  if (!parsedUser) {
    try {
      const saved = localStorage.getItem('max_cached_profile')
      if (saved) {
        const u = JSON.parse(saved)
        if (u && (u.id || u.firstName || u.username)) {
          parsedUser = u
        }
      }
    } catch {}
  }

  // Извлекаем роль из стартовых параметров
  const urlParams = new URLSearchParams(urlSearch)
  const roleFromUrl =
    maxWebApp?.initDataUnsafe?.start_param ||
    urlParams.get('startapp') ||
    urlParams.get('role') ||
    null

  // Формируем финальный профиль пользователя
  const userId = parsedUser?.id || localStorage.getItem('max_user_id') || '104313660'
  const firstName = parsedUser?.firstName || localStorage.getItem('max_first_name') || ''
  const lastName = parsedUser?.lastName || localStorage.getItem('max_last_name') || ''
  let username = parsedUser?.username || localStorage.getItem('max_username') || ''
  if (['alex_student', 'alex_oge9', 'physics_tutor'].includes(username)) {
    username = ''
    try { localStorage.removeItem('max_username') } catch {}
  }
  const photoUrl = parsedUser?.photoUrl || localStorage.getItem('max_photo_url') || null

  const fullName = [firstName, lastName].filter(Boolean).join(' ') || firstName || 'Пользователь МАКС'

  const userProfile = {
    id: userId,
    firstName: firstName || 'Пользователь',
    lastName: lastName || '',
    fullName,
    username: username || '',
    photoUrl: photoUrl || null,
    avatarUrl: photoUrl || null,
  }

  // Сохраняем в localStorage для стабильности работы между экранами
  try {
    localStorage.setItem('max_user_id', String(userId))
    if (firstName) localStorage.setItem('max_first_name', firstName)
    if (lastName) localStorage.setItem('max_last_name', lastName)
    if (username) localStorage.setItem('max_username', username)
    if (photoUrl) localStorage.setItem('max_photo_url', photoUrl)
    localStorage.setItem('max_cached_profile', JSON.stringify(userProfile))
  } catch {}

  const isMaxEnv = Boolean(
    maxWebApp ||
    urlHash.includes('WebAppData') ||
    urlParams.get('user_id') ||
    sessionStorage.getItem('WebAppData')
  )

  return {
    isMaxEnvironment: isMaxEnv,
    user: userProfile,
    roleFromUrl,
    maxWebApp,
  }
}

export function closeMaxApp() {
  const maxWebApp = window.WebApp || window.Telegram?.WebApp || window.Max?.WebApp
  if (maxWebApp?.close) {
    maxWebApp.close()
  } else {
    window.close()
  }
}
