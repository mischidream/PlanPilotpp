<template>
    <div class="input-fields">
        <InputField label="Problem file:" v-model="instanceFile" type="file" accept=".pddl" />
        <InputField label="Domain file:" v-model="domainFile" type="file" accept=".pddl" />
        <Button label="Start" type="submit" @click="submitFiles"></Button>
    </div>
    <div v-if="response" class="horizon-output">
      <p><strong>Horizon:</strong> {{ response.horizon }}</p>
    </div>
</template>

<script setup lang="ts">
import InputField from '@/components/InputField.vue';
import Button from '@/components/Button.vue';
import { ref } from 'vue';
import { getSasPlan } from '@/services/apiService';
import type { FastDownwardResponse } from '@/models/FastDownwardResponse';
const instanceFile = ref<File | null>(null);
const domainFile = ref<File | null>(null);
const response = ref<FastDownwardResponse | null>(null);

async function submitFiles() {
  if (!instanceFile.value || !domainFile.value) {
    alert('Please select both files.');
    return;
  }

  try {
    const result = await getSasPlan(instanceFile.value, domainFile.value);
    response.value = result ?? null;
    console.log(response.value?.horizon);
    console.log(response.value?.sasFile);
  } catch (error) {
    alert((error as Error).message);
  }
}

</script>

<style scoped>
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