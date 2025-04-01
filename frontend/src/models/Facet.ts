import type { ActionType } from "./ActionType";

export interface Facet {
    id: number;
    action: ActionType;
    constant1: string;
    constant2?: string | null;
    timestep: number;
    reduction?: number | null;
    remaining?: number | null;
  }