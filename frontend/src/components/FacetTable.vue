<template>
    <div class="facet-table">
      <div class="facet-header">
        <div v-for="header in headers" :key="header" class="facet-header-cell">
          {{ header }}
        </div>
      </div>
      <Divider/>
      <FacetRow
        v-for="facet in facets"
        :key="facet.id"
        :facet="facet"
        :onSelectFacet="handleSelectFacet"
      />
    </div>
</template>

<script lang="ts" setup>
import FacetRow from './FacetRow.vue';
import type { Facet } from '@/models/Facet';
import { SelectionState } from '@/models/SelectionState';
import Divider from './Divider.vue';

const props = defineProps<{
    facets: Facet[];
    headers: string[];
}>();

const emit = defineEmits<{
    (event: 'selectFacet', facet: Facet, newState: SelectionState): void;
}>();

function handleSelectFacet(facet: Facet, newState: SelectionState) {
    emit('selectFacet', facet, newState);
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
</style>
  