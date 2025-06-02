import type { ActionType } from "./ActionType";
import type { SelectionState } from "./SelectionState";

export interface Facet {
    id: string;
    action: ActionType;
    constant1: string;
    constant2?: string | null;
    timestep: number;
    reduction?: { solution: { positive: number | null; negative: number | null } | null, facets: { positive: number | null; negative: number | null } | null } | null;
    remaining?: { solution: { positive: number | null; negative: number | null } | null, facets: { positive: number | null; negative: number | null } | null } | null;
    selectionState?: SelectionState;
}