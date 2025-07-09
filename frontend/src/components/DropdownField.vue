<template>
  <div class="input-wrapper" ref="dropdownRef">
    <label :for="inputId">{{ label }}</label>

    <div class="dropdown-input" @click="toggleDropdown"  :class="{ disabled: props.disabled }">
      <span>
        {{ selectedItemsPreview }}
      </span>
      <span class="material-icons dropdown-icon">
        {{ isOpen ? 'expand_less' : 'expand_more' }}
      </span>
    </div>

    <div v-show="isOpen" class="checkbox-dropdown" @click.stop>
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Search..."
        class="search-input"
        @click.stop
        autocomplete="off"
      />
      <div v-for="option in filteredOptions" :key="option" class="checkbox-item">
        <div v-if="props.isMultiple">
          <div v-if="props.isMultiStatus" class="multi-state-option">
            <span
              class="material-icons state-icon"
              :class="{ active: selectedValuesMap[option] === 'add' }"
              @click="setState(option, 'add')"
            >
              add_box
            </span>
            <span
              class="material-icons state-icon"
              :class="{ active: selectedValuesMap[option] === 'remove' }"
              @click="setState(option, 'remove')"
            >
              indeterminate_check_box
            </span>
            <span class="option-label">{{ option }}</span>
          </div>
          <div v-else>
            <label>
              <input
                type="checkbox"
                :value="option"
                :checked="selectedValues.includes(option)"
                @change="toggleSelection(option)"
              />
              {{ option }}
            </label>
          </div>
        </div>
        <div v-else>
          <label>
            <div @click="toggleSelection(option)" class="radio-option">
              <span class="material-icons">
                {{
                  selectedValues.includes(option)
                    ? 'radio_button_checked'
                    : 'radio_button_unchecked'
                }}
              </span>
              {{ option }}
            </div>
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType, onMounted, onUnmounted } from 'vue';
import { nanoid } from 'nanoid';
import type { MultiSelectState } from '@/models/MultiSelectState';

const props = defineProps({
  label: {
    type: String,
  },
  modelValue: {
    type: Array as PropType<(string | number | MultiSelectState)[]>,
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
  isMultiStatus: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const dropdownRef = ref<HTMLElement | null>(null);

const emit = defineEmits(['update:modelValue']);

const inputId = computed(() => `select-${nanoid(6)}`);

const isOpen = ref(false);
const searchQuery = ref('');

const toggleDropdown = () => {
  if (props.disabled) return;
  isOpen.value = !isOpen.value;
  if (!isOpen.value) {
    searchQuery.value = '';
  }
};

const selectedValues = computed({
  get: () => props.modelValue,
  set: val => emit('update:modelValue', val),
});

const isMultiSelectState = (entry: unknown): entry is MultiSelectState => {
  return (
    (typeof entry === 'object' &&
      entry !== null &&
      'option' in entry &&
      'state' in entry &&
      (entry as any).state === 'add') ||
    (entry as any).state === 'remove'
  );
};

const selectedValuesMap = computed(() => {
  const map: Record<string | number, 'add' | 'remove' | null> = {};
  props.options.forEach(option => {
    const match = props.modelValue.find(
      (entry): entry is MultiSelectState => isMultiSelectState(entry) && entry.option === option
    );
    map[option] = match?.state ?? null;
  });
  return map;
});

const setState = (option: string | number, state: 'add' | 'remove') => {
  const updated = props.modelValue.filter(
    (entry): entry is string | number | MultiSelectState =>
      !isMultiSelectState(entry) || entry.option !== option
  );
  if (selectedValuesMap.value[option] === state) {
    emit('update:modelValue', updated);
  } else {
    updated.push({ option, state });
    emit('update:modelValue', updated);
  }
};

const toggleSelection = (option: string | number) => {
  if (props.disabled) return;
  const index = selectedValues.value.indexOf(option);
  if (props.isMultiple) {
    if (index === -1) {
      selectedValues.value.push(option);
    } else {
      selectedValues.value.splice(index, 1);
    }
  } else {
    if (selectedValues.value.includes(option)) {
      selectedValues.value = [];
    } else {
      selectedValues.value = [option];
    }
    isOpen.value = false;
    searchQuery.value = '';
  }
};

const filteredOptions = computed(() => {
  const lowerSearch = searchQuery.value.toLowerCase();

  // Filter options by search query
  const filtered = props.options.filter(option =>
    String(option).toLowerCase().includes(lowerSearch)
  );

  const selectedSet = new Set<string | number>();

  for (const entry of props.modelValue) {
    if (isMultiSelectState(entry)) {
      // Multi-status entry
      selectedSet.add(entry.option);
    } else {
      // Regular string/number entry
      selectedSet.add(entry);
    }
  }

  // Separate selected and unselected options
  const selectedFiltered = filtered.filter(option => selectedSet.has(option));
  const nonSelectedFiltered = filtered.filter(option => !selectedSet.has(option));

  return [...selectedFiltered, ...nonSelectedFiltered];
});

const selectedItemsPreview = computed(() => {
  if (props.isMultiple && props.isMultiStatus) {
    const added = props.modelValue.filter(isMultiSelectState).filter(e => e.state === 'add');
    const removed = props.modelValue.filter(isMultiSelectState).filter(e => e.state === 'remove');

    const previewParts: string[] = [];
    if (added.length > 0) previewParts.push(`+ ${added.map(e => e.option).join(', ')}`);
    if (removed.length > 0) previewParts.push(`- ${removed.map(e => e.option).join(', ')}`);
    if (previewParts.length === 0) return 'Select options';
    return previewParts.join(' | ');
  } else {
    return selectedValues.value.length > 0 ? String(selectedValues.value[0]) : 'Select an option';
  }
});

const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false;
    searchQuery.value = '';
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.input-wrapper {
  display: flex;
  flex-direction: column;
  position: relative;
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

.dropdown-input.disabled {
  background-color: var(--gray-soft);
  color: var(--gray-mute);
  cursor: not-allowed;
  pointer-events: none;
  border-color: var(--divider-light-1);
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

.checkbox-dropdown input[type='checkbox'] {
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

.search-input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.5rem;
  border: none;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.5rem;
  font-size: 1rem;
}

.multi-state-option {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.state-icon {
  cursor: pointer;
  font-size: 1.25rem;
  opacity: 0.4;
  transition: opacity 0.2s ease;
}

.state-icon.active {
  opacity: 1;
  color: var(--light-blue);
}

.option-label {
  margin-left: 0.5rem;
  flex: 1;
}
</style>
