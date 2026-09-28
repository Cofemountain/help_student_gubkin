<template>
  <div class="homework-page">
    <header class="page-header">
      <button class="back-btn" @click="$router.back()">← Назад</button>
      <h1>📚 Домашние задания и индивидуальные работы</h1>
    </header>

    <div class="hw-card">
      <div class="hw-icon">📝</div>
      <h2>Реестр домашних заданий</h2>
      <p class="desc">
        В данном разделе регистрируются и проверяются домашние и проверочные работы, направленные преподавателем, с экспертной оценкой каждого этапа решения.
      </p>
      <router-link to="/create-request" class="cta-link">
        + Сформировать заявку на проверку работы
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.homework-page {
  max-width: 700px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.back-btn {
  background: transparent;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--text-muted);
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.hw-card {
  background: #fff;
  border: 1px solid #e6e1d6;
  border-radius: var(--radius-lg);
  padding: var(--space-7);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}

.hw-icon {
  font-size: 48px;
}

.hw-card h2 {
  margin: 0;
  font-size: 20px;
}

.desc {
  max-width: 45ch;
  color: var(--text-muted);
  line-height: 1.5;
  margin: 0;
}

.cta-link {
  display: inline-block;
  margin-top: var(--space-3);
  background: var(--primary);
  color: var(--ink);
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-pill);
  font-weight: 700;
  text-decoration: none;
  transition: transform 0.2s;
}
.cta-link:hover {
  transform: scale(1.04);
}
</style>
