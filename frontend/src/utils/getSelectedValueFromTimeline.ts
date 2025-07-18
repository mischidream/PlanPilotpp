import type { TimelineFacet } from '@/models/TimelineFacet';
import { TimelineStepType } from '@/models/TimelineStepType';
import { formatFacetOption } from './formatFacetOption';
import type { MultiSelectState } from '@/models/MultiSelectState';

export function getSelectedValueFromTimeline(
  value: TimelineFacet[],
  index: number
): MultiSelectState[] | undefined {
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
