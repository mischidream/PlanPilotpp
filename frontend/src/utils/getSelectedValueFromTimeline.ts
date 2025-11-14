import type { TimelineFacet } from '@/models/TimelineFacet';
import { TimelineStepType } from '@/models/TimelineStepType';
import { formatFacetOption } from './formatFacetOption';
import type { MultiSelectState } from '@/models/MultiSelectState';
import { SelectionState } from '@/models/SelectionState';

export function getSelectedValueFromTimeline(
  facets: TimelineFacet[],
  index: number
): MultiSelectState[] | undefined {
  const validTypes = new Set([
    TimelineStepType.selected,
    TimelineStepType.implied,
    TimelineStepType.plan,
  ]);

  const result: MultiSelectState[] = [];

  const seenOptions = new Set<string>();

  for (const group of facets) {
    if (!validTypes.has(group.type)) continue;

    for (const facet of group.facets ?? []) {
      if (
        facet.selectionState !== SelectionState.Positive &&
        facet.selectionState !== SelectionState.Negative
      )
        continue;

      const option = formatFacetOption(facet);
      if (seenOptions.has(option)) continue;

      const state = facet.selectionState === SelectionState.Positive ? 'add' : 'remove';
      result.push({ option, state });
      seenOptions.add(option);
    }
  }

  return result.length > 0 ? result : undefined;
}
