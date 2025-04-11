<template>
  <div class="app-container">
    <div class="top-bar">
      <Header class="header"></Header>
      <nav class="nav">
        <RouterLink to="/home" class="nav-link">Home</RouterLink>
        <div class="divider"></div>
        <RouterLink to="/visualization" class="nav-link">Visualization</RouterLink>
      </nav>
    </div>
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Header from './components/Header.vue';
</script>

<style scoped>

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--background);
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: var(--background-soft); /* Soft background */
  border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.header {
  flex: 1;
  color: var(--heading);
}

.nav {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-link {
  color: var(--text); /* Text color */
  font-weight: 500;
  text-decoration: none;
  transition: color 0.3s ease, font-weight 0.3s ease;
}

.nav-link:hover {
  color: var(--deep-blue); /* Hover color from your palette */
  font-weight: bold; /* Make text bold on hover */
}

.divider {
  height: 1.5rem;
  width: 1px;
  background-color: var(--border); /* Divider color */
}

.main-content {
  padding: 1rem;
  flex: 1;
  background-color: var(--background); /* Ensure main content background */
  color: var(--text);
}
</style>