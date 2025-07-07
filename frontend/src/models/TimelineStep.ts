import type { TimelineFacet } from "./TimelineFacet";

export interface TimelineStep {
  timestep: number;
  facets: TimelineFacet[];
}