/**
 * Сервис геймификации, званий и ачивок (согласован с backend app/services/gamification.py)
 */

export const OGE_LEVELS = {
  GRADE_3: {
    grade: '3',
    title: 'Порог сдачи (Оценка 3)',
    minXp: 0,
    maxXp: 200,
    color: '#f59e0b',
  },
  GRADE_4: {
    grade: '4',
    title: 'Уверенная 4-ка (Оценка 4)',
    minXp: 201,
    maxXp: 600,
    color: '#3b82f6',
  },
  GRADE_5: {
    grade: '5',
    title: 'Отличник ОГЭ (Оценка 5)',
    minXp: 601,
    maxXp: Infinity,
    color: '#10b981',
  },
}

export function calculateOgeLevel(totalXp) {
  if (totalXp >= 600) return OGE_LEVELS.GRADE_5
  if (totalXp >= 201) return OGE_LEVELS.GRADE_4
  return OGE_LEVELS.GRADE_3
}

export function getUserTitle(role, xp) {
  if (role === 'teacher' || role === 'tutor') {
    if (xp >= 1000) {
      return {
        badge: '🏆',
        title: 'Заслуженный преподаватель',
        fullTitle: '🏆 Заслуженный преподаватель',
        nextTitle: null,
        neededXp: 1000,
        xpToNext: 0,
        progress: 100,
      }
    } else if (xp >= 500) {
      return {
        badge: '🥇',
        title: 'Мастер физики',
        fullTitle: '🥇 Мастер физики',
        nextTitle: 'Заслуженный преподаватель',
        neededXp: 1000,
        xpToNext: 1000 - xp,
        progress: Math.round(((xp - 500) / 500) * 100),
      }
    } else if (xp >= 150) {
      return {
        badge: '🥈',
        title: 'Опытный наставник',
        fullTitle: '🥈 Опытный наставник',
        nextTitle: 'Мастер физики',
        neededXp: 500,
        xpToNext: 500 - xp,
        progress: Math.round(((xp - 150) / 350) * 100),
      }
    } else {
      return {
        badge: '🥉',
        title: 'Наставник-стажёр',
        fullTitle: '🥉 Наставник-стажёр',
        nextTitle: 'Опытный наставник',
        neededXp: 150,
        xpToNext: 150 - xp,
        progress: Math.round((xp / 150) * 100),
      }
    }
  } else {
    // Ученик
    if (xp >= 500) {
      return {
        badge: '🥇',
        title: 'Мастер физики',
        fullTitle: '🥇 Мастер физики',
        nextTitle: null,
        neededXp: 500,
        xpToNext: 0,
        progress: 100,
      }
    } else if (xp >= 150) {
      return {
        badge: '🥈',
        title: 'Знаток законов физики',
        fullTitle: '🥈 Знаток законов физики',
        nextTitle: 'Мастер физики',
        neededXp: 500,
        xpToNext: 500 - xp,
        progress: Math.round(((xp - 150) / 350) * 100),
      }
    } else {
      return {
        badge: '🥉',
        title: 'Юный наблюдатель',
        fullTitle: '🥉 Юный наблюдатель',
        nextTitle: 'Знаток законов физики',
        neededXp: 150,
        xpToNext: 150 - xp,
        progress: Math.round((xp / 150) * 100),
      }
    }
  }
}

export function getAllAchievements(role, xp = 0, solvedCount = 0) {
  const common = [
    {
      id: 'first_step',
      icon: '🚀',
      title: 'Первый шаг',
      description: role === 'teacher' ? 'Взять первую задачу на разбор' : 'Создать свою первую заявку',
      unlocked: xp > 0 || solvedCount > 0,
      reward: '+50 XP',
    },
    {
      id: 'telemost_call',
      icon: '📹',
      title: 'На связи в Телемосте',
      description: 'Провести или посетить разбор с видеосвязью',
      unlocked: xp >= 100,
      reward: '+50 XP',
    },
    {
      id: 'mechanics_pro',
      icon: '⚙️',
      title: 'Мастер механики',
      description: 'Успешный разбор задачи по кинематике или статике',
      unlocked: xp >= 150,
      reward: '+75 XP',
    },
    {
      id: 'electric_spark',
      icon: '⚡',
      title: 'Искра знаний',
      description: 'Разобрать закон Ома или электрические цепи',
      unlocked: xp >= 300,
      reward: '+100 XP',
    },
    {
      id: 'streak_master',
      icon: '🔥',
      title: 'В огне активности',
      description: 'Активность в приложении 3 дня подряд',
      unlocked: xp >= 400,
      reward: '+150 XP',
    },
    {
      id: 'legend',
      icon: '🏆',
      title: 'Легенда платформы',
      description: role === 'teacher' ? 'Получить звание Заслуженного преподавателя' : 'Набрать уровень Отличника ОГЭ (600+ XP)',
      unlocked: xp >= (role === 'teacher' ? 1000 : 600),
      reward: '+300 XP',
    },
  ]

  return common
}
