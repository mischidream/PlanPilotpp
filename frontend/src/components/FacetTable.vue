<template>
    <div class="facet-table">
      <div class="facet-header">
        <div v-for="header in headers" :key="header" class="facet-header-cell">
          {{ header }}
        </div>
      </div>
      <Divider/>
      <template v-if="viewMode === 'facets' || viewMode === 'query'">
        <FacetRow
          v-for="facet in facets"
          :key="facet.id"
          :facet="facet"
          :readonly="false"
          :onSelectFacet="handleSelectFacet"
        />
      </template>
      <template v-else>
        <div
          v-for="(solution, index) in solutions"
          :key="solution.label"
          class="solution-block"
        >
          <div @click="toggleSolution(index)" class="solution-toggle">
            <span class="material-icons">
              {{ isSolutionOpen(index) ? 'expand_less' : 'expand_more' }}
            </span>
            <span class="solution-label">
              {{ solution.label.charAt(0).toUpperCase() + solution.label.slice(1) }}
            </span>
          </div>
          <div v-if="isSolutionOpen(index)" class="solution-facets">
            <FacetRow
              v-for="facet in solution.facets"
              :key="facet.id"
              :facet="facet"
              :readonly="true"
            />
          </div>
        </div>
      </template>
    </div>
</template>

<script lang="ts" setup>
import FacetRow from './FacetRow.vue';
import type { Facet } from '@/models/Facet';
import { SelectionState } from '@/models/SelectionState';
import Divider from './Divider.vue';
import { ref } from 'vue';
import type { AnswerSet } from '@/models/AnswerSet';

const props = defineProps<{
  headers: string[];
  facets?: Facet[];
  solutions?: AnswerSet[];
  viewMode: 'facets' | 'solutions' | 'query';
}>();

const emit = defineEmits<{
    (event: 'selectFacet', facet: Facet, newState: SelectionState): void;
}>();

const openSolutions = ref<number[]>([]);

function handleSelectFacet(facet: Facet, newState: SelectionState) {
    emit('selectFacet', facet, newState);
}

function toggleSolution(index: number) {
  const pos = openSolutions.value.indexOf(index);
  if (pos === -1) {
    openSolutions.value.push(index);
  } else {
    openSolutions.value.splice(pos, 1);
  }
}

function isSolutionOpen(index: number): boolean {
  return openSolutions.value.includes(index);
}
</script>

<style scoped>
.facet-table {
    width: 100%;
}
.facet-header {
    display: flex;
}
.facet-header-cell {
    flex: 1;
}

.solution-block {
  padding: 0.5rem 0;
  border-bottom: 1px solid #ccc;
}

.solution-toggle {
  cursor: pointer;
  display: flex;
  align-items: center;
}

.solution-facets {
  margin-left: 1rem;
}

</style>
  