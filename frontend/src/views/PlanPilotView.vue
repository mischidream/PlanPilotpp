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
    <div v-if="loadingFacetCount || loadingAnswerSetCount || answerSetCount || facetCount">
      <Divider/>
      <div class="count">
        <p v-if="!answerSetCount && loadingAnswerSetCount"><SkeletonCount/></p>
        <p v-else-if="answerSetCount">Answer Sets: {{ answerSetCount }}</p>
        <p v-if="!facetCount && loadingFacetCount"><SkeletonCount/></p>
        <p v-else-if="facetCount">Facets: {{ facetCount }}</p>
      </div>
     </div>
    <Divider/>
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
              label="Objects:"
              :options="allObjects"
              v-model="selectedObjects"
              :isMultiple="true"
          />
          <DropdownField
              label="Timesteps:"
              :options="allTimesteps"
              v-model="selectedTimesteps"
              :isMultiple="true"
          />
          <Button label="Reset filters" type="submit" @click="resetFilters"></Button>
        </div>
        <Divider/>
      </div>
      <FacetTableView
        :headers="columns"
        :facets="filteredFacets"
        :answerSets="answerSets"
        :viewMode="viewMode"
        :loading="loading"
        :itemsPerPage="itemsPerPage"
        :currentPage="currentPage"
        @update:currentPage="handlePageUpdate"
        @selectFacet="updateFacetSelectionState"
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
import Paginator from '@/components/Paginator.vue';
import Button from '@/components/Button.vue';
import SkeletonCount from '@/components/SkeletonCount.vue';
import testData from '@/testdata/example_facets.json';
import testDataAnswerSet from '@/testdata/example_answer_sets.json';
import { transformToFacets } from '@/utils/transformFacets';
import { usePlanStore } from '@/stores/planStore';
import { runPlanPilot, sendPlanPilotCommand, updateSelectionState } from '@/services/apiService';
import type { AnswerSet } from '@/models/AnswerSet';
import FacetTableView from '@/components/FacetTableView.vue';

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
const loading = ref(false);
const loadingAnswerSetCount = ref(false);
const loadingFacetCount = ref(false);

// Search filters
const selectedFacetState = ref<SelectionState[]>([]);
const selectedActionType = ref<ActionType[]>([]);
const selectedObjects = ref<string[]>([]);
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
watch(selectedObjects, (val) => planStore.setSelectedObjects(val), { deep: true });
watch(selectedTimesteps, (val) => planStore.setSelectedTimesteps(val), { deep: true });

function handlePageUpdate(val: number) {
  currentPage.value = val;
}

const allObjects = computed(() => {
    const objectsSet = new Set<string>();
    for (const facet of facets.value) {
        if (facet.constant1) objectsSet.add(facet.constant1);
        if (facet.constant2) objectsSet.add(facet.constant2);
    }
    return Array.from(objectsSet).sort();
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
    base = ['Solutions', 'Action', 'Objects', 'Timestep'];
  } else if (viewMode.value === "query") {
    base = ['Choose facet', 'Action', 'Objects', 'Timestep', 'Significance + | -', 'Remaining + | -'];
  } else {
    return ['Choose facet', 'Action', 'Objects', 'Timestep'];
  }
  return base;
});

// Computed filtered facets based on search
const filteredFacets = computed(() => {
  const matchesFilters = (facet: Facet) => {
    const matchState = !selectedFacetState.value.length || selectedFacetState.value.includes(facet.selectionState as SelectionState);
    const matchAction = !selectedActionType.value.length || selectedActionType.value.includes(facet.action);
    const objects = [facet.constant1, facet.constant2].filter(Boolean) as string[];
    const matchObjects = !selectedObjects.value.length || objects.some(c => selectedObjects.value.includes(c));
    const matchTimestep = !selectedTimesteps.value.length || selectedTimesteps.value.includes(facet.timestep);
    return matchState && matchAction && matchObjects && matchTimestep;
  };

  const filteredSelected = selectedFacets.value.filter(matchesFilters);
  const selectedIds = new Set(filteredSelected.map(f => f.id));

  const filteredOthers = facets.value
    .filter(f => !selectedIds.has(f.id))
    .filter(matchesFilters);

  const result = [...filteredSelected, ...filteredOthers];
  console.log("filteredFacets", result);
  return result;
});

// Reset to page 1 on filter change
watch(
  [selectedFacetState, selectedActionType, selectedObjects, selectedTimesteps],
  () => {
    currentPage.value = 1;
  },
  { deep: true }
);

watch(facets, () => {
  const availableTimesteps = new Set(facets.value.map(f => f.timestep));
  selectedTimesteps.value = selectedTimesteps.value.filter(t => availableTimesteps.has(t));

  const availableObjects = new Set(
    facets.value.flatMap(f => [f.constant1, f.constant2].filter(Boolean) as string[])
  );
  selectedObjects.value = selectedObjects.value.filter(c => availableObjects.has(c));

  const availableStates = new Set(facets.value.map(f => f.selectionState));
  selectedFacetState.value = selectedFacetState.value.filter(s => availableStates.has(s));

  const availableActions = new Set(facets.value.map(f => f.action));
  selectedActionType.value = selectedActionType.value.filter(a => availableActions.has(a));
});


function resetFilters() {
  selectedFacetState.value = [];
  selectedActionType.value = [];
  selectedObjects.value = [];
  selectedTimesteps.value = [];
}

// Update selectionState when a facet is selected
async function updateFacetSelectionState(facet: Facet, newState: SelectionState) {
  loading.value = true;
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
  } finally {
    loading.value = false;
  }
}

const listFacets = async () => {
  loading.value = true;
  try {
    viewMode.value = 'facets';
    answerSetCount.value = null;
    facetCount.value = null;
    const horizonChanged = lastUsedHorizon.value !== horizon.value;
    const encodingChanged = lastUsedEncoding.value !== encoding.value[0];
    let result;
    if (isFirstRun.value || horizonChanged || encodingChanged) {
      selectedFacets.value = [];
      result = await runPlanPilot(sasFile.value, horizon.value, encoding.value[0]);
      isFirstRun.value = false;
      lastUsedHorizon.value = horizon.value;
      lastUsedEncoding.value = encoding.value[0];
    } else {
      result = await sendPlanPilotCommand('?');
    }
    if (result) {
      facets.value = result as Facet[];
      currentPage.value = 1;
    }
  } catch (error) {
    console.error('Error running PlanPilot:', error);
  } finally {
    loading.value = false;
  }
};

const listSolutions = async () => {
  loading.value = true;
  try {
    viewMode.value = 'solutions';
    answerSetCount.value = null;
    facetCount.value = null;
    const command = numberOfSolutions.value
      ? `! ${numberOfSolutions.value}`
      : '!';
    const output = await sendPlanPilotCommand(command);
    if (Array.isArray(output)) {
      answerSets.value = output as AnswerSet[];
      currentPage.value = 1;
    } else {
      console.warn('Unexpected output format for solutions:', output);
    }
  } catch (error) {
    console.error('Error sending command:', error);
  } finally {
    loading.value = false;
  }
};

const countAnswerSets = async () => {
  loadingAnswerSetCount.value = true;
  try {
    const output = await sendPlanPilotCommand('#!');
    answerSetCount.value = typeof output === 'string' ? output : null;
  } catch (error) {
    console.error('Error:', error);
  } finally {
    loadingAnswerSetCount.value = false;
  }
};

const countFacets = async () => {
  loadingFacetCount.value = true;
  try {
    const output = await sendPlanPilotCommand('#?');
    facetCount.value = typeof output === 'string' ? output : null;
  } catch (error) {
    console.error('Error:', error);
  } finally {
    loadingFacetCount.value = false;
  }
};

const queryRemainingFacets = async () => {
  loading.value = true;
  try {
    viewMode.value = 'query';
    const updatedFacets = await sendPlanPilotCommand('#??');

    if (Array.isArray(updatedFacets)) {
      facets.value = updatedFacets as Facet[];
      currentPage.value = 1;
    } else {
      console.warn('Unexpected output format for remaining facets:', updatedFacets);
    }
  } catch (error) {
    console.error('Error querying remaining facets:', error);
  } finally {
    loading.value = false;
  }
};

const queryRemainingAnswerSets = async () => {
  loading.value = true;
  try {
    viewMode.value = 'query';
    const updatedFacets = await sendPlanPilotCommand('#!!');

    if (Array.isArray(updatedFacets)) {
      facets.value = updatedFacets as Facet[];
      currentPage.value = 1;
    } else {
      console.warn('Unexpected output format for remaining answer sets:', updatedFacets);
    }
  } catch (error) {
    console.error('Error querying remaining answer sets:', error);
  } finally {
    loading.value = false;
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

.search-fields .button{
  align-self: flex-end;
}

.count {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}
</style>