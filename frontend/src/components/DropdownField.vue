<template>
  <div class="input-wrapper" ref="dropdownRef">
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
          {{ option }}
        </label>
        <label v-else>
          <div @click="toggleSelection(option)" class="radio-option">
            <span class="material-icons">
              {{ selectedValues.includes(option) ? 'radio_button_checked' : 'radio_button_unchecked' }}
            </span>
            {{ option }}
          </div>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType, onMounted, onUnmounted } from 'vue'
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

const dropdownRef = ref<HTMLElement | null>(null);

const emit = defineEmits(['update:modelValue'])

const inputId = computed(() => `select-${nanoid(6)}`)

const isOpen = ref(false)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const selectedValues = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

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

const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
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
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  flex: 1;
  min-width: 12.5rem;
  cursor: pointer;
  background-color: var(--background);
  color: var(--text);
}

.dropdown-input {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  cursor: pointer;
  min-width: 12.5rem;
  background-color: var(--background);
  color: var(--text);
}

.checkbox-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  max-height: 12.5rem;
  overflow-y: auto;
  width: 100%;
  background-color: var(--background);
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  box-shadow: 0 0.25rem 0.375rem rgba(0, 0, 0, 0.1);
}

.checkbox-item {
  padding: 0.5rem;
  color: var(--text);
}

.checkbox-dropdown label {
  display: flex;
  align-items: center;
  color: var(--text);
}

.checkbox-dropdown input[type="checkbox"] {
  margin-right: 0.5rem;
}

.radio-option {
  display: flex;
  align-items: center;
  width: 100%;
  color: var(--text);
}

.radio-option .material-icons {
  margin-right: 0.5rem;
  font-size: 1.125rem;
  display: inline-flex;
  align-items: center;
}
</style>