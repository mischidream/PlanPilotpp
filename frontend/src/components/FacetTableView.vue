<template>
  <div>
    <FacetTable
      :key="viewMode"
      :headers="headers"
      :facets="pagedFacets"
      :solutions="pagedSolutions"
      :viewMode="viewMode"
      :loading="loading"
      :itemsPerPage="itemsPerPage"
      @selectFacet="handleFacetSelectionState"
    />

    <Paginator
      v-model:currentPage="localPage"
      :totalItems="totalItems"
      :itemsPerPage="itemsPerPage"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import FacetTable from '@/components/FacetTable.vue';
import Paginator from '@/components/Paginator.vue';

import type { Facet } from '@/models/Facet';
import type { Solution } from '@/models/Solution';
import type { SelectionState } from '@/models/SelectionState';

const props = defineProps<{
  viewMode: 'facets' | 'query' | 'solutions';
  headers: string[];
  facets: Facet[];
  solutions: Solution[];
  loading: boolean;
  itemsPerPage: number;
  currentPage: number;
}>();

const emit = defineEmits<{
  (e: 'update:currentPage', page: number): void;
  (e: 'selectFacet', facet: Facet, state: SelectionState): void;
}>();

const localPage = ref(props.currentPage);
watch(localPage, val => emit('update:currentPage', val));
watch(
  () => props.currentPage,
  val => (localPage.value = val)
);

// Determine what to show
const showFacets = computed(() => props.viewMode === 'facets' || props.viewMode === 'query');
const showSolutions = computed(() => props.viewMode === 'solutions');

const pagedFacets = computed(() =>
  showFacets.value
    ? props.facets.slice(
        (localPage.value - 1) * props.itemsPerPage,
        localPage.value * props.itemsPerPage
      )
    : undefined
);

const pagedSolutions = computed(() =>
  showSolutions.value
    ? props.solutions.slice(
        (localPage.value - 1) * props.itemsPerPage,
        localPage.value * props.itemsPerPage
      )
    : undefined
);

const totalItems = computed(() =>
  showFacets.value ? props.facets.length : props.solutions.length
);

function handleFacetSelectionState(facet: Facet, state: SelectionState) {
  emit('selectFacet', facet, state);
}
</script>
