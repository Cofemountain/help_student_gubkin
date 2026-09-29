/**
 * Centralized API client for Blobs frontend.
 * Works seamlessly in local dev, in production on VPS, and inside MAX Mini App.
 */

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (window.location.port === '5173' ? 'http://localhost:8000/api' : '/api')

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorDetail = 'Ошибка сети'
    try {
      const errJson = await response.json()
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson)
    } catch {
      errorDetail = await response.text()
    }
    throw new Error(errorDetail || `HTTP error ${response.status}`)
  }

  return response.json()
}

export const api = {
  // --- Темы и кодификатор по физике (7-9 классы) ---
  getTopics: (block = null, grade = null) => {
    const params = new URLSearchParams()
    if (block) params.append('block', block)
    if (grade) params.append('grade', grade)
    const q = params.toString() ? `?${params.toString()}` : ''
    return request(`/topics${q}`)
  },

  // --- Синхронизация пользователя и роли ---
  syncUser: (userData) => {
    return request('/users/sync', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  },

  updateRole: (telegramId, activeRole) => {
    return request(`/users/${telegramId}/role`, {
      method: 'PATCH',
      body: JSON.stringify({ active_role: activeRole }),
    })
  },

  // --- Заявки и доска задач ---
  createTask: (taskData, studentTgId) => {
    return request(`/tasks?student_tg_id=${encodeURIComponent(studentTgId)}`, {
      method: 'POST',
      body: JSON.stringify(taskData),
    })
  },

  getBoardTasks: (status = 'OPEN', block = null, part = null, grade = null) => {
    const params = new URLSearchParams()
    if (status) params.append('status_filter', status)
    if (block && block !== 'ALL') params.append('block', block)
    if (part) params.append('part', part)
    if (grade && grade !== 'ALL') params.append('grade', grade)
    const q = params.toString() ? `?${params.toString()}` : ''
    return request(`/tasks${q}`)
  },

  getMyTasks: (telegramId, asRole = 'student') => {
    return request(`/tasks/my?telegram_id=${encodeURIComponent(telegramId)}&as_role=${encodeURIComponent(asRole)}`)
  },

  getTaskDetail: (taskId) => {
    return request(`/tasks/${taskId}`)
  },

  acceptTask: (taskId, tutorTgId) => {
    return request(`/tasks/${taskId}/accept?tutor_tg_id=${encodeURIComponent(tutorTgId)}`, {
      method: 'POST',
    })
  },

  submitReview: (taskId, reviewData, tutorTgId) => {
    return request(`/tasks/${taskId}/review?tutor_tg_id=${encodeURIComponent(tutorTgId)}`, {
      method: 'POST',
      body: JSON.stringify(reviewData),
    })
  },

  generateTelemost: (taskId, tutorTgId) => {
    return request(`/tasks/${taskId}/telemost?tutor_tg_id=${encodeURIComponent(tutorTgId)}`, {
      method: 'POST',
    })
  },

  updateTelemostUrl: (taskId, telemostUrl) => {
    return request(`/tasks/${taskId}/telemost-url`, {
      method: 'PATCH',
      body: JSON.stringify({ telemost_url: telemostUrl }),
    })
  },

  completeTask: (taskId, studentTgId = null) => {
    const query = studentTgId ? `?student_tg_id=${encodeURIComponent(studentTgId)}` : ''
    return request(`/tasks/${taskId}/complete${query}`, {
      method: 'POST',
    })
  },

  markTaskUnderstood: (taskId, studentTgId) => {
    return request(`/tasks/${taskId}/understood?student_tg_id=${encodeURIComponent(studentTgId)}`, {
      method: 'POST',
    })
  },

  checkTaskHomework: (taskId, userAnswer, studentTgId = null) => {
    return request(`/tasks/${taskId}/check-homework`, {
      method: 'POST',
      body: JSON.stringify({ user_answer: userAnswer, student_tg_id: studentTgId }),
    })
  },

  clarifyTask: (taskId, clarification, studentTgId) => {
    return request(`/tasks/${taskId}/clarify?student_tg_id=${encodeURIComponent(studentTgId)}`, {
      method: 'POST',
      body: JSON.stringify({ clarification }),
    })
  },

  // --- Домашние задания ---
  issueHomework: (taskId, homeworkData, tutorTgId) => {
    return request(`/tasks/${taskId}/homework?tutor_tg_id=${encodeURIComponent(tutorTgId)}`, {
      method: 'POST',
      body: JSON.stringify(homeworkData),
    })
  },

  submitHomework: (hwId, solutionPhotoUrl, studentTgId) => {
    return request(`/homework/${hwId}/submit?student_tg_id=${encodeURIComponent(studentTgId)}`, {
      method: 'POST',
      body: JSON.stringify({ solution_photo_url: solutionPhotoUrl }),
    })
  },

  reviewHomework: (hwId, isAccepted, feedback, tutorTgId) => {
    return request(`/homework/${hwId}/review?tutor_tg_id=${encodeURIComponent(tutorTgId)}`, {
      method: 'POST',
      body: JSON.stringify({ is_accepted: isAccepted, feedback }),
    })
  },

  // --- Банк задач ОГЭ (Открытый, Закрытый и База разобранных заявок) ---
  getSolvedBankTasks: (grade = null, block = null, search = '', limit = 50, offset = 0) => {
    const params = new URLSearchParams({ limit, offset })
    if (grade) params.append('grade', grade)
    if (block) params.append('block', block)
    if (search && search.trim()) params.append('search', search.trim())
    return request(`/bank/solved-tasks?${params.toString()}`)
  },

  getOpenBankTasks: (grade = null, block = null, limit = 50, offset = 0) => {
    const params = new URLSearchParams({ limit, offset })
    if (grade) params.append('grade', grade)
    if (block) params.append('block', block)
    return request(`/bank/tasks?${params.toString()}`)
  },

  getClosedBankTasks: (grade = null, block = null, limit = 50, offset = 0) => {
    const params = new URLSearchParams({ limit, offset })
    if (grade) params.append('grade', grade)
    if (block) params.append('block', block)
    return request(`/bank/tasks/tutor?${params.toString()}`)
  },

  getClosedBankTasksForStudents: (grade = null, block = null, limit = 50, offset = 0) => {
    const params = new URLSearchParams({ limit, offset })
    if (grade) params.append('grade', grade)
    if (block) params.append('block', block)
    return request(`/bank/tasks/closed?${params.toString()}`)
  },

  getBankTaskById: (taskId) => {
    return request(`/bank/tasks/${taskId}`)
  },

  checkAnswer: (taskId, userAnswer, studentTgId) => {
    return request(`/bank/tasks/${taskId}/check-answer`, {
      method: 'POST',
      body: JSON.stringify({
        user_answer: userAnswer,
        student_tg_id: studentTgId,
      }),
    })
  },

  assignBankHomework: (bankTaskId, taskId, tutorTgId) => {
    return request('/bank/assign-homework', {
      method: 'POST',
      body: JSON.stringify({
        bank_task_id: bankTaskId,
        task_id: taskId,
        tutor_tg_id: tutorTgId,
      }),
    })
  },

  getBankStats: () => {
    return request('/bank/stats')
  },
}
