<template>
    <div class="input-fields">
        <InputField label="Problem file:" :modelValue="instanceFile" type="file" :disabled="true" />
        <InputField label="Domain file:" :modelValue="domainFile" type="file" :disabled="true" />
        <InputField label="Horizon:" v-model="horizon" type="number" :placeholder="minHorizon?.toString()" />
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
        <InputField label="Restricted To:" v-model="numberOfSolutions" type="number" />
        <Button label="Number of Answer Sets" type="button" @click="countAnswerSets"></Button>
        <Button label="Number of Facets" type="button" @click="countFacets"></Button>
        <Button label="Query Remaining Facets" type="button" @click="queryRemainingFacets"></Button>
        <Button label="Query Remaining Answer Sets" type="button" @click="queryRemainingAnswerSets"></Button>
    </div>
    <div v-if="answerSetCount || facetCount">
      <Divider/>
      <div class="count">
        <p v-if="answerSetCount">Answer Sets: {{ answerSetCount }}</p>
        <p v-if="facetCount">Facets: {{ facetCount }}</p>
      </div>
     </div>
    <Divider/>
    <div v-if="!isFirstRun">
      <div v-if="viewMode === 'facets' || viewMode === 'query'">
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
      </div>
      <FacetTable
          :key="viewMode"
          :headers="columns"
          :facets="viewMode === 'facets' || viewMode === 'query' ? paginatedFacets : undefined"
          :solutions="viewMode === 'solutions' ? paginatedAnswerSets : undefined"
          :viewMode="viewMode"
          @selectFacet="updateFacetSelectionState"
      />
      <Paginator
          v-model:currentPage="currentPage"
          :totalItems="viewMode === 'facets' || viewMode === 'query' ? filteredFacets.length : answerSets.length"
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
import { runPlanPilot, sendPlanPilotCommand, updateSelectionState } from '@/services/apiService';
import type { AnswerSet } from '@/models/AnswerSet';

// Store
const planStore = usePlanStore();
const instanceFile = computed(() => planStore.instanceFile);
const domainFile = computed(() => planStore.domainFile);
const sasFile = computed(() => planStore.sasFile);
const minHorizon = computed(() => planStore.horizon);
const horizon = ref<number>(planStore.horizon);

// Other values
const encoding = ref<EncodingType[]>([EncodingType.exact]);
const numberOfSolutions = ref<number | undefined>(undefined);
const facets = ref<Facet[]>([]);
const selectedFacets = ref<Facet[]>([]);
const answerSets = ref<AnswerSet[]>([]);
const answerSetCount = ref<string | null>(null);
const facetCount = ref<string | null>(null);
const viewMode = ref<'facets' | 'solutions' | 'query'>('facets');
const isFirstRun = ref(true);
const lastUsedHorizon = ref<number | null>(null);
const lastUsedEncoding = ref<EncodingType | null>(null);

// Search filters
const selectedFacetState = ref<SelectionState[]>([]);
const selectedActionType = ref<ActionType[]>([]);
const selectedConstants = ref<string[]>([]);
const selectedTimesteps = ref<number[]>([]);

// Pagination
const currentPage = ref(1);
const itemsPerPage = 4;

// === Sync with store ===
watch(horizon, (val) => planStore.setHorizon(val));
watch(minHorizon, (val) => planStore.setMinHorizon);
watch(encoding, ([val]) => val && planStore.setEncoding(val));
watch(facets, (val) => planStore.setFacets(val));
watch(answerSets, (val) => planStore.setAnswerSets(val));
watch(viewMode, (val) => planStore.setViewMode(val));

watch(selectedFacetState, (val) => planStore.setSelectedFacetState(val), { deep: true });
watch(selectedActionType, (val) => planStore.setSelectedActionType(val), { deep: true });
watch(selectedConstants, (val) => planStore.setSelectedConstants(val), { deep: true });
watch(selectedTimesteps, (val) => planStore.setSelectedTimesteps(val), { deep: true });

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
  let base: string[];
  if (viewMode.value === "solutions") {
    base = ['Solutions', 'Action', 'Constants', 'Timestep'];
  } else if (viewMode.value === "query") {
    base = ['Choose facet', 'Action', 'Constants', 'Timestep', 'Significance + | -', 'Remaining + | -'];
  } else {
    return ['Choose facet', 'Action', 'Constants', 'Timestep'];
  }
  return base;
});

// Computed filtered facets based on search
const filteredFacets = computed(() => {
  const leftovers = facets.value.filter(facet => {
    const matchState = !selectedFacetState.value.length || selectedFacetState.value.includes(facet.selectionState ?? SelectionState.NotSelected);
    const matchAction = !selectedActionType.value.length || selectedActionType.value.includes(facet.action);
    const constants = [facet.constant1, facet.constant2].filter(Boolean) as string[];
    const matchConstants = !selectedConstants.value.length || constants.some(c => selectedConstants.value.includes(c));
    const matchTimestep = !selectedTimesteps.value.length || selectedTimesteps.value.includes(facet.timestep);
    return matchState && matchAction && matchConstants && matchTimestep;
  });
  console.log("filteredFacets", [...selectedFacets.value, ...leftovers])
  return [...selectedFacets.value, ...leftovers];
});

// Paginate filtered facets
const paginatedFacets = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  return filteredFacets.value.slice(start, start + itemsPerPage);
});

const paginatedAnswerSets = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  return answerSets.value.slice(start, start + itemsPerPage);
});

// Reset to page 1 on filter change
watch(
  [selectedFacetState, selectedActionType, selectedConstants, selectedTimesteps],
  () => {
    currentPage.value = 1;
  },
  { deep: true }
);

// Update selectionState when a facet is selected
async function updateFacetSelectionState(facet: Facet, newState: SelectionState) {
  try {
    answerSetCount.value = null;
    facetCount.value = null;

    const output = await updateSelectionState(facet, newState);
    
    if (newState !== SelectionState.NotSelected) {
      const alreadySelected = selectedFacets.value.find(f => f.id === facet.id);
      if (!alreadySelected) {
        facet.selectionState = newState;
        selectedFacets.value.push({...facet});
      } else {
        alreadySelected.selectionState = newState;
      }
    } else {
      selectedFacets.value = selectedFacets.value.filter(f => f.id !== facet.id);
    }

    if (Array.isArray(output)) {
      facets.value = output as Facet[];
      currentPage.value = 1;
      viewMode.value = 'facets';
    }
  } catch (error) {
    console.error('Error updating selection state:', error);
  }
}

const listFacets = async () => {
  try {
    answerSetCount.value = null;
    facetCount.value = null;
    const horizonChanged = lastUsedHorizon.value !== horizon.value;
    const encodingChanged = lastUsedEncoding.value !== encoding.value[0];
    let result;
    if (isFirstRun.value || horizonChanged || encodingChanged) {
      result = await runPlanPilot(sasFile.value, horizon.value, encoding.value[0]);
      isFirstRun.value = false;
      lastUsedHorizon.value = horizon.value;
      lastUsedEncoding.value = encoding.value[0];
      console.log(isFirstRun.value);
    } else {
      result = await sendPlanPilotCommand('?');
    }
    if (result) {
      facets.value = result as Facet[];
      currentPage.value = 1;
      viewMode.value = 'facets';
    }
  } catch (error) {
    console.error('Error running PlanPilot:', error);
  }
};

const listSolutions = async () => {
  try {
    answerSetCount.value = null;
    facetCount.value = null;
    const command = numberOfSolutions.value
      ? `! ${numberOfSolutions.value}`
      : '!';
    const output = await sendPlanPilotCommand(command);
    if (Array.isArray(output)) {
      answerSets.value = output as AnswerSet[];
      currentPage.value = 1;
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

const queryRemainingFacets = async () => {
  try {
    const updatedFacets = await sendPlanPilotCommand('#??');

    if (Array.isArray(updatedFacets)) {
      facets.value = updatedFacets as Facet[];
      currentPage.value = 1;
      viewMode.value = 'query';
    } else {
      console.warn('Unexpected output format for remaining facets:', updatedFacets);
    }
  } catch (error) {
    console.error('Error querying remaining facets:', error);
  }
};

const queryRemainingAnswerSets = async () => {
  try {
    const updatedFacets = await sendPlanPilotCommand('#!!');

    if (Array.isArray(updatedFacets)) {
      facets.value = updatedFacets as Facet[];
      currentPage.value = 1;
      viewMode.value = 'query';
    } else {
      console.warn('Unexpected output format for remaining answer sets:', updatedFacets);
    }
  } catch (error) {
    console.error('Error querying remaining answer sets:', error);
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

.count {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}
</style>