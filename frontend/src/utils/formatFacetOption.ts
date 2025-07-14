import type { Facet } from "@/models/Facet";

export function formatFacetOption(facet: Facet): string {
  const { action, constant1, constant2 } = facet;

  if ((action === "stack" || action === "unstack") && constant2) {
    const preposition = action === "stack" ? "on" : "from";
    return `${action} ${constant1} ${preposition} ${constant2}`;
  }

  return `${action} ${constant1}${constant2 ? ` ${constant2}` : ''}`;
}