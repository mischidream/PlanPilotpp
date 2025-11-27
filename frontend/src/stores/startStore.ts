import { defineStore } from 'pinia';

export const useStartStore = defineStore('start', {
  state: () => ({
    // Shared files from Start page
    instanceFile: null as File | null,
    domainFile: null as File | null,
    sasFile: null as string | null,
    planFile: null as string | null,

    // Horizon coming from Start (min horizon for all pages)
    minHorizon: 0,
  }),
  actions: {
    setInstanceFile(file: File | null) {
      this.instanceFile = file;
    },
    setDomainFile(file: File | null) {
      this.domainFile = file;
    },
    setStartResponse(sasFile: string, planFile: string, minHorizon: number) {
      this.sasFile = sasFile;
      this.planFile = planFile;
      this.minHorizon = minHorizon;
    }
  },
  persist: true,
});
