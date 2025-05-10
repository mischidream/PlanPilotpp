import { defineStore } from 'pinia';

export const usePlanStore = defineStore('plan', {
  state: () => ({
    instanceFile: null as File | null,
    domainFile: null as File | null,
    horizon: 0,
    sasFile: '',
    planFile: '',
  }),

  actions: {
    setFiles(instanceFile: File | null, domainFile: File | null) {
      this.instanceFile = instanceFile;
      this.domainFile = domainFile;
    },
    setInstanceFile(instanceFile: File | null){
      this.instanceFile = instanceFile;
    },
    setDomainFile(domainFile: File | null){
      this.domainFile = domainFile;
    },
    setFastDownwardResponse(horizon: number, sasFile: string, planFile: string) {
      this.horizon = horizon;
      this.sasFile = sasFile;
      this.planFile = planFile;
    },
  },
});
