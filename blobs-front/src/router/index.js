import { createRouter, createWebHistory } from 'vue-router'
import StyleGuide from '../views/StyleGuide.vue'
import RoleSelection from '../views/RoleSelection.vue'
import AchievementsView from '../views/AchievementsView.vue'
import BankView from '../views/BankView.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  // --- ЭКРАН ВЫБОРА РОЛИ И ОНБОРДИНГА ДЛЯ MAX MINI APP ---
  { path: '/login', component: RoleSelection },
  { path: '/onboarding', component: RoleSelection },
  { path: '/register', redirect: '/login' },

  // --- ОСНОВНЫЕ ЭКРАНЫ ---
  {
    path: '/',
    component: () => import('../views/HomePlaceholder.vue'),
    meta: { requiresAuth: true }
  },

  // Банк задач ОГЭ (Практика)
  {
    path: '/bank',
    component: BankView,
    meta: { requiresAuth: true }
  },

  // Ачивки и звания
  {
    path: '/achievements',
    component: AchievementsView,
    meta: { requiresAuth: true }
  },

  // Профиль пользователя МАКС
  {
    path: '/profile',
    component: () => import('../views/Profile.vue'),
    meta: { requiresAuth: true }
  },

  // Домашние задания
  {
    path: '/homework',
    component: () => import('../views/Homework.vue'),
    meta: { requiresAuth: true }
  },

  // Лента заявок (для преподавателя)
  {
    path: '/requests',
    name: 'TeacherFeed',
    component: () => import('../views/TeacherFeed.vue'),
    meta: { requiresAuth: true }
  },

  // Создание заявки (для ученика)
  {
    path: '/create-request',
    component: () => import('../views/CreateRequest.vue'),
    meta: { requiresAuth: true }
  },

  // Гайд по компонентам (служебный)
  { path: '/styleguide', component: StyleGuide },

  // Любой неизвестный маршрут -> перенаправляем на главную
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.role) {
    next('/login')
  } else {
    next()
  }
})