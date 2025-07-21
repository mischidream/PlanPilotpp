import type { TimelineFacet } from '@/models/TimelineFacet';
import { TimelineStepType } from '@/models/TimelineStepType';
import { formatFacetOption } from './formatFacetOption';
import type { MultiSelectState } from '@/models/MultiSelectState';
import { SelectionState } from '@/models/SelectionState';

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
  const selectionState = firstFacet?.selectionState as SelectionState;
  if (firstFacet) {
    let state: 'add' | 'remove' | 'none';
    switch (selectionState) {
      case SelectionState.Positive:
        state = 'add';
        break;
      case SelectionState.Negative:
        state = 'remove';
        break;
      case SelectionState.NotSelected:
      default:
        return undefined;
    }

    return [
      {
        option: formatFacetOption(firstFacet),
        state,
      }
    ]
  }
  return undefined;
}
