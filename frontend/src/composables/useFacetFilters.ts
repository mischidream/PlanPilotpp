// composables/useFacetFilters.ts
import { computed, type Ref } from 'vue';
import type { Facet } from '@/models/Facet';
import { SelectionState } from '@/models/SelectionState';
import { ActionType } from '@/models/ActionType';

export function useFacetFilters(
  facets: Ref<Facet[]>,
  selectedFacets: Ref<Facet[]>,
  selectedFacetState: Ref<SelectionState[]>,
  selectedActionType: Ref<ActionType[]>,
  selectedObjects: Ref<string[]>,
  selectedTimesteps: Ref<string[]>
) {
  const filteredFacets = computed<Facet[]>(() => {
    const matches = (facet: Facet): boolean => {
      const matchState =
        selectedFacetState.value.length === 0 ||
        selectedFacetState.value.includes(facet.selectionState as SelectionState);
      const matchAction =
        selectedActionType.value.length === 0 || selectedActionType.value.includes(facet.action);
      const objects = [facet.constant1, facet.constant2].filter(Boolean) as string[];
      const matchObjects =
        selectedObjects.value.length === 0 || objects.some(o => selectedObjects.value.includes(o));
      const timestep = facet.timestep === 0 ? 'sometime' : String(facet.timestep);
      const matchTime =
        selectedTimesteps.value.length === 0 || selectedTimesteps.value.includes(timestep);

      return matchState && matchAction && matchObjects && matchTime;
    };

    const filteredSelected = selectedFacets.value.filter(matches);
    const selectedIds = new Set(filteredSelected.map(f => f.id));
    const filteredOthers = facets.value.filter(f => !selectedIds.has(f.id)).filter(matches);
    return [...filteredSelected, ...filteredOthers];
  });

  return { filteredFacets };
}
