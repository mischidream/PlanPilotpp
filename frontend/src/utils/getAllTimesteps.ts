import type { Facet } from '@/models/Facet';
import { computed, type Ref } from 'vue';

export function getAllTimesteps(facets: Ref<Facet[]>, selectedFacets: Ref<Facet[]>) {
  return computed(() => {
    const timestepSet = new Set<string>();
    const allFacets = [...facets.value, ...selectedFacets.value];
    for (const facet of allFacets) {
      const label = facet.timestep === 0 ? 'sometime' : String(facet.timestep);
      timestepSet.add(label);
    }
    return Array.from(timestepSet).sort((a, b) => {
      if (a === 'sometime') return -1;
      if (b === 'sometime') return 1;
      return Number(a) - Number(b);
    });
  });
}
