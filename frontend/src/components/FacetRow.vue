<template>
    <div class="facet-row">
      <!-- Choose Facet -->
      <div class="facet-cell choose-facet">
        <template v-if="!readonly">
          <button
            :class="{ active: facet.selectionState === SelectionState.Positive }"
            @click="toggleState(SelectionState.Positive)"
          >
            <span class="material-icons">add</span>
          </button>
          <button
            :class="{ active: facet.selectionState === SelectionState.Negative }"
            @click="toggleState(SelectionState.Negative)"
          >
            <span class="material-icons">remove</span>
          </button>
        </template>
      </div>
  
      <!-- Action -->
      <div class="facet-cell">{{ facet.action }}</div>
  
      <!-- Constants -->
      <div class="facet-cell">
        <template v-if="facet.constant2">
          {{ facet.constant1 }} | {{ facet.constant2 }}
        </template>
        <template v-else>
          {{ facet.constant1 }}
        </template>
      </div>
  
      <!-- Timestep -->
      <div class="facet-cell">{{ facet.timestep }}</div>
      
      <!-- Reduction -->
      <div class="facet-cell" v-if="facet.reduction?.facets && viewMode === 'query'"> {{ facet.reduction.facets.positive }} | {{ facet.reduction.facets.negative }}</div>
      <div class="facet-cell" v-else-if="facet.reduction?.answer_set && viewMode === 'query'"> {{ facet.reduction.answer_set.positive }} | {{ facet.reduction.answer_set.negative }}</div>
      
      <!-- Remaining -->
      <div class="facet-cell" v-if="facet.remaining?.facets && viewMode === 'query'"> {{ facet.remaining.facets.positive }} | {{ facet.remaining.facets.negative }}</div>
      <div class="facet-cell" v-else-if="facet.remaining?.answer_set && viewMode === 'query'"> {{ facet.remaining.answer_set.positive }} | {{ facet.remaining.answer_set.negative }}</div>
    </div>
</template>

<script lang="ts" setup>
import type { Facet } from '@/models/Facet';
import { SelectionState } from '@/models/SelectionState';

const props = defineProps<{
    facet: Facet;
    readonly?: boolean;
    viewMode?: 'facets' | 'solutions' | 'query';
    onSelectFacet?: (facet: Facet, newState: SelectionState) => void;
}>();

function toggleState(state: SelectionState) {
  if (!props.onSelectFacet) return;
  const current = props.facet.selectionState;
  const newState =
    current === state ? SelectionState.NotSelected : state;
  props.onSelectFacet(props.facet, newState);
}
</script>

<style scoped>
.facet-row {
    display: flex;
    padding: 0.5rem 0;
    border-bottom: 1px solid #ccc;
}
.facet-row:first-child {
  padding-top: 0;
}
.facet-cell {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}
.choose-facet button {
    margin-right: 5px;
    cursor: pointer;
    background: transparent;
    border: 2px solid black;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: var(--border-radius);
    transition: all 0.2s ease;
}
.choose-facet button.active {
  background-color: var(--light-blue);
}
.choose-facet button.active:hover {
  background-color: var(--deep-blue);
  transform: scale(1.05);
}
.choose-facet button:hover:not(.active) {
  background-color: var(--white-mute);
  transform: scale(1.05);
}
.choose-facet .material-icons {
  font-size: 28px;
  color: inherit;
}
</style>
  