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
  <SkeletonFacetRow class="skeleton" v-if="loading" v-for="i in 3" :key="i" viewMode="facets" />
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
import {
  activateBestPlan,
  runPlanPilot,
  sendPlanPilotCommand,
  updatePlan,
} from '@/services/apiService';
import { usePlanStore } from '@/stores/planStore';
import { bindWatch } from '@/utils/bindWatch';

import { computed, ref, watch } from 'vue';
import type { Facet } from '@/models/Facet';
import type { TimelineStep } from '@/models/TimelineStep';
import type { MultiSelectState } from '@/models/MultiSelectState';
import type { TimelineFacet } from '@/models/TimelineFacet';
import { TimelineStepType } from '@/models/TimelineStepType';
import { formatFacetOption } from '@/utils/formatFacetOption';

// Store
const planStore = usePlanStore();
const instanceFile = computed(() => planStore.instanceFile);
const domainFile = computed(() => planStore.domainFile);
const sasFile = computed(() => planStore.sasFile);
const horizon = ref<number>(planStore.horizon);

const selectedValues = ref<(MultiSelectState[] | null)[]>([]);

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
let isUpdating = ref(false);

// Sync with store
bindWatch(horizon, planStore.setHorizon);
bindWatch(minHorizon, planStore.setMinHorizon);
bindWatch(encoding, ([val]) => val && planStore.setEncoding(val));
bindWatch(timeStep, ([val]) => val && planStore.setTimeStep(val));

watch(
  selectedValues,
  async (newVal, oldVal) => {
    if (isUpdating.value) {
      isUpdating.value = false;
      return;
    }

    await handleSelectedValuesChange(newVal, oldVal);
  },
  { deep: true }
);

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
      console.log('timeline: ', timeline.value);
      selectedValues.value = timeline.value.map(
        (step, index) => getSelectedValue(step.facets, index) ?? null
      );
      console.log('pre selectedValues: ', selectedValues.value);
    }
  } catch (error) {
    console.error('Error running PlanPilot:', error);
  } finally {
    loading.value = false;
  }
};

function getSelectedValue(value: TimelineFacet[], index: number): MultiSelectState[] | undefined {
  const selected = value.find(
    v =>
      v.type === TimelineStepType.plan ||
      v.type === TimelineStepType.implied ||
      v.type === TimelineStepType.selected
  );
  const firstFacet = selected?.facets?.[0];
  if (firstFacet) {
    return [
      {
        option: formatFacetOption(firstFacet),
        state: 'add',
      },
    ];
  }

  return undefined;
}

async function handleSelectedValuesChange(
  newVal: typeof selectedValues.value,
  oldVal: typeof selectedValues.value
) {
  if (!oldVal || oldVal.every(v => v == null)) {
    return;
  }
  loading.value = true;
  try {
    console.log('newValue, oldValue: ', newVal, oldVal);
    const batchedCommands: string[] = [];
    let changedTimestep: number = -1;
    let result;

    const isOptionObject = (val: any): val is { option: string; state: 'add' | 'remove' } =>
      typeof val === 'object' && val !== null && 'option' in val && 'state' in val;

    for (let i = 0; i < newVal.length; i++) {
      const newRaw = newVal[i]?.[0];
      const oldRaw = oldVal?.[i]?.[0];

      const newSelection = isOptionObject(newRaw) ? newRaw : null;
      const oldSelection = isOptionObject(oldRaw) ? oldRaw : null;

      const newOpt = newSelection?.option ?? '';
      const oldOpt = oldSelection?.option ?? '';
      const newState = newSelection?.state;

      const step = timeline.value[i];
      if (!step) continue;

      const hasEmptyType = step.facets.some(f => f.type === 'empty');

      function findFacet(option: string): Facet | undefined {
        const searchFacets = hasEmptyType
          ? step.facets.flatMap(f => f.facets)
          : step.facets
              .filter(f => f.type === 'plan' || f.type === 'selected')
              .flatMap(f => f.facets);
        return searchFacets.find(facet => formatFacetOption(facet) === option);
      }

      if (changedTimestep === -1 && (newOpt !== oldOpt || (!newSelection && oldSelection))) {
        changedTimestep = i + 1;
      }

      if (!newSelection && oldSelection) {
        const matchingFacet = findFacet(oldOpt);
        console.log('facet deleted: ', matchingFacet);
        if (matchingFacet) {
          batchedCommands.push(`- ${matchingFacet.id}`);
        }
        continue;
      }

      if (newOpt !== oldOpt) {
        const matchingFacet = findFacet(newOpt);
        console.log('new option is different to old one: ', matchingFacet);
        if (!matchingFacet) continue;

        const isPlanStep = step.facets.some(f => f.type === 'plan');

        if (isPlanStep) {
          for (let j = i; j < timeline.value.length; j++) {
            const futureStep = timeline.value[j];
            futureStep.facets
              .filter(f => f.type === 'plan')
              .flatMap(f => f.facets)
              .forEach(facet => {
                batchedCommands.push(`- ${facet.id}`);
              });
          }

          const addCmd = newState === 'remove' ? `+ ~${matchingFacet.id}` : `+ ${matchingFacet.id}`;
          batchedCommands.push(addCmd);
        } else {
          const cmd = newState === 'remove' ? `+ ~${matchingFacet.id}` : `+ ${matchingFacet.id}`;
          result = await updatePlan(changedTimestep, cmd);
        }
      }
    }

    if (batchedCommands.length && changedTimestep > -1) {
      console.log('batched commands: ', batchedCommands);
      result = await updatePlan(changedTimestep, batchedCommands);
    }

    console.log('result in watch: ', result);
    if (result?.timeline) {
      timeline.value = result.timeline;
      console.log('timeline: ', timeline.value);
      isUpdating.value = true;
      selectedValues.value = result.timeline.map(
        (step, index) => getSelectedValue(step.facets, index) ?? null
      );
      console.log('updated selectedValues: ', selectedValues.value);
    }
  } finally {
    loading.value = false;
  }
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
