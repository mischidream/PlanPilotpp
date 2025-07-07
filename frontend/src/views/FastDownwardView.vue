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
    @update:timeline="timeline = $event"
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

// Store
const planStore = usePlanStore();
const instanceFile = computed(() => planStore.instanceFile);
const domainFile = computed(() => planStore.domainFile);
const sasFile = computed(() => planStore.sasFile);
const horizon = ref<number>(planStore.horizon);

const dropdownValues = computed({
  get: () => planStore.dropdownValues,
  set: val => planStore.setDropdownValues(val),
});

const options = computed({
  get: () => planStore.dropdownOptions,
  set: val => planStore.setDropdownOptions(val),
});

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

      /* const formattedOptions = result.bestPlan.facets.map(formatFacetOption);
      const formattedValues = result.bestPlan.facets.map((facet) => [
        {
          option: formatFacetOption(facet),
          state: 'add' as const,
        }
      ]);

      planStore.setDropdownOptions(formattedOptions);
      planStore.setDropdownValues(formattedValues); */
    }
    if (result?.timeline) {
      timeline.value = result.timeline;
      console.log("timeline: ", timeline.value);
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
