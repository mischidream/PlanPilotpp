<template>
  <div class="facet-row">
    <div class="skeleton-bar" :class="viewMode"></div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  viewMode: 'facets' | 'solutions' | 'query' | 'landmarks';
}>();
</script>

<style scoped>
.facet-row {
  display: flex;
  padding: 0.5rem 0;
  border-bottom: 1px solid #ccc;
}

.skeleton-bar {
  height: 2.5rem;
  width: 100%;
  background-color: #e0e0e0;
  border-radius: 4px;
  animation: pulse 1.5s infinite ease-in-out;
}

.skeleton-bar.facets, .skeleton-bar.query, .skeleton-bar.landmarks {
  height: 2.5rem;
}

.skeleton-bar.solutions {
  height: 1.8rem;
}

@keyframes pulse {
  0% {
    opacity: 0.4;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.4;
  }
}
</style>
