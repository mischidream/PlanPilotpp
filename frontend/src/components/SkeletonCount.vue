<template>
  <div class="skeleton-count"></div>
</template>

<script setup lang="ts">
// No script needed unless you want props (e.g. for size or animated shimmer)
</script>

<style scoped>
.skeleton-count {
  width: 6.25rem;
  height: 1.5rem;
  background-color: var(--white-mute);
  border-radius: var(--border-radius);
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
