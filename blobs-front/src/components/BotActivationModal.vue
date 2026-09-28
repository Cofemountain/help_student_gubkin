<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-card">
        <header class="modal-header">
          <h3>Подключение уведомлений платформы</h3>
          <button class="close-btn" @click="$emit('close')">×</button>
        </header>

        <div class="modal-body">
          <p>Для своевременного получения уведомлений о статусе проверки заданий, новых заявках и назначенных видеоконсультациях откройте диалог с ботом и нажмите <strong>«Начать»</strong>.</p>

          <!-- Реальная ссылка на бота в МАКС -->
          <a href="https://max.ru/t334_hakaton_max_bot" target="_blank" class="action-link">
            🤖 Подключить бота в МАКС (@t334_hakaton_max_bot) ↗
          </a>

          <p class="hint-text">После подтверждения вернитесь в личный кабинет.</p>
        </div>

        <footer class="modal-footer">
          <BaseButton variant="secondary" size="md" @click="handleDone">
            Продолжить
          </BaseButton>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import BaseButton from './BaseButton.vue'
import { useAuthStore } from '../stores/auth'

const emit = defineEmits(['close'])
const auth = useAuthStore()

function handleDone() {
  auth.setBotActive() // Помечаем как активированного
  emit('close')       // Закрываем модалку
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0; /* top/right/bottom/left = 0 */
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-4);
}

.modal-card {
  background: #fff;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.2);
  overflow: hidden;
}

.modal-header {
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 { margin: 0; font-size: 18px; color: var(--text); }
.close-btn {
  border: none; background: transparent; cursor: pointer;
  font-size: 24px; line-height: 1; color: var(--text-muted);
}

.modal-body {
  padding: var(--space-5);
  text-align: center;
}
.modal-body p { margin: 0 0 var(--space-4); color: var(--text-muted); line-height: 1.5; }
.action-link {
  display: inline-block;
  padding: var(--space-3) var(--space-5);
  background: var(--surface);
  color: var(--ink);
  text-decoration: none;
  border-radius: var(--radius-pill);
  font-weight: 600;
  transition: background 0.2s;
}
.action-link:hover { background: #e8e3da; }
.hint-text { font-size: 13px !important; margin-top: var(--space-3) !important; }

.modal-footer {
  padding: var(--space-4) var(--space-5) var(--space-5);
  border-top: 1px solid #eee;
}
.modal-footer .btn { width: 100%; }
</style>