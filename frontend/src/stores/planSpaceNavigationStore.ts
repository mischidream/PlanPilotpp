import type { Facet } from '@/models/Facet';
import type { Solution } from '@/models/Solution';
import type { SelectionState } from '@/models/SelectionState';
import type { ActionType } from '@/models/ActionType';
import type { TimelineStep } from '@/models/TimelineStep';
import type { MultiSelectState } from '@/models/MultiSelectState';
import { EncodingType } from '@/models/EncodingType';
import { TimeStepType } from '@/models/TimeStepType';
import { defineStore } from 'pinia';
import { v4 as uuidv4 } from 'uuid';
import { useStartStore } from './startStore';
import { toRaw } from 'vue';

export const usePlanSpaceNavigationStore = defineStore('planSpaceNavigation', {
  state: () => ({
    pageId: uuidv4(),

    // Planning config
    horizon: 0,
    encoding: EncodingType.exact as EncodingType,
    timeStep: TimeStepType.concrete as TimeStepType,

    // PlanPilot data
    facets: [] as Facet[],
    landmarks: [] as Facet[],
    solutions: [] as Solution[],
    selectedFacetState: [] as SelectionState[],
    selectedActionType: [] as ActionType[],
    selectedObjects: [] as string[],
    selectedTimesteps: [] as string[],
    selectedSolution: null as Solution | null,
    bestPlan: null as Facet[] | null,
    timeline: [] as TimelineStep[],
    selectedValues: [] as (MultiSelectState[] | null)[],
    facetCount: null as number | null,

    // Page UI state
    viewMode: 'facets' as 'facets' | 'solutions' | 'query',
    sidebarEnabled: false,
  }),

  getters: {
    global: () => useStartStore(),

    currentInstanceFile: () => useStartStore().instanceFile,
    currentDomainFile: () => useStartStore().domainFile,
    currentSas: () => useStartStore().sasFile,
    currentPlan: () => useStartStore().planFile,
    minHorizon: () => useStartStore().minHorizon,
  },

  actions: {
        // Planning config setters
    setHorizon(val: number) { this.horizon = val; },
    setEncoding(val: EncodingType) { this.encoding = val; },
    setTimeStep(val: TimeStepType) { this.timeStep = val; },

    // Backend data setters
    setFacets(val: Facet[]) { this.facets = val; },
    setLandmarks(val: Facet[]) { this.landmarks = val; },
    setSolutions(val: Solution[]) { this.solutions = val; },
    setBestPlan(val: Facet[] | null) { this.bestPlan = val; },
    setFacetCount(val: number | null) { this.facetCount = val; },
    setTimeline(val: TimelineStep[]) { this.timeline = structuredClone(toRaw(val)); },
    setSelectedValues(val: (MultiSelectState[] | null)[]) {
      this.selectedValues = structuredClone(toRaw(val));
    },

    // User selection setters
    setViewMode(val: 'facets' | 'solutions' | 'query') { this.viewMode = val; },
    setSelectedFacetState(val: SelectionState[]) { this.selectedFacetState = val; },
    setSelectedActionType(val: ActionType[]) { this.selectedActionType = val; },
    setSelectedObjects(val: string[]) { this.selectedObjects = val; },
    setSelectedTimesteps(val: string[]) { this.selectedTimesteps = val; },
    setSelectedSolution(val: Solution | null) { this.selectedSolution = val; },

    // UI setters
    setSidebarEnabled(val: boolean) { this.sidebarEnabled = val; },

    reset() {
      const oldId = this.pageId;
      this.$reset();
      this.pageId = oldId; // Keep session across refresh
    }
  },
});
