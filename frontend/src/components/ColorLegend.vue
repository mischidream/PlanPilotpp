<template>
<div class="legend">
  <div class="legend-item">
    <span class="legend-swatch purple"></span>
    <span>Preselection*</span>
  </div>
  <div class="legend-item">
    <span class="legend-swatch blue"></span>
    <span>Self selected</span>
  </div>
  <div class="legend-item">
    <span class="legend-swatch white"></span>
    <span>Empty (To select)</span>
  </div>
  <div class="legend-item">
    <span class="legend-swatch gray"></span>
    <span>Implied (disabled)</span>
  </div>
</div>
</template>

<script setup lang="ts">

</script>

<style scoped>
.legend {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  color: var(--text);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-swatch {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid var(--border);
  display: inline-block;
}

.purple {
  background-color: var(--soft-purple-transparent);
}

.blue {
  background-color: var(--light-blue-transparent);
}

.white {
  background-color: var(--white);
  border: 1px solid var(--divider-light-1);
}

.gray {
  background-color: var(--background-mute);
  color: var(--gray-mute);
  border: 1px solid var(--border);
}
</style>
