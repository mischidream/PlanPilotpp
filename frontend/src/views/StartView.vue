<template>
  <div class="layout">
    <div class="input-fields">
      <InputField label="Problem file:" v-model="instanceFile" type="file" accept=".pddl" />
      <InputField label="Domain file:" v-model="domainFile" type="file" accept=".pddl" />
      <Button label="Start" type="submit" @click="submitFiles"></Button>
    </div>
    <div v-if="loading" class="horizon-output">
      <SkeletonCount></SkeletonCount>
    </div>
    <div v-else-if="response" class="horizon-output">
      <p><strong>Horizon:</strong> {{ response.horizon }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import InputField from '@/components/InputField.vue';
import Button from '@/components/Button.vue';
import { computed, ref } from 'vue';
import { getSasPlan } from '@/services/apiService';
import { useStartStore } from '@/stores/startStore';
import type { FastDownwardResponse } from '@/models/FastDownwardResponse';
import SkeletonCount from '@/components/SkeletonCount.vue';
import { usePlanModificationStore } from '@/stores/planModificationStore';
import { usePlanSpaceNavigationStore } from '@/stores/planSpaceNavigationStore';

const startStore = useStartStore();
const planModificationStore = usePlanModificationStore();
const planSpaceNavigationStore = usePlanSpaceNavigationStore();

const instanceFile = computed({
  get: () => startStore.instanceFile,
  set: v => startStore.setInstanceFile(v),
});

const domainFile = computed({
  get: () => startStore.domainFile,
  set: v => startStore.setDomainFile(v),
});

const loading = ref(false);

// Local response state to display
const response = ref<FastDownwardResponse | null>(null);

async function submitFiles() {
  if (!instanceFile.value || !domainFile.value) {
    alert('Please select both files.');
    return;
  }

  loading.value = true;
  try {
    const result = await getSasPlan({
      problemFile: instanceFile.value,
      domainFile: domainFile.value,
    });
    if (!result) {
      throw new Error('No response received from planner.');
    }
    response.value = result;
    startStore.setStartResponse(result.sasFile, result.planFile, result.horizon);
    planModificationStore.reset();
    planSpaceNavigationStore.reset();
  } catch (error) {
    alert((error as Error).message);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.layout {
  padding: 1rem;
}

.input-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
}
.input-fields .button {
  align-self: flex-end;
}
.horizon-output {
  margin-top: 0.625rem;
}
</style>
