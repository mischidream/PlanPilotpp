<template>
  <div class="layout">
    <div class="input-fields">
      <InputField
        label="Concrete Problem file:"
        v-model="concreteProblemFile"
        type="file"
        accept=".pddl"
      />
      <InputField
        label="Concrete Domain file:"
        v-model="concreteDomainFile"
        type="file"
        accept=".pddl"
      />
      <InputField
        label="Abstract Problem file:"
        v-model="abstractProblemFile"
        type="file"
        accept=".pddl"
      />
      <InputField
        label="Abstract Domain file:"
        v-model="abstractDomainFile"
        type="file"
        accept=".pddl"
      />
      <InputField
        label="Horizon:"
        v-model="horizon"
        type="number"
        :placeholder="minHorizon?.toString()"
      />
      <DropdownField
        label="Encoding:"
        :options="Object.values(EncodingType)"
        v-model="encoding"
        :isMultiple="false"
      />
      <DropdownField
        label="Time Steps:"
        :options="Object.values(TimeStepType)"
        v-model="timeStep"
        :isMultiple="false"
      />
      <Button label="Start" type="submit" @click="start"></Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import InputField from '@/components/InputField.vue';
import Button from '@/components/Button.vue';
import DropdownField from '@/components/DropdownField.vue';
import { ref } from 'vue';
import { EncodingType } from '@/models/EncodingType';
import { TimeStepType } from '@/models/TimeStepType';
import { getConcreteFromAbstractPlan } from '@/services/apiService';

const abstractProblemFile = ref<File | null>(null);
const abstractDomainFile = ref<File | null>(null);
const concreteProblemFile = ref<File | null>(null);
const concreteDomainFile = ref<File | null>(null);

const horizon = ref<number>(1);
const encoding = ref<EncodingType[]>([EncodingType.exact]);
const timeStep = ref<TimeStepType[]>([TimeStepType.concrete]);

const loading = ref(false);
const minHorizon = 1;

const start = async () => {
  if (
    !concreteProblemFile.value || !concreteDomainFile.value ||
    !abstractProblemFile.value || !abstractDomainFile.value
  ) {
    alert('Please select all four files.');
    return;
  }

  loading.value = true;
try {
    const result = await getConcreteFromAbstractPlan({
      abstractProblemFile: abstractProblemFile.value,
      abstractDomainFile: abstractDomainFile.value,
      concreteProblemFile: concreteProblemFile.value,
      concreteDomainFile: concreteDomainFile.value,
      horizon: horizon.value,
      encoding: encoding.value[0],
      timeStep: timeStep.value[0] !== TimeStepType.concrete,
    });
  } catch (err: any) {
    alert(err.message ?? 'Error calculating concrete plan.');
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
  gap: 1rem;
}

.input-fields .button {
  align-self: flex-end;
}

.horizon-output {
  margin-top: 0.5rem;
}
</style>
