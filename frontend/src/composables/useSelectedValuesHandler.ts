import type { Facet } from '@/models/Facet';
import type { MultiSelectState } from '@/models/MultiSelectState';
import type { TimelineFacet } from '@/models/TimelineFacet';
import type { TimelineStep } from '@/models/TimelineStep';
import { TimelineStepType } from '@/models/TimelineStepType';
import { updatePlan } from '@/services/apiService';
import { formatFacetOption } from '@/utils/formatFacetOption';
import { getSelectedValueFromTimeline } from '@/utils/getSelectedValueFromTimeline';
import type { Ref } from 'vue';

export async function handleSelectedValuesChange(
  newVal: (MultiSelectState[] | null)[],
  oldVal: (MultiSelectState[] | null)[],
  selectedValues: Ref<(MultiSelectState[] | null)[]>,
  timeline: Ref<TimelineStep[]>,
  loading: Ref<boolean>,
  isUpdating: Ref<boolean>
): Promise<void> {
  if (!oldVal || oldVal.every(v => v == null)) return;

  loading.value = true;

  try {
    const batchedCommands: string[] = [];
    let changedTimestep: number = -1;
    let result;

    for (let i = 0; i < newVal.length; i++) {
      const newRaw = newVal[i]?.[0] ?? null;
      const oldRaw = oldVal?.[i]?.[0] ?? null;

      const newSelection = isMultiSelectState(newRaw) ? newRaw : null;
      const oldSelection = isMultiSelectState(oldRaw) ? oldRaw : null;

      const newOpt = newSelection?.option?.toString() ?? '';
      const oldOpt = oldSelection?.option?.toString() ?? '';
      const newState = newSelection?.state;

      const step = timeline.value[i];
      if (!step) continue;

      if (changedTimestep === -1 && (newOpt !== oldOpt || (!newSelection && oldSelection))) {
        changedTimestep = i + 1;
      }

      // CASE 1: Deletion
      if (!newSelection && oldSelection) {
        const matchingFacet = findMatchingFacet(step, oldOpt);
        if (matchingFacet) batchedCommands.push(`- ${matchingFacet.id}`);
        continue;
      }

      // CASE 2: Value changed
      if (newOpt !== oldOpt) {
        const matchingFacet = findMatchingFacet(step, newOpt);
        if (!matchingFacet) continue;

        const isPlanStep: boolean = step.facets.some(f => f.type === TimelineStepType.plan);
        if (isPlanStep) {
          batchedCommands.push(
            newState === 'remove' ? `+ ~${matchingFacet.id}` : `+ ${matchingFacet.id}`
          );
        } else {
          const cmd: string =
            newState === 'remove' ? `+ ~${matchingFacet.id}` : `+ ${matchingFacet.id}`;
          console.log("changed timestep, command: ", changedTimestep, cmd);
          result = await updatePlan(changedTimestep, cmd);
        }
      }
    }

    if (batchedCommands.length && changedTimestep > -1) {
      console.log("changed timestep, batched commands: ", changedTimestep, batchedCommands);
      result = await updatePlan(changedTimestep, batchedCommands);
    }

    if (result?.timeline) {
      timeline.value = result.timeline;
      console.log('timeline: ', timeline.value);
      isUpdating.value = true;
      selectedValues.value = result.timeline.map(
        (step: TimelineStep, index: number) =>
          getSelectedValueFromTimeline(step.facets, index) ?? null
      );
    }
  } finally {
    loading.value = false;
  }
}

function isMultiSelectState(val: any): val is MultiSelectState {
  return typeof val === 'object' && val !== null && 'option' in val && 'state' in val;
}

function findMatchingFacet(step: TimelineStep, option: string): Facet | undefined {
  const hasEmptyType: boolean = step.facets.some(
    (f: TimelineFacet) => f.type === TimelineStepType.empty
  );

  const searchFacets: Facet[] = hasEmptyType
    ? step.facets.flatMap(f => f.facets || [])
    : step.facets
        .filter(f => f.type === TimelineStepType.plan || f.type === TimelineStepType.selected)
        .flatMap(f => f.facets || []);

  return searchFacets.find((facet: Facet) => formatFacetOption(facet) === option);
}

function collectPlanRemovals(timeline: TimelineStep[], startIndex: number): string[] {
  const commands: string[] = [];
  for (let j = startIndex; j < timeline.length; j++) {
    const futureStep: TimelineStep = timeline[j];
    futureStep.facets
      .filter(f => f.type === 'plan')
      .flatMap(f => f.facets || [])
      .forEach(facet => {
        commands.push(`- ${facet.id}`);
      });
  }
  return commands;
}
