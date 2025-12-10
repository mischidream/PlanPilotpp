import type { Facet } from '@/models/Facet';
import type { TimelineStep } from '@/models/TimelineStep';
import type { MultiSelectState } from '@/models/MultiSelectState';
import { EncodingType } from '@/models/EncodingType';
import { TimeStepType } from '@/models/TimeStepType';
import { defineStore } from 'pinia';
import { v4 as uuidv4 } from 'uuid';
import { useStartStore } from './startStore';
import { toRaw } from 'vue';

export const usePlanModificationStore = defineStore('planModification', {
  state: () => ({
    pageId: uuidv4(),

    // Planning config
    horizon: 0,
    encoding: EncodingType.exact as EncodingType,
    timeStep: TimeStepType.concrete as TimeStepType,

    // Derived from backend
    bestPlan: null as Facet[] | null,
    timeline: [] as TimelineStep[],
    selectedValues: [] as (MultiSelectState[] | null)[],
    facetCount: null as number | null,

    // Page UI state
    sidebarEnabled: false
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
    setHorizon(val: number) { this.horizon = val; },
    setEncoding(val: EncodingType) { this.encoding = val; },
    setTimeStep(val: TimeStepType) { this.timeStep = val; },
    setBestPlan(val: Facet[] | null) { this.bestPlan = val; },
    setTimeline(val: TimelineStep[]) { this.timeline = structuredClone(toRaw(val)); },
    setSelectedValues(val: (MultiSelectState[] | null)[]) { this.selectedValues = structuredClone(toRaw(val)); },
    setFacetCount(val: number | null) { this.facetCount = val; },
    setSidebarEnabled(val: boolean) { this.sidebarEnabled = val; },

    reset() {
      const id = this.pageId;
      this.$reset();
      this.pageId = id;
    }
  },
  persist: true,
});
