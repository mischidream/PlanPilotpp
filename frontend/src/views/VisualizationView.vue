<template>
  <div class="layout">
    <BlockVisualizer :solution="solution"></BlockVisualizer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import BlockVisualizer from '@/components/BlockVisualizer.vue';
import testData from '../testdata/example_answer_sets.json';
import type { Solution } from '@/models/Solution';
import { usePlanSpaceNavigationStore } from '@/stores/planSpaceNavigationStore';

const planStore = usePlanSpaceNavigationStore();
const solution = computed(() => planStore.selectedSolution);

//const solution = testData[2] as Solution;
</script>

<style scoped>
.layout {
  padding: 1rem;
}
</style>
