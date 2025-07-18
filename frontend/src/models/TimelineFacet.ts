import type { Facet } from './Facet';
import type { TimelineStepType } from './TimelineStepType';

export interface TimelineFacet {
  type: TimelineStepType;
  facets: Facet[];
  causedBy?: Record<string, string>;
}
