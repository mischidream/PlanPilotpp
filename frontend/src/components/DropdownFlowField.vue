<template>
  <div class="input-wrapper" ref="dropdownRef">
    <label v-if="props.id !== undefined">Timestep: {{ props.id + 1 }}</label>

    <div class="dropdown-input" @click="toggleDropdown" :class="[highlight, { disabled:
      disabled }]">
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
        <div class="multi-state-option">
          <span
            class="material-icons state-icon"
            :class="{ active: selectedValuesMap[option] === 'add' }"
            @click="setState(String(option), 'add')"
          >
            add_box
          </span>
          <span
            class="material-icons state-icon"
            :class="{ active: selectedValuesMap[option] === 'remove' }"
            @click="setState(String(option), 'remove')"
          >
            indeterminate_check_box
          </span>
          <span class="option-label">{{ option }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, type PropType, onMounted, onUnmounted, type ComputedRef } from 'vue';
import type { MultiSelectState } from '@/models/MultiSelectState';
import type { TimelineFacet } from '@/models/TimelineFacet';
import { TimelineStepType } from '@/models/TimelineStepType';
import { formatFacetOption } from '@/utils/formatFacetOption';
import type { Facet } from '@/models/Facet';

const props = defineProps({
  id: {
    type: Number,
  },
  modelValue: {
    type: Array as PropType<MultiSelectState[]>,
    default: () => [],
  },
  facets: {
    type: Array as PropType<TimelineFacet[]>,
  },
});

const dropdownRef = ref<HTMLElement | null>(null);

const emit = defineEmits<{
  (e: "update", value: string[]): void
}>()


const isOpen = ref(false);
const searchQuery = ref('');

const toggleDropdown = () => {
  if (disabled.value) return;
  isOpen.value = !isOpen.value;
  if (!isOpen.value) {
    searchQuery.value = '';
  }
};

/* const selectedValues = computed({
  get: () => props.modelValue,
  set: val => emit('update:modelValue', val),
}); */

const getHighlightType = (facets: TimelineFacet[]): 'purple' | 'blue' | null => {
  if (facets.some(f => f.type === TimelineStepType.selected)) return 'blue';
  if (facets.some(f => f.type === TimelineStepType.plan)) return 'purple';
  return null;
};
const highlight: ComputedRef<'purple' | 'blue' | null> = computed(() =>
  getHighlightType(props.facets ?? [])
)

const isDisabled = (facets: TimelineFacet[]): boolean => {
  const hasImplied = facets.some(f => f.type === TimelineStepType.implied);
  const hasPlan = facets.some(f => f.type === TimelineStepType.plan);
  const hasSelected = facets.some(f => f.type === TimelineStepType.selected);
  return hasImplied && !hasPlan && !hasSelected;
};
const disabled: ComputedRef<boolean> = computed(() =>
  isDisabled(props.facets ?? [])
)

function getOptions(value: TimelineFacet[]): (string | number)[] {
  if (
    value.some(f => f.type === TimelineStepType.plan) ||
    value.some(f => f.type === TimelineStepType.selected)
  ) {
    const optional = value.find(f => f.type === TimelineStepType.optional);
    if (Array.isArray(optional?.facets)) {
      return optional.facets.map(formatFacetOption);
    }
  } else if (value.some(f => f.type === TimelineStepType.empty)) {
    const empty = value.find(f => f.type === TimelineStepType.empty);
    if (Array.isArray(empty?.facets)) {
      return empty.facets.map(formatFacetOption);
    }
  }
  return [];
}
const options: ComputedRef<(string | number)[] | undefined> = computed(() =>
  getOptions(props.facets ?? [])
)

const selectedValuesMap = computed(() => {
  const map: Record<string | number, 'add' | 'remove' | null> = {};
  options.value?.forEach(option => {
    const match = props.modelValue.find(
      (entry: MultiSelectState) => entry.option === option
    );
    map[option] = match?.state ?? null;
  });
  return map;
});

// checks if facet is either selected or planned (which both means that it was activated
// and on click should be deactivated
function checkSelectedStatus(facetName: String, timelineFacets: TimelineFacet[]):
'add' | 'remove' | 'none' {
  const impliedFacets = timelineFacets.find(f => f.type === TimelineStepType.implied);
  const selectedFacets = timelineFacets.find(f => f.type === TimelineStepType.selected);
  const plannedFacets = timelineFacets.find(f => f.type === TimelineStepType.plan);
  const allFacets: Facet[] = [
    ...(impliedFacets?.facets ?? []),
    ...(selectedFacets?.facets ?? []),
    ...(plannedFacets?.facets ?? [])
  ];
  for (const facet of allFacets) {
    if (facetName === formatFacetOption(facet)) {
      if (facet.selectionState) {
        if (facet.selectionState === '+') return 'add';
        else if (facet.selectionState === '-') return 'remove';
        else return 'none';
      } else {
        console.error("No selection state for an facet");
      }
    }
  }
  return 'none';
}

// gets the facet id for this facet
function getFacetId(facetName: String, timelineFacets: TimelineFacet[]): string {
  const optionalFacets = timelineFacets.find(f => f.type === TimelineStepType.optional);
  const emptyFacets = timelineFacets.find(f => f.type === TimelineStepType.empty);
  const allFacets: Facet[] = [
    ...(emptyFacets?.facets ?? []),
    ...(optionalFacets?.facets ?? [])
  ];
  for (const facet of allFacets) {
    if (facetName === formatFacetOption(facet)) {
      return facet.id;
    }
  }
  throw Error("No facet with this facet name.");
}

const setState = (option: string, state: 'add' | 'remove') => {
  const selectedStatus = checkSelectedStatus(option, props.facets ?? []);
  // selectedStatus: what it was before; state: what was pressed now
  const emits: string[] = [];
  const facetId: string = getFacetId(option, props.facets ?? []);
  if (selectedStatus === 'add') {
    if (state === 'add') { // was already added so the add should now be unselected
      emits.push(`- ${facetId}`);
    } else {
      // emits.push(`- ${facetId}`, `+ ~${facetId}`);
      emits.push(`+ ~${facetId}`);
    }
  } else if (selectedStatus === 'remove') {
    if (state === 'remove') {
      emits.push(`- ~${facetId}`);
    } else {
      // emits.push(`- ~${facetId}`, `+ ${facetId}`);
      emits.push(`+ ${facetId}`);
    }
  } else { // not selected at all
    if (state === 'add') {
      emits.push(`+ ${facetId}`);
    } else {
      emits.push(`+ ~${facetId}`);
    }
  }
  emit('update', emits);
};

/* const toggleSelection = (option: string | number) => {
  if (disabled.value) return;
  const index = selectedValues.value.indexOf(option);
  if (index === -1) {
    selectedValues.value.push(option);
  } else {
    selectedValues.value.splice(index, 1);
  }
}; */


const filteredOptions = computed(() => {
  const lowerSearch = searchQuery.value.toLowerCase();

  // Filter options by search query
  const filtered = options.value?.filter(option =>
    String(option).toLowerCase().includes(lowerSearch)
  ) ?? [];

  const selectedSet = new Set<string | number>();

  for (const entry of props.modelValue) {
    selectedSet.add(entry.option);
  }

  // Separate selected and unselected options
  const selectedFiltered = filtered.filter(option => selectedSet.has(option));
  const nonSelectedFiltered = filtered.filter(option => !selectedSet.has(option));

  return [...selectedFiltered, ...nonSelectedFiltered];
});

const selectedItemsPreview = computed(() => {
  const added = props.modelValue.filter(e => e.state === 'add');
  const removed = props.modelValue.filter(e => e.state === 'remove');

  const previewParts: string[] = [];
  if (added.length > 0) previewParts.push(`+ ${added.map(e => e.option).join(', ')}`);
  if (removed.length > 0) previewParts.push(`- ${removed.map(e => e.option).join(', ')}`);
  if (previewParts.length === 0) return 'Select options';
  return previewParts.join(' | ');
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

.green {
  background-color: var(--teal-green-transparent);
}

.blue {
  background-color: var(--light-blue-transparent);
}

.purple {
  background-color: var(--soft-purple-transparent);
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

