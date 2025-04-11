<template>
  <div class="input-wrapper">
    <label :for="inputId">{{ label }}</label>

    <select
      :id="inputId"
      v-model="selectedValue"
      class="input"
    >
      <option disabled value="">-- Select an option --</option>
      <option
        v-for="(option, index) in options"
        :key="index"
        :value="option" >
        {{ formatOption(option) }} </option>
    </select>
  </div>
</template>

<script setup lang="ts">
  import { ref, watch, computed, type PropType } from 'vue'
  import { nanoid } from 'nanoid'

  const props = defineProps({
    label: {
      type: String,
      required: true,
    },
    modelValue: {
      type: [String, null],
      default: '',
    },
    options: {
      type: Array as PropType<string[]>, // Expect an array of strings
      required: true,
      default: () => [],
    },
  })

  const emit = defineEmits(['update:modelValue'])

  const inputId = computed(() => `select-${nanoid(6)}`)

  const selectedValue = ref(props.modelValue)

  watch(() => props.modelValue, (newVal) => {
    selectedValue.value = newVal
  })

  watch(selectedValue, (val) => {
    emit('update:modelValue', val)
  })

  const formatOption = (option: string) => {
    return option.charAt(0).toUpperCase() + option.slice(1);
  }
</script>
<style scoped>
  .input-wrapper {
    display: flex;
    flex-direction: column;
  }
  .input {
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 0.5rem;
    flex: 1;
    min-width: 200px;
  }
</style>
  