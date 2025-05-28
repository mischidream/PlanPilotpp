<template>
  <div class="layout">
    <BlockVisualizer :solution="solution"></BlockVisualizer>
  </div>
</template>

<script setup lang="ts">
import BlockVisualizer from '@/components/BlockVisualizer.vue';
import { usePlanStore } from '@/stores/planStore';

const planStore = usePlanStore();
const solution = planStore.selectedSolution;

</script>

<style scoped>
.layout {
  padding: 1rem;
}
</style>