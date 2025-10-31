import type { TimelineFacet } from "@/models/TimelineFacet";
import type { TimelineStep } from "@/models/TimelineStep";

export function updateOptionalFacet(
  timeline: TimelineStep[],
  timestepNumber: number,
  refreshedFacet: TimelineFacet
) {
  const step = timeline[timestepNumber];
  if (!step) return;

  const index = step.facets.findIndex(f => f.type === refreshedFacet.type);

  if (index !== -1) {
    // Replace existing optional facet
    step.facets[index] = refreshedFacet;
  } else {
    // Add new optional facet if it doesn't exist
    step.facets.push(refreshedFacet);
  }
}
