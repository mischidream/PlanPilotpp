<template>
  <div class="search-fields">
    <DropdownField
      label="Facet:"
      :options="Object.values(SelectionState)"
      :isMultiple="true"
      v-model="internalFacetState"
    />
    <DropdownField
      label="Action:"
      :options="Object.values(ActionType)"
      :isMultiple="true"
      v-model="internalActionType"
    />
    <DropdownField
      label="Objects:"
      :options="allObjects"
      :isMultiple="true"
      v-model="internalObjects"
    />
    <DropdownField
      label="Timesteps:"
      :options="allTimesteps"
      :isMultiple="true"
      v-model="internalTimesteps"
    />
    <Button label="Reset filters" type="submit" @click="onResetFilters"></Button>
  </div>
</template>

<script setup lang="ts">
import DropdownField from './DropdownField.vue';
import Button from './Button.vue';
import { ref, watch } from 'vue';
import { SelectionState } from '@/models/SelectionState';
import { ActionType } from '@/models/ActionType';

const props = defineProps<{
  selectedFacetState: SelectionState[];
  selectedActionType: ActionType[];
  selectedObjects: string[];
  selectedTimesteps: string[];
  allObjects: string[];
  allTimesteps: string[];
}>();

const emit = defineEmits<{
  'update:selectedFacetState': [SelectionState[]];
  'update:selectedActionType': [ActionType[]];
  'update:selectedObjects': [string[]];
  'update:selectedTimesteps': [string[]];
}>();

const internalFacetState = ref([...props.selectedFacetState]);
const internalActionType = ref([...props.selectedActionType]);
const internalObjects = ref([...props.selectedObjects]);
const internalTimesteps = ref([...props.selectedTimesteps]);

watch(internalFacetState, (val) => emit('update:selectedFacetState', val), { deep: true });
watch(internalActionType, (val) => emit('update:selectedActionType', val), { deep: true });
watch(internalObjects, (val) => emit('update:selectedObjects', val), { deep: true });
watch(internalTimesteps, (val) => emit('update:selectedTimesteps', val), { deep: true });

watch(() => props.allObjects, (newOptions) => {
  internalObjects.value = internalObjects.value.filter(obj => newOptions.includes(obj));
});

watch(() => props.allTimesteps, (newOptions) => {
  internalTimesteps.value = internalTimesteps.value.filter(t => newOptions.includes(t));
});

watch(() => Object.values(SelectionState), (validStates) => {
  internalFacetState.value = internalFacetState.value.filter(s => validStates.includes(s));
});

watch(() => Object.values(ActionType), (validActions) => {
  internalActionType.value = internalActionType.value.filter(a => validActions.includes(a));
});


function onResetFilters() {
  internalFacetState.value = [];
  internalActionType.value = [];
  internalObjects.value = [];
  internalTimesteps.value = [];
}
</script>

<style scoped>
.search-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.search-fields .button{
  align-self: flex-end;
}
</style>
