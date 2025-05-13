import type { ActionType } from "./ActionType";
import type { SelectionState } from "./SelectionState";

export interface Facet {
    id: number;
    action: ActionType;
    constant1: string;
    constant2?: string | null;
    timestep: number;
    reduction?: { answer_set: null, facets: null } | null;
    remaining?: { answer_set: null, facets: null } | null;
    selectionState?: SelectionState;
}