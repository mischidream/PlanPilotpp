<template>
  <div class="main-layout">
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
        <Button label="Start" type="submit" @click="start"></Button>
      </div>

      <div v-if="!loading && facetCount !== undefined" class="text">
        <p>Number of facets to choose from: {{ facetCount }}</p>
        <div class="legend-refresh-container">
          <ColorLegend />
          <div class="tooltip-wrapper">
            <Button
              label="Reload Timeline"
              @click="refresh"
              :disabled="loading || refreshInProgress"
            ></Button>
            <span
              class="tooltip-text"
              v-if="refreshInProgress"
            >
              {{ tooltipText }}
            </span>
          </div>
        </div>
        <p class="text-small">* Preselection is based on the plan we received from fastdownward</p>
      </div>

      <SkeletonFacetRow class="skeleton" v-if="loading" v-for="i in 3" :key="i" viewMode="facets" />
      <DropdownFlow
        v-else
        :timeline="timeline"
        :selected-values="selectedValues"
        @update:commands="payload => handleDropdownFlowChanges(payload)"
        @update:timeline="timeline = $event"
        @update:selectedValues="selectedValues = $event"
        @refresh="handleRefresh"
      />
    </div>
    <LandmarkSidebar
      :landmarks="bestPlan"
      :loadingLandmarks="false"
      :enabled="sidebarEnabled"
      title="Preselected plan from fastdownward"
    />
  </div>
</template>

<script setup lang="ts">
import DropdownFlow from '@/components/DropdownFlow.vue';
import InputField from '@/components/InputField.vue';
import DropdownField from '@/components/DropdownField.vue';
import SkeletonFacetRow from '@/components/SkeletonFacetRow.vue';
import Button from '@/components/Button.vue';
import LandmarkSidebar from '@/components/LandmarkSidebar.vue';
import ColorLegend from '@/components/ColorLegend.vue';

import { EncodingType } from '@/models/EncodingType';
import { TimeStepType } from '@/models/TimeStepType';
import type { TimelineStep } from '@/models/TimelineStep';
import type { MultiSelectState } from '@/models/MultiSelectState';
import type { Facet } from '@/models/Facet';

import {
  activateBestPlan,
  runPlanPilot,
  refreshTimeline,
  refreshTimestep,
  updatePlan,
  checkRefreshStatus,
} from '@/services/apiService';

import { computed, onMounted, ref } from 'vue';
import { usePlanModificationStore } from '@/stores/planModificationStore';
import { bindWatch } from '@/utils/bindWatch';
import { getSelectedValueFromTimeline } from '@/utils/getSelectedValueFromTimeline';
import { updateOptionalFacet } from '@/utils/updateOptionalFacet';

// Store
const store = usePlanModificationStore();

// Files from startStore
const instanceFile = computed(() => store.currentInstanceFile);
const domainFile = computed(() => store.currentDomainFile);
const sasFile = computed(() => store.currentSas);
const planFile = computed(() => store.currentPlan);

// Horizon: start with minHorizon, user can overwrite it
const horizon = ref<number>(store.minHorizon);

const selectedValues = ref<(MultiSelectState[] | null)[]>([]);
const facetCount = ref<number | null>(store.facetCount);
const timeline = ref<TimelineStep[]>([]);
const bestPlan = ref<Facet[] | null>(store.bestPlan);

// Planning configuration
const minHorizon = ref<number>(store.minHorizon);
const encoding = ref<EncodingType[]>([EncodingType.exact]);
const timeStep = ref<TimeStepType[]>([TimeStepType.concrete]);

// Last used settings
const lastUsedHorizon = ref<number | null>(null);
const lastUsedEncoding = ref<EncodingType | null>(null);
const lastUsedTimeStep = ref<TimeStepType | null>(null);

// Loading states
const loading = ref(false);
const isFirstRun = ref(true);
const sidebarEnabled = ref(false);
const refreshInProgress = ref(false);
const tooltipText = ref("");

// Sync with store
bindWatch(horizon, store.setHorizon);
bindWatch(encoding, ([val]) => val && store.setEncoding(val));
bindWatch(timeStep, ([val]) => val && store.setTimeStep(val));
bindWatch(timeline, store.setTimeline, { deep: true });
bindWatch(selectedValues, store.setSelectedValues, { deep: true });
bindWatch(facetCount, store.setFacetCount);
bindWatch(bestPlan, store.setBestPlan);
bindWatch(sidebarEnabled, store.setSidebarEnabled);

const handleDropdownFlowChanges = async (payload: {
  commands: string[];
  timestepNumber: number;
}) => {
  loading.value = true;
  const result = await updatePlan(store.pageId, payload.timestepNumber + 1, payload.commands);

  if (result?.timeline) {
    timeline.value = result.timeline;
    selectedValues.value = result.timeline.map(
      (step: TimelineStep, index: number) =>
        getSelectedValueFromTimeline(step.facets, index) ?? null
    );
  }

  if (result?.facetCount !== undefined) {
    facetCount.value = result?.facetCount;
  }

  loading.value = false;
};

const handleRefresh = async (timestepNumber: number) => {
  loading.value = true;

  const result = await refreshTimestep(store.pageId, timestepNumber + 1);
  loading.value = false;
  if (!result) return;

  const { refreshedFacet, facetCount: newFacetCount } = result;

  // Update the optional facet in the reactive timeline
  updateOptionalFacet(timeline.value, timestepNumber, refreshedFacet);

  // Update facet count if available
  if (newFacetCount !== undefined) {
    facetCount.value = newFacetCount;
  }
};

const start = async () => {
  loading.value = true;
  try {
    const horizonChanged = lastUsedHorizon.value !== horizon.value;
    const encodingChanged = lastUsedEncoding.value !== encoding.value[0];
    const timeStepChanged = lastUsedTimeStep.value !== timeStep.value[0];
    let result;
    if (isFirstRun.value || horizonChanged || encodingChanged || timeStepChanged) {
      await runPlanPilot({
        pageId: store.pageId,
        sasFile: sasFile.value ?? '',
        horizon: horizon.value,
        encoding: encoding.value[0],
        abstractTimeStep: timeStep.value[0] !== TimeStepType.concrete,
      });
      isFirstRun.value = false;
      lastUsedHorizon.value = horizon.value;
      lastUsedEncoding.value = encoding.value[0];
      lastUsedTimeStep.value = timeStep.value[0];
    }
    result = await activateBestPlan(store.pageId, planFile.value ?? '');

    sidebarEnabled.value = true;

    if (result?.bestPlan) {
      bestPlan.value = result.bestPlan;
    }
    if (result?.timeline) {
      timeline.value = result.timeline;
      selectedValues.value = timeline.value.map(
        (step, index) => getSelectedValueFromTimeline(step.facets, index) ?? null
      );
    }
    if (result?.facetCount !== undefined) {
      facetCount.value = result?.facetCount;
    }
  } catch (error) {
    console.error('Error running PlanPilot:', error);
  } finally {
    loading.value = false;
  }
};

const refresh = async () => {
  loading.value = true;
  try {
    const result = await refreshTimeline(store.pageId);

    if (!result) return;

    // Update timeline
    if (result.timeline) {
      timeline.value = result.timeline;
      selectedValues.value = result.timeline.map(
        (step, index) => getSelectedValueFromTimeline(step.facets, index) ?? null
      );
    }

    // Update facet count
    if (result.facetCount !== undefined) {
      facetCount.value = result.facetCount;
    }
  } catch (err) {
    console.error('Error refreshing timeline:', err);
  } finally {
    loading.value = false;
  }
};

const pollRefreshStatus = async () => {
  // Skip polling if the page is currently loading
  if (loading.value) return;
  
  const res = await checkRefreshStatus();
  if (!res) return;

  switch (res.status) {
    case "in_progress":
      refreshInProgress.value = true;
      tooltipText.value = "Background refresh still running…";
      break;
    case "non_existent":
      refreshInProgress.value = true; // disable button
      tooltipText.value = "No background task exists";
      break;
    case "done":
      refreshInProgress.value = false;
      tooltipText.value = "";
      break;
    default:
      refreshInProgress.value = false;
      tooltipText.value = "";
  }
};

onMounted(() => {
  pollRefreshStatus();
  setInterval(pollRefreshStatus, 500);
});
</script>

<style scoped>
.main-layout {
  display: flex;
  flex-direction: row;
  gap: 0.5rem;
}

.input-fields {
  padding: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
}

.input-fields .button {
  align-self: flex-end;
}

.text {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.text-small {
  font-size: smaller;
}

.skeleton {
  padding: 1rem;
}

.legend-refresh-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Tooltip wrapper for the button */
.tooltip-wrapper {
  position: relative;
  display: inline-block;
}

/* Reuse existing tooltip style */
.tooltip-text {
  visibility: hidden;
  opacity: 0;
  background-color: var(--black-mute);
  color: var(--white);
  text-align: center;
  border-radius: var(--border-radius);
  padding: 0.25rem 0.5rem;
  position: absolute;
  z-index: 200;
  bottom: 110%;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-size: 0.75rem;
  transition: opacity 0.2s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

/* Make tooltip show */
.tooltip-wrapper:hover .tooltip-text {
  visibility: visible;
  opacity: 1;
}

</style>
