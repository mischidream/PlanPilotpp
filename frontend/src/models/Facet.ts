import type { ActionType } from "./ActionType";
import type { SelectionState } from "./SelectionState";

export interface Facet {
    id: number;
    action: ActionType;
    constant1: string;
    constant2?: string | null;
    timestep: number;
    reduction?: number | null;
    remaining?: number | null;
    selectionState?: SelectionState;
}