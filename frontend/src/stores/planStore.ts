import type { ActionType } from '@/models/ActionType';
import type { Solution } from '@/models/Solution';
import { EncodingType } from '@/models/EncodingType';
import type { Facet } from '@/models/Facet';
import type { SelectionState } from '@/models/SelectionState';
import { TimeStepType } from '@/models/TimeStepType';
import { defineStore } from 'pinia';

export const usePlanStore = defineStore('plan', {
  state: () => ({
    instanceFile: null as File | null,
    domainFile: null as File | null,
    sasFile: '',
    planFile: '',
    horizon: 0,
    minHorizon: 0,
    encoding: EncodingType.exact as EncodingType,
    timeStep: TimeStepType.concrete as TimeStepType,
    facets: [] as Facet[],
    landmarks: [] as Facet[],
    solutions: [] as Solution[],
    viewMode: 'facets' as 'facets' | 'solutions' | 'query',
    selectedFacetState: [] as SelectionState[],
    selectedActionType: [] as ActionType[],
    selectedObjects: [] as string[],
    selectedTimesteps: [] as string[],
    selectedSolution: null as Solution | null,
  }),

  actions: {
    setFiles(instanceFile: File | null, domainFile: File | null) {
      this.instanceFile = instanceFile;
      this.domainFile = domainFile;
    },
    setInstanceFile(instanceFile: File | null) {
      this.instanceFile = instanceFile;
    },
    setDomainFile(domainFile: File | null) {
      this.domainFile = domainFile;
    },
    setFastDownwardResponse(horizon: number, sasFile: string, planFile: string) {
      this.horizon = horizon;
      this.sasFile = sasFile;
      this.planFile = planFile;
    },
    setHorizon(horizon: number) {
      this.horizon = horizon;
    },
    setMinHorizon(minHorizon: number) {
      this.minHorizon = minHorizon;
    },
    setEncoding(encoding: EncodingType) {
      this.encoding = encoding;
    },
    setTimeStep(timeStep: TimeStepType) {
      this.timeStep = timeStep;
    },
    setFacets(facets: Facet[]) {
      this.facets = facets;
    },
    setLandmarks(landmarks: Facet[]) {
      this.landmarks = landmarks;
    },
    setSolutions(solutions: Solution[]) {
      this.solutions = solutions;
    },
    setViewMode(mode: 'facets' | 'solutions' | 'query') {
      this.viewMode = mode;
    },
    setSelectedFacetState(val: SelectionState[]) {
      this.selectedFacetState = val;
    },
    setSelectedActionType(val: ActionType[]) {
      this.selectedActionType = val;
    },
    setSelectedObjects(val: string[]) {
      this.selectedObjects = val;
    },
    setSelectedTimesteps(val: string[]) {
      this.selectedTimesteps = val;
    },
    setSelectedSolution(val: Solution) {
      this.selectedSolution = val;
    },
  },
  persist: true,
});
