<template>
  <div class="layout">
    <div class="main-content">
      <div class="input-fields">
        <InputField label="Problem file:" :modelValue="instanceFile" type="file" :disabled="true" />
        <InputField label="Domain file:" :modelValue="domainFile" type="file" :disabled="true" />
        <InputField
          label="Horizon:"
          v-model="horizon"
          type="number"
          :placeholder="minHorizon?.toString()"
        />
        <DropdownField
          label="Encoding:"
          :options="Object.values(EncodingType)"
          v-model="encoding"
          :isMultiple="false"
        />
        <DropdownField
          label="Time Steps:"
          :options="Object.values(TimeStepType)"
          v-model="timeStep"
          :isMultiple="false"
        />
        <Button label="List Facets" type="submit" @click="listFacets"></Button>
      </div>
      <div class="button-input">
        <div class="button-input-group">
          <Button label="List Solutions" type="submit" @click="listSolutions"></Button>
          <InputField label="Restricted To:" v-model="numberOfSolutions" type="number" />
        </div>
        <Button label="Number of Solutions" type="button" @click="countSolutions"></Button>
        <Button label="Number of Facets" type="button" @click="countFacets"></Button>
        <Button label="Query Remaining Facets" type="button" @click="queryRemainingFacets"></Button>
        <Button
          label="Query Remaining Solutions"
          type="button"
          @click="queryRemainingSolutions"
        ></Button>
        <div class="button-input-group">
          <Button label="Implied Actions" type="submit" @click="listLandmarks"></Button>
          <InputField label="Restricted To:" v-model="landmarkAction" type="text" />
        </div>
      </div>
      <FacetCountDisplay
        :loadingSolutionCount="loadingSolutionCount"
        :loadingFacetCount="loadingFacetCount"
        :solutionCount="solutionCount"
        :facetCount="facetCount"
      />
      <Divider />
      <div v-if="viewMode === 'facets' || viewMode === 'query'">
        <FacetFilterPanel
          :selectedFacetState="selectedFacetState"
          :selectedActionType="selectedActionType"
          :selectedObjects="selectedObjects"
          :selectedTimesteps="selectedTimesteps"
          :allObjects="allObjects"
          :allTimesteps="allTimesteps"
          @update:selectedFacetState="val => (selectedFacetState = val)"
          @update:selectedActionType="val => (selectedActionType = val)"
          @update:selectedObjects="val => (selectedObjects = val)"
          @update:selectedTimesteps="val => (selectedTimesteps = val)"
        />
        <Divider />
      </div>
      <FacetTableView
        :headers="columns"
        :facets="filteredFacets"
        :solutions="solutions"
        :viewMode="viewMode"
        :loading="loading"
        :itemsPerPage="itemsPerPage"
        :currentPage="currentPage"
        @update:currentPage="handlePageUpdate"
        @selectFacet="updateFacetSelectionState"
      />
    </div>
    <LandmarkSidebar
      :landmarks="landmarks"
      :loadingLandmarks="loadingLandmarks"
      :enabled="sidebarEnabled"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import type { Facet } from '@/models/Facet';
import type { Solution } from '@/models/Solution';
import { ActionType } from '@/models/ActionType';
import { EncodingType } from '@/models/EncodingType';
import { SelectionState } from '@/models/SelectionState';
import { TimeStepType } from '@/models/TimeStepType';
import { usePlanStore } from '@/stores/planStore';
import { runPlanPilot, sendPlanPilotCommand, updateSelectionState } from '@/services/apiService';
import Button from '@/components/Button.vue';
import Divider from '@/components/Divider.vue';
import DropdownField from '@/components/DropdownField.vue';
import FacetCountDisplay from '@/components/FacetCountDisplay.vue';
import FacetFilterPanel from '@/components/FacetFilterPanel.vue';
import FacetTableView from '@/components/FacetTableView.vue';
import InputField from '@/components/InputField.vue';
import LandmarkSidebar from '@/components/LandmarkSidebar.vue';
import { bindWatch } from '@/utils/bindWatch';
import { getAllObjects } from '@/utils/getAllObjects';
import { getAllTimesteps } from '@/utils/getAllTimesteps';
import { getFacetTableColumns } from '@/utils/getFacetTableColumns';
import { transformToFacets } from '@/utils/transformFacets';
import { useFacetFilters } from '@/composables/useFacetFilters';
import testData from '@/testdata/example_facets.json';
import testDataSolution from '@/testdata/example_answer_sets.json';

// Store
const planStore = usePlanStore();
const instanceFile = computed(() => planStore.instanceFile);
const domainFile = computed(() => planStore.domainFile);
const sasFile = computed(() => planStore.sasFile);
const horizon = ref<number>(planStore.horizon);

// Planning configuration
const minHorizon = ref(horizon.value);
const encoding = ref<EncodingType[]>([EncodingType.exact]);
const timeStep = ref<TimeStepType[]>([TimeStepType.concrete]);
const numberOfSolutions = ref<number | undefined>(undefined);
const landmarkAction = ref<string | undefined>(undefined);

// Data collections
const facets = ref<Facet[]>([]);
const selectedFacets = ref<Facet[]>([]);
const landmarks = ref<Facet[]>([]);
const solutions = ref<Solution[]>([]);

// Count information
const solutionCount = ref<string | null>(null);
const facetCount = ref<string | null>(null);

// UI state
const viewMode = ref<'facets' | 'solutions' | 'query'>('facets');
const isFirstRun = ref(true);
const sidebarEnabled = ref(false);

// Last used settings
const lastUsedHorizon = ref<number | null>(null);
const lastUsedEncoding = ref<EncodingType | null>(null);
const lastUsedTimeStep = ref<TimeStepType | null>(null);

// Loading states
const loading = ref(false);
const loadingSolutionCount = ref(false);
const loadingFacetCount = ref(false);
const loadingLandmarks = ref(false);

// Filters for search
const selectedFacetState = ref<SelectionState[]>([]);
const selectedActionType = ref<ActionType[]>([]);
const selectedObjects = ref<string[]>([]);
const selectedTimesteps = ref<string[]>([]);

// Pagination
const currentPage = ref(1);
const itemsPerPage = 4;

// Sync with store
bindWatch(horizon, planStore.setHorizon);
bindWatch(minHorizon, planStore.setMinHorizon);
bindWatch(encoding, ([val]) => val && planStore.setEncoding(val));
bindWatch(timeStep, ([val]) => val && planStore.setTimeStep(val));

bindWatch(facets, planStore.setFacets);
bindWatch(landmarks, planStore.setLandmarks);
bindWatch(solutions, planStore.setSolutions);

bindWatch(viewMode, planStore.setViewMode);

bindWatch(selectedFacetState, planStore.setSelectedFacetState, { deep: true });
bindWatch(selectedActionType, planStore.setSelectedActionType, { deep: true });
bindWatch(selectedObjects, planStore.setSelectedObjects, { deep: true });
bindWatch(selectedTimesteps, planStore.setSelectedTimesteps, { deep: true });

function handlePageUpdate(val: number) {
  currentPage.value = val;
}

const allObjects = getAllObjects(facets, selectedFacets);

const allTimesteps = getAllTimesteps(facets, selectedFacets);

const columns = computed(() => getFacetTableColumns(viewMode.value));

// Computed filtered facets based on search
const { filteredFacets } = useFacetFilters(
  facets,
  selectedFacets,
  selectedFacetState,
  selectedActionType,
  selectedObjects,
  selectedTimesteps
);

// Reset to page 1 on filter change
watch(
  [selectedFacetState, selectedActionType, selectedObjects, selectedTimesteps],
  () => {
    currentPage.value = 1;
  },
  { deep: true }
);

// Update selectionState when a facet is selected
async function updateFacetSelectionState(facet: Facet, newState: SelectionState) {
  loading.value = true;
  try {
    solutionCount.value = null;
    facetCount.value = null;
    landmarks.value = [];
    sidebarEnabled.value = false;

    const output = await updateSelectionState({
      facet,
      newState,
    });

    if (newState !== SelectionState.NotSelected) {
      const alreadySelected = selectedFacets.value.find(f => f.id === facet.id);
      if (!alreadySelected) {
        facet.selectionState = newState;
        selectedFacets.value.push({ ...facet });
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
    const horizonChanged = lastUsedHorizon.value !== horizon.value;
    const encodingChanged = lastUsedEncoding.value !== encoding.value[0];
    const timeStepChanged = lastUsedTimeStep.value !== timeStep.value[0];
    let result;
    if (isFirstRun.value || horizonChanged || encodingChanged || timeStepChanged) {
      solutionCount.value = null;
      facetCount.value = null;
      landmarks.value = [];
      sidebarEnabled.value = false;
      selectedFacets.value = [];
      result = await runPlanPilot({
        sasFile: sasFile.value,
        horizon: horizon.value,
        encoding: encoding.value[0],
        abstractTimeStep: timeStep.value[0] !== TimeStepType.concrete,
      });
      isFirstRun.value = false;
      lastUsedHorizon.value = horizon.value;
      lastUsedEncoding.value = encoding.value[0];
      lastUsedTimeStep.value = timeStep.value[0];
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
    solutionCount.value = null;
    facetCount.value = null;
    const command = numberOfSolutions.value ? `! ${numberOfSolutions.value}` : '!';
    const output = await sendPlanPilotCommand(command);
    if (Array.isArray(output)) {
      solutions.value = output as Solution[];
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

const countSolutions = async () => {
  loadingSolutionCount.value = true;
  try {
    const output = await sendPlanPilotCommand('#!');
    solutionCount.value = typeof output === 'string' ? output : null;
  } catch (error) {
    console.error('Error:', error);
  } finally {
    loadingSolutionCount.value = false;
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

const queryRemainingSolutions = async () => {
  loading.value = true;
  try {
    viewMode.value = 'query';
    const updatedFacets = await sendPlanPilotCommand('#!!');

    if (Array.isArray(updatedFacets)) {
      facets.value = updatedFacets as Facet[];
      currentPage.value = 1;
    } else {
      console.warn('Unexpected output format for remaining solutions:', updatedFacets);
    }
  } catch (error) {
    console.error('Error querying remaining solutions:', error);
  } finally {
    loading.value = false;
  }
};

const listLandmarks = async () => {
  loadingLandmarks.value = true;
  sidebarEnabled.value = true;
  console.log(landmarkAction.value);
  try {
    const command = landmarkAction.value ? `|= % ${landmarkAction.value}` : '|= %';
    const output = await sendPlanPilotCommand(command);
    if (Array.isArray(output)) {
      landmarks.value = (output as Facet[]).sort((a, b) => {
        if (a.timestep === 0 && b.timestep !== 0) return 1;
        if (a.timestep !== 0 && b.timestep === 0) return -1;
        return a.timestep - b.timestep;
      });
    } else {
      console.warn('Unexpected output format for landmarks:', output);
    }
  } catch (error) {
    console.error('Error: ', error);
  } finally {
    loadingLandmarks.value = false;
  }
};

// Load test data and transform it to facets
onMounted(() => {
  //facets.value = transformToFacets(testData);
  //solutions.value = testDataSolution as Solution[];
  //viewMode.value = 'solutions';
});
</script>

<style scoped>
.layout {
  display: flex;
  flex-direction: row;
}

.main-content {
  padding: 1rem;
  flex: 1;
  transition: margin 0.3s ease;
}

.input-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}

.input-fields .button {
  align-self: flex-end;
}

.button-input {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
}

.button-input .button {
  align-self: flex-end;
}

.count {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
}

.button-input-group {
  display: flex;
  gap: 0.625rem;
  flex-wrap: nowrap;
  flex-shrink: 0;
}
</style>
