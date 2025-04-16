import type { ActionType } from "@/models/ActionType";
import type { Facet } from "@/models/Facet";

export function transformToFacets(facets: any[]): Facet[] {
    return facets.map(facet => ({
        id: facet.id,
        action: facet.action as ActionType,
        constant1: facet.constant1,
        constant2: facet.constant2 ?? null,
        timestep: facet.timestep,
        reduction: facet.reduction ?? null,
        remaining: facet.remaining ?? null,
        selectionState: undefined,
    }));
}