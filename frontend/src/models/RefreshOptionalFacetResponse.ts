import type { TimelineFacet } from "./TimelineFacet";

export interface RefreshOptionalFacetResponse {
  refreshedFacet: TimelineFacet;
  facetCount: number;
}