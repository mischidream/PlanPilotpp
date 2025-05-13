import type { Facet } from "./Facet";

export interface AnswerSet {
  [solutionLabel: string]: Facet[];
}
