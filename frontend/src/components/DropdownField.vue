<template>
  <div class="input-wrapper">
    <label :for="inputId">{{ label }}</label>

    <div class="dropdown-input" @click="toggleDropdown">
      <span>
        {{ selectedItemsPreview }}
      </span>
      <span class="material-icons dropdown-icon">
        {{ isOpen ? 'expand_less' : 'expand_more' }}
      </span>
    </div>

    <div v-show="isOpen" class="checkbox-dropdown">
      <div v-for="(option, index) in options" :key="index" class="checkbox-item">
        <label v-if="props.isMultiple">
          <input
            type="checkbox"
            :value="option"
            :checked="selectedValues.includes(option)"
            @change="toggleSelection(option)"
          />
          {{ formatOption(option) }}
        </label>
        <label v-else>
          <div @click="toggleSelection(option)" class="radio-option">
            <span class="material-icons">
              {{ selectedValues.includes(option) ? 'radio_button_checked' : 'radio_button_unchecked' }}
            </span>
            {{ formatOption(option) }}
          </div>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, type PropType } from 'vue'
import { nanoid } from 'nanoid'

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  modelValue: {
    type: Array as PropType<(string | number)[]>,
    default: () => [],
  },
  options: {
    type: Array as PropType<(string | number)[]>,
    required: true,
    default: () => [],
  },
  isMultiple: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const inputId = computed(() => `select-${nanoid(6)}`)

const selectedValues = ref([...props.modelValue])

watch(() => props.modelValue, (newVal) => {
  selectedValues.value = [...newVal]
})

watch(selectedValues, (newVal) => {
  emit('update:modelValue', newVal)
})

const formatOption = (option: string | number) => {
  const str = option.toString()
  return str.charAt(0).toUpperCase() + str.slice(1)
}

const isOpen = ref(false)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const toggleSelection = (option: string | number) => {
  const index = selectedValues.value.indexOf(option)
  if (props.isMultiple) {
    if (index === -1) {
      selectedValues.value.push(option)
    } else {
      selectedValues.value.splice(index, 1)
    }
  } else {
    if (selectedValues.value.includes(option)) {
      selectedValues.value = []
    } else {
      selectedValues.value = [option]
    }
    isOpen.value = false
  }
}

const selectedItemsPreview = computed(() => {
  if (props.isMultiple) {
    if(selectedValues.value.length === 0){
      return 'Select options'
    }
    const previewLimit = 2
    const previewItems = selectedValues.value.slice(0, previewLimit)
    const remainingItemsCount = selectedValues.value.length - previewItems.length

    if (remainingItemsCount > 0) {
      return `${previewItems.join(', ')} and ${remainingItemsCount} more`
    } else {
      return previewItems.join(', ')
    }
  } else {
    return selectedValues.value.length > 0 ? selectedValues.value[0] : 'Select an option'
  }
})
</script>

<style scoped>
.input-wrapper {
  display: flex;
  flex-direction: column;
  position: relative;
}

.input {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 0.5rem;
  flex: 1;
  min-width: 200px;
  cursor: pointer;
}

.dropdown-input {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 0.5rem;
  cursor: pointer;
  min-width: 200px;
}

.checkbox-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  max-height: 200px;
  overflow-y: auto;
  width: 100%;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 0.5rem;
}

.checkbox-item {
  padding: 8px;
}

.checkbox-dropdown label {
  display: flex;
  align-items: center;
}

.checkbox-dropdown input[type="checkbox"] {
  margin-right: 8px;
}

.radio-option {
  display: flex;
  align-items: center;
  width: 100%;
}

.radio-option .material-icons {
  margin-right: 8px;
  font-size: 18px;
  display: inline-flex;
  align-items: center;
}
</style>