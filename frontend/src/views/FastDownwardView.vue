<template>
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
  <SkeletonFacetRow
    class="skeleton"
    v-if="loading"
    v-for="i in 3"
    :key="i"
    viewMode="facets"
  />
  <DropdownFlow
    v-else
    :timeline="timeline"
    :selected-values="selectedValues"
    @update:timeline="timeline = $event"
    @update:selectedValues="selectedValues = $event"
  />
</template>

<script setup lang="ts">
import DropdownFlow from '@/components/DropdownFlow.vue';
import InputField from '@/components/InputField.vue';
import DropdownField from '@/components/DropdownField.vue';
import SkeletonFacetRow from '@/components/SkeletonFacetRow.vue';
import Button from '@/components/Button.vue';
import { EncodingType } from '@/models/EncodingType';
import { TimeStepType } from '@/models/TimeStepType';
import { activateBestPlan, runPlanPilot } from '@/services/apiService';
import { usePlanStore } from '@/stores/planStore';
import { bindWatch } from '@/utils/bindWatch';

import { computed, ref } from 'vue';
import type { Facet } from '@/models/Facet';
import type { TimelineStep } from '@/models/TimelineStep';
import type { MultiSelectState } from '@/models/MultiSelectState';
import type { TimelineFacet } from '@/models/TimelineFacet';
import { TimelineStepType } from '@/models/TimelineStepType';

// Store
const planStore = usePlanStore();
const instanceFile = computed(() => planStore.instanceFile);
const domainFile = computed(() => planStore.domainFile);
const sasFile = computed(() => planStore.sasFile);
const horizon = ref<number>(planStore.horizon);

const selectedValues = ref<((string | MultiSelectState)[] | null)[]>([]);

const timeline = ref<TimelineStep[]>([]);

// Planning configuration
const minHorizon = ref(horizon.value);
const encoding = ref<EncodingType[]>([EncodingType.exact]);
const timeStep = ref<TimeStepType[]>([TimeStepType.concrete]);

// Last used settings
const lastUsedHorizon = ref<number | null>(null);
const lastUsedEncoding = ref<EncodingType | null>(null);
const lastUsedTimeStep = ref<TimeStepType | null>(null);

// Loading states
const loading = ref(false);

const isFirstRun = ref(true);

// Sync with store
bindWatch(horizon, planStore.setHorizon);
bindWatch(minHorizon, planStore.setMinHorizon);
bindWatch(encoding, ([val]) => val && planStore.setEncoding(val));
bindWatch(timeStep, ([val]) => val && planStore.setTimeStep(val));

const start = async () => {
  loading.value = true;
  try {
    const horizonChanged = lastUsedHorizon.value !== horizon.value;
    const encodingChanged = lastUsedEncoding.value !== encoding.value[0];
    const timeStepChanged = lastUsedTimeStep.value !== timeStep.value[0];
    let result;
    if (isFirstRun.value || horizonChanged || encodingChanged || timeStepChanged) {
      await runPlanPilot({
        sasFile: sasFile.value,
        horizon: horizon.value,
        encoding: encoding.value[0],
        abstractTimeStep: timeStep.value[0] !== TimeStepType.concrete,
      });
      isFirstRun.value = false;
      lastUsedHorizon.value = horizon.value;
      lastUsedEncoding.value = encoding.value[0];
      lastUsedTimeStep.value = timeStep.value[0];
    }
    result = await activateBestPlan(planStore.planFile);
    if (result?.bestPlan) {
      planStore.setBestPlan(result.bestPlan);
    }
    if (result?.timeline) {
      timeline.value = result.timeline;
      console.log("timeline: ", timeline.value);
      selectedValues.value = timeline.value.map((step, index) =>
        getSelectedValue(step.facets, index) ?? null
      );
      console.log("has selected stuff");
      console.log("pre selectedValues: ", selectedValues.value);
    }
  } catch (error) {
    console.error('Error running PlanPilot:', error);
  } finally {
    loading.value = false;
  }
}

function formatFacetOption(facet: Facet): string {
  const { action, constant1, constant2 } = facet;

  if ((action === "stack" || action === "unstack") && constant2) {
    const preposition = action === "stack" ? "on" : "from";
    return `${action} ${constant1} ${preposition} ${constant2}`;
  }

  return `${action} ${constant1}${constant2 ? ` ${constant2}` : ''}`;
}

function getSelectedValue(value: TimelineFacet[], index: number): (string | MultiSelectState)[] | undefined {
  const selected = value.find(v => 
    v.type === TimelineStepType.plan || v.type === TimelineStepType.implied
  );
  const firstFacet = selected?.facets?.[0];
  if (firstFacet) {
    return [{
      option: formatFacetOption(firstFacet),
      state: 'add',
    }];
  }

  return undefined;
}

</script>

<style scoped>
.input-fields {
  padding: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin-bottom: 1.25rem;
}

.input-fields .button {
  align-self: flex-end;
}

.skeleton {
  padding: 1rem;
}

</style>
