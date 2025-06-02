<template>
  <div class="layout">
    <BlockVisualizer :solution="solution"></BlockVisualizer>
  </div>
</template>

<script setup lang="ts">
import BlockVisualizer from '@/components/BlockVisualizer.vue';
import { usePlanStore } from '@/stores/planStore';
import testData from '../testdata/example_answer_sets.json';
import type { AnswerSet } from '@/models/AnswerSet';

const planStore = usePlanStore();
const solution = planStore.selectedSolution;

//const solution = testData[2] as AnswerSet;

</script>

<style scoped>
.layout {
  padding: 1rem;
}
</style>