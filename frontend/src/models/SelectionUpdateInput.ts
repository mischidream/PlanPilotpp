import type { Facet } from './Facet';
import type { SelectionState } from './SelectionState';

export interface SelectionUpdateInput {
  facet: Facet;
  newState: SelectionState;
}
