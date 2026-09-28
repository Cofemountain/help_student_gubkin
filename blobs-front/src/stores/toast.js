import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])

  function show({ message, title = '', type = 'info', duration = 3500 }) {
    const id = Date.now() + Math.random()
    const toast = { id, message, title, type, duration }
    toasts.value.push(toast)

    if (duration > 0) {
      setTimeout(() => {
        remove(id)
      }, duration)
    }
    return id
  }

  function success(message, title = '') {
    return show({ message, title, type: 'success' })
  }

  function error(message, title = '') {
    return show({ message, title, type: 'error' })
  }

  function warning(message, title = '') {
    return show({ message, title, type: 'warning' })
  }

  function info(message, title = '') {
    return show({ message, title, type: 'info' })
  }

  function remove(id) {
    const idx = toasts.value.findIndex((t) => t.id === id)
    if (idx !== -1) {
      toasts.value.splice(idx, 1)
    }
  }

  return {
    toasts,
    show,
    success,
    error,
    warning,
    info,
    remove,
  }
})
