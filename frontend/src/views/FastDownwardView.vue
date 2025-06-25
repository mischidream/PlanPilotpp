<template>
  <DropdownFlow
    :dropdowns="dropdownValues"
    :options="options"
    @update:dropdowns="dropdownValues = $event"
  />
</template>

<script setup lang="ts">
import DropdownFlow from '@/components/DropdownFlow.vue';
import type { MultiSelectState } from '@/models/MultiSelectState';

import { ref } from 'vue';

const dropdownValues = ref<(string[] | MultiSelectState[] | null)[]>([
  [{ option: 'Short', state: 'add' }],
  [{ option: 'Medium', state: 'add' }],
  null,
  null,
  null,
  null
]);
const options = ['Short', 'Medium', 'Longer option'];
</script>

<style scoped></style>
