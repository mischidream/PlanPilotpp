import type { Solution } from "./Solution";
import type { TimelineStep } from "./TimelineStep";

export interface ActivatePlanResponse {
  activated: string[];
  errors: { action: string; error: string }[];
  bestPlan: Solution;
  timeline: TimelineStep[];
}
