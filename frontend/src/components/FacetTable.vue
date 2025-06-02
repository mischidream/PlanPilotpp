<template>
  <div class="facet-table">
    <div class="facet-header">
      <div v-for="header in headers" :key="header" class="facet-header-cell">
        {{ header }}
      </div>
    </div>
    <Divider />
    <template v-if="loading">
      <SkeletonFacetRow
        v-for="n in itemsPerPage || 4"
        :key="'skeleton-' + n"
        :viewMode="viewMode"
      />
    </template>
    <template v-else-if="viewMode === 'facets' || viewMode === 'query' || viewMode === 'landmarks'">
      <FacetRow
        v-for="facet in facets"
        :key="facet.id"
        :facet="facet"
        :readonly="viewMode === 'landmarks'"
        :viewMode="viewMode"
        :onSelectFacet="handleSelectFacet"
      />
    </template>
    <template v-else>
      <div v-for="(solution, index) in solutions" :key="solution.label" class="solution-block">
        <div class="solution-toggle">
          <div class="solution-toggle-left" @click="toggleSolution(index)">
            <span class="material-icons">
              {{ isSolutionOpen(index) ? 'expand_less' : 'expand_more' }}
            </span>
            <span class="solution-label">
              {{ solution.label.charAt(0).toUpperCase() + solution.label.slice(1) }}
            </span>
          </div>
          <button class="visualize-button" @click.stop="goToVisualization(solution)">
            Visualize
          </button>
        </div>
        <div v-if="isSolutionOpen(index)" class="solution-facets">
          <FacetRow
            v-for="facet in solution.facets"
            :key="facet.id"
            :facet="facet"
            :readonly="true"
            :viewMode="viewMode"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script lang="ts" setup>
import FacetRow from './FacetRow.vue';
import SkeletonFacetRow from './SkeletonFacetRow.vue';
import type { Facet } from '@/models/Facet';
import { SelectionState } from '@/models/SelectionState';
import Divider from './Divider.vue';
import { ref } from 'vue';
import type { Solution } from '@/models/Solution';
import { useRouter } from 'vue-router';
import { usePlanStore } from '@/stores/planStore';

const props = defineProps<{
  headers: string[];
  facets?: Facet[];
  solutions?: Solution[];
  viewMode: 'facets' | 'solutions' | 'query' | 'landmarks';
  loading?: boolean;
  itemsPerPage?: number;
}>();

const planStore = usePlanStore();
const router = useRouter();

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

function goToVisualization(solution: Solution) {
  planStore.setSelectedSolution(solution);
  router.push({ name: 'visualization' });
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
  display: flex;
  align-items: center;
}

.solution-block {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}

.solution-toggle {
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.solution-toggle-left {
  display: flex;
  align-items: center;
  flex-grow: 1;
  cursor: pointer;
  gap: 0.5rem;
}

.solution-facets {
  margin-left: 1rem;
}

.visualize-button {
  padding: 0.25rem 0.5rem;
  background-color: var(--light-blue);
  color: var(--white);
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
}

.visualize-button:hover {
  background-color: var(--deep-blue);
}
</style>
