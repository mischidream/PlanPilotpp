<template>
    <div class="input-fields">
        <InputField label="Problem file:" v-model="instanceFile" type="file" accept=".pddl" />
        <InputField label="Domain file:" v-model="domainFile" type="file" accept=".pddl" />
        <InputField label="Horizon:" v-model="horizon" type="number" placeholder="Enter horizon" />
        <DropdownField
            label="Encoding:"
            :options="Object.values(EncodingType)"
            v-model="encoding"
            :isMultiple="false"
        />
        <InputField label="Number of sets:" v-model="numberOfSets" type="number" />
    </div>
    <Divider/>
    <div class="search-fields">
        <DropdownField
            label="Facet:"
            :options="Object.values(SelectionState)"
            v-model="selectedFacetState"
            :isMultiple="true"
        />
        <DropdownField
            label="Action:"
            :options="Object.values(ActionType)"
            v-model="selectedActionType"
            :isMultiple="true"
        />
        <DropdownField
            label="Constants:"
            :options="allConstants"
            v-model="selectedConstants"
            :isMultiple="true"
        />
        <DropdownField
            label="Timesteps:"
            :options="allTimesteps"
            v-model="selectedTimesteps"
            :isMultiple="true"
        />
    </div>
    <Divider/>
    <FacetTable
        :headers="columns"
        :facets="filteredFacets"
        @selectFacet="updateSelectionState"
    />
</template>

<script setup lang="ts">
import { EncodingType } from '@/models/EncodingType';
import { SelectionState } from '@/models/SelectionState';
import { ActionType } from '@/models/ActionType';
import type { Facet } from '@/models/Facet';
import { computed, onMounted, ref, watch } from 'vue';
import InputField from '@/components/InputField.vue';
import DropdownField from '@/components/DropdownField.vue';
import Divider from '@/components/Divider.vue';
import FacetTable from '@/components/FacetTable.vue';
import testData from '@/testdata/example.json'
import { transformToFacets } from '@/utils/transformFacets';

const instanceFile = ref<File | null>(null);
const domainFile = ref<File | null>(null);
const horizon = ref<number>(0);
const encoding = ref<EncodingType[]>([EncodingType.Exact])
const numberOfSets = ref<number | undefined>(undefined);
const facets = ref<Facet[]>([]);
const showReductionColumns = ref(false);

const selectedFacetState = ref<SelectionState[]>([])
const selectedActionType = ref<ActionType[]>([])
const selectedConstants = ref<string[]>([])
const selectedTimesteps = ref<number[]>([]);

const allConstants = computed(() => {
    const constantsSet = new Set<string>();
    for (const facet of facets.value) {
        if (facet.constant1) constantsSet.add(facet.constant1);
        if (facet.constant2) constantsSet.add(facet.constant2);
    }
    return Array.from(constantsSet).sort();
});

const allTimesteps = computed(() => {
    const timestepSet = new Set<number>();
    for (const facet of facets.value) {
        timestepSet.add(facet.timestep);
    }
    return Array.from(timestepSet).sort((a, b) => a - b);
});

const columns = computed(() => {
  const base = ['Choose facet', 'Action', 'Constants', 'Timestep'];
  return showReductionColumns.value ? [...base, 'Reduction', 'Remaining'] : base;
});

// Computed filtered facets based on search
const filteredFacets = computed(() => {
  return facets.value.filter(facet => {
    const matchState = !selectedFacetState.value.length || selectedFacetState.value.includes(facet.selectionState ?? SelectionState.NotSelected);
    const matchAction = !selectedActionType.value.length || selectedActionType.value.includes(facet.action);
    const constants = [facet.constant1, facet.constant2].filter(Boolean) as string[];
    const matchConstants = !selectedConstants.value.length || constants.some(c => selectedConstants.value.includes(c));
    const matchTimestep = !selectedTimesteps.value.length || selectedTimesteps.value.includes(facet.timestep);
    return matchState && matchAction && matchConstants && matchTimestep;
  });
});

// Update selectionState when a facet is selected
function updateSelectionState(facet: Facet, newState: SelectionState) {
  facet.selectionState = newState;
}

watch([selectedFacetState, selectedActionType, selectedConstants, selectedTimesteps], () => {
    console.log("Filtering facets with:", {
        selectedFacetState: selectedFacetState.value,
        selectedActionType: selectedActionType.value,
        selectedConstants: selectedConstants.value,
        selectedTimesteps: selectedTimesteps.value
    });
});

// Load test data and transform it to facets
onMounted(() => {
    facets.value = transformToFacets(testData);
});
</script>

<style scoped>
.input-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}
.search-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}
</style>