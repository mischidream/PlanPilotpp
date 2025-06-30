import type { Solution } from "./Solution";

export interface ActivatePlanResponse {
  activated: string[];
  errors: { action: string; error: string }[];
  bestPlan: Solution;
}
