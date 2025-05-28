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
import { usePlanStore } from '@/stores/planStore';
import type { FastDownwardResponse } from '@/models/FastDownwardResponse';
import SkeletonCount from '@/components/SkeletonCount.vue';

const planStore = usePlanStore();

const instanceFile = computed({
  get: () => planStore.instanceFile,
  set: (val: File | null) => planStore.setInstanceFile(val),
});
const domainFile = computed({
  get: () => planStore.domainFile,
  set: (val: File | null) => planStore.setDomainFile(val),
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
    planStore.setFastDownwardResponse(result.horizon, result.sasFile, result.planFile);
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
    gap: 20px;
}
.input-fields .button{
    align-self: flex-end;
}
.horizon-output {
  margin-top: 10px;
}
</style>