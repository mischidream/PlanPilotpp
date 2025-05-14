<template>
    <div class="input-fields">
        <InputField label="Problem file:" :modelValue="instanceFile" type="file" :disabled="false" />
        <InputField label="Domain file:" :modelValue="domainFile" type="file" :disabled="false" />
        <InputField label="Horizon:" v-model="horizon" type="number" placeholder="${minHorizon}" />
        <DropdownField
            label="Encoding:"
            :options="Object.values(EncodingType)"
            v-model="encoding"
            :isMultiple="false"
        />
        <Button label="List Facets" type="submit" @click="listFacets"></Button>
    </div>
    <div class="button-input">
        <Button label="List Solutions" type="submit" @click="listSolutions"></Button>
        <InputField label="Restricted to:" v-model="numberOfSolutions" type="number" />
        <Button label="Number of Answer sets" type="button" @click="countAnswerSets"></Button>
        <Button label="Number of Facets" type="button" @click="countFacets"></Button>
    </div>
    <Divider v-if="answerSetCount || facetCount"></Divider>
        <p v-if="answerSetCount">Answer Sets: {{ answerSetCount }}</p>
        <p v-if="facetCount">Facets: {{ facetCount }}</p>
    <Divider/>
    <div v-if="!isFirstRun">
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
          :facets="viewMode === 'facets' ? paginatedFacets : undefined"
          :solutions="viewMode === 'solutions' ? answerSets : undefined"
          :viewMode="viewMode"
          @selectFacet="updateSelectionState"
      />
      <Paginator
          v-model:currentPage="currentPage"
          :totalItems="filteredFacets.length"
          :itemsPerPage="itemsPerPage"
      />
    </div>
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
import Paginator from '@/components/Paginator.vue';
import Button from '@/components/Button.vue';
import testData from '@/testdata/example_facets.json';
import testDataAnswerSet from '@/testdata/example_answer_sets.json';
import { transformToFacets } from '@/utils/transformFacets';
import { usePlanStore } from '@/stores/planStore';
import { runPlanPilot, sendPlanPilotCommand } from '@/services/apiService';
import type { AnswerSet } from '@/models/AnswerSet';

// Store
const planStore = usePlanStore();
const instanceFile = computed(() => planStore.instanceFile);
const domainFile = computed(() => planStore.domainFile);
const sasFile = planStore.sasFile;
const minHorizon = computed(() => planStore.horizon);
const horizon = ref<number>(planStore.horizon);

// Other values
const encoding = ref<EncodingType[]>([EncodingType.exact]);
const numberOfSolutions = ref<number | undefined>(undefined);
const facets = ref<Facet[]>([]);
const answerSets = ref<AnswerSet[]>([]);
const showReductionColumns = ref(false);
const answerSetCount = ref<string | null>(null);
const facetCount = ref<string | null>(null);
const viewMode = ref<'facets' | 'solutions'>('facets');
let isFirstRun = true;

// Search filters
const selectedFacetState = ref<SelectionState[]>([]);
const selectedActionType = ref<ActionType[]>([]);
const selectedConstants = ref<string[]>([]);
const selectedTimesteps = ref<number[]>([]);

// Pagination
const currentPage = ref(1);
const itemsPerPage = 4;

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

// Paginate filtered facets
const paginatedFacets = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  return filteredFacets.value.slice(start, start + itemsPerPage);
});

// Reset to page 1 on filter change
watch(
  [selectedFacetState, selectedActionType, selectedConstants, selectedTimesteps],
  () => {
    currentPage.value = 1;
  }
);

// Update selectionState when a facet is selected
function updateSelectionState(facet: Facet, newState: SelectionState) {
  facet.selectionState = newState;
  console.log(facet.selectionState);
}

const listFacets = async () => {
  try {
    let result;
    if (isFirstRun) {
      result = await runPlanPilot(sasFile, horizon.value, encoding.value[0]);
      isFirstRun = false;
    } else {
      result = await sendPlanPilotCommand('?');
    }
    if (result) {
      facets.value = result as Facet[];
      viewMode.value = 'facets';
    }
  } catch (error) {
    console.error('Error running PlanPilot:', error);
  }
};

const listSolutions = async () => {
  try {
    const command = numberOfSolutions.value
      ? `! ${numberOfSolutions.value}`
      : '!';
    const output = await sendPlanPilotCommand(command);
    if (Array.isArray(output)) {
      answerSets.value = output as AnswerSet[];
      viewMode.value = 'solutions';
    } else {
      console.warn('Unexpected output format for solutions:', output);
    }
  } catch (error) {
    console.error('Error sending command:', error);
  }
};

const countAnswerSets = async () => {
  try {
    const output = await sendPlanPilotCommand('#!');
    answerSetCount.value = typeof output === 'string' ? output : null;
  } catch (error) {
    console.error('Error:', error);
  }
};

const countFacets = async () => {
  try {
    const output = await sendPlanPilotCommand('#?');
    facetCount.value = typeof output === 'string' ? output : null;
  } catch (error) {
    console.error('Error:', error);
  }
};

// Load test data and transform it to facets
onMounted(() => {
    //facets.value = transformToFacets(testData);
    //answerSets.value = testDataAnswerSet as AnswerSet[];
    //viewMode.value = 'solutions';
});
</script>

<style scoped>
.input-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 20px;
}
.input-fields .button {
    align-self: flex-end;
}
.button-input {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}
.button-input .button{
    align-self: flex-end;
}
.search-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}
</style>