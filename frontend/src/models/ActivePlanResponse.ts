import type { Facet } from './Facet';
import type { TimelineStep } from './TimelineStep';

export interface ActivatePlanResponse {
  errors: { action: string; error: string }[];
  bestPlan?: Facet[];
  timeline: TimelineStep[];
  facetCount: number;
}
