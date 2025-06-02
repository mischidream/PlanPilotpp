import type { Facet } from '@/models/Facet';
import { computed, type Ref } from 'vue';

export function getAllObjects(facets: Ref<Facet[]>, selectedFacets: Ref<Facet[]>) {
  return computed(() => {
    const objectsSet = new Set<string>();
    const allFacets = [...facets.value, ...selectedFacets.value];
    for (const facet of allFacets) {
      if (facet.constant1) objectsSet.add(facet.constant1);
      if (facet.constant2) objectsSet.add(facet.constant2);
    }
    return Array.from(objectsSet).sort();
  });
}
