<template>
  <div class="skeleton-count"></div>
</template>

<script setup lang="ts">
// No script needed unless you want props (e.g. for size or animated shimmer)
</script>

<style scoped>
.skeleton-count {
  width: 100px;
  height: 1.5rem;
  background-color: #e0e0e0;
  border-radius: 4px;
  animation: pulse 1.5s infinite ease-in-out;
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
