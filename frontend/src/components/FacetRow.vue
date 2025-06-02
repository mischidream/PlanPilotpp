<template>
  <div class="facet-row">
    <!-- Choose Facet -->
    <div v-if="viewMode !== 'landmarks'" class="facet-cell choose-facet">
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
      <template v-if="facet.constant2"> {{ facet.constant1 }} | {{ facet.constant2 }} </template>
      <template v-else>
        {{ facet.constant1 }}
      </template>
    </div>

    <!-- Timestep -->
    <div class="facet-cell">{{ facet.timestep === 0 ? 'sometime' : facet.timestep }}</div>

    <!-- Reduction -->
    <div class="facet-cell" v-if="showReduction">{{ showReduction }}</div>

    <!-- Remaining -->
    <div class="facet-cell" v-if="showRemaining">{{ showRemaining }}</div>
  </div>
</template>

<script lang="ts" setup>
import type { Facet } from '@/models/Facet';
import { SelectionState } from '@/models/SelectionState';
import { computed } from 'vue';

const props = defineProps<{
  facet: Facet;
  readonly?: boolean;
  viewMode?: 'facets' | 'solutions' | 'query' | 'landmarks';
  onSelectFacet?: (facet: Facet, newState: SelectionState) => void;
}>();

function toggleState(state: SelectionState) {
  if (!props.onSelectFacet) return;
  const current = props.facet.selectionState;
  const newState = current === state ? SelectionState.NotSelected : state;
  props.onSelectFacet(props.facet, newState);
}

const showReduction = computed(() => {
  if (props.viewMode !== 'query') return null;

  const red = props.facet.reduction;
  if (red?.facets?.positive != null && red?.facets?.negative != null) {
    return `${red.facets.positive} | ${red.facets.negative}`;
  }
  if (red?.solution?.positive != null && red?.solution?.negative != null) {
    return `${red.solution.positive} | ${red.solution.negative}`;
  }
  return null;
});

const showRemaining = computed(() => {
  if (props.viewMode !== 'query') return null;

  const rem = props.facet.remaining;
  if (rem?.facets?.positive != null && rem?.facets?.negative != null) {
    return `${rem.facets.positive} | ${rem.facets.negative}`;
  }
  if (rem?.solution?.positive != null && rem?.solution?.negative != null) {
    return `${rem.solution.positive} | ${rem.solution.negative}`;
  }
  return null;
});
</script>

<style scoped>
.facet-row {
  display: flex;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}

.facet-row:first-child {
  padding-top: 0;
}

.facet-cell {
  flex: 1;
  display: flex;
  align-items: center;
}

.choose-facet button {
  margin-right: 0.3125rem;
  cursor: pointer;
  background: transparent;
  border: 0.125rem solid var(--black);
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
  font-size: 1.75rem;
  color: inherit;
}
</style>
