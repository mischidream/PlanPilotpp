<template>
  <div class="dropdown-wrapper" ref="wrapper">
    <div
      v-for="(value, index) in dropdowns"
      :key="index"
      class="dropdown"
      :ref="el => setDropdownRef(el, index)"
    >
      <DropdownField
        :modelValue="normalizeToArray(value)"
        :options="options"
        :isMultiple="true"
        :isMultiStatus="true"
        @update:modelValue="val => emitUpdate(index, val)"
      />
    </div>

    <svg class="arrows">
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="black" />
        </marker>
      </defs>

      <path
        v-for="(path, i) in arrowPaths"
        :key="i"
        :d="path"
        stroke="black"
        fill="none"
        marker-end="url(#arrowhead)"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import {
  ref,
  onMounted,
  onBeforeUnmount,
  nextTick,
  watch,
  computed,
  type ComponentPublicInstance,
  type PropType,
} from 'vue';
import DropdownField from './DropdownField.vue';
import type { MultiSelectState } from '@/models/MultiSelectState';

type DropdownValue = 
  | null 
  | string 
  | MultiSelectState 
  | (string | MultiSelectState)[];

// Props
const props = defineProps({
  dropdowns: {
    type: Array as PropType<DropdownValue[]>,
    default: () => [],
  },
  options: {
    type: Array as PropType<string[]>,
    default: () => [],
  },
});
const emit = defineEmits(['update:dropdowns']);

// Refs
const dropdownRefs = ref<(HTMLElement | null)[]>([]);
const wrapper = ref<HTMLElement | null>(null);
const arrowPaths = ref<string[]>([]);

// Normalize any value to array for DropdownField
function normalizeToArray(value: DropdownValue): (string | MultiSelectState)[] {
  if (value === null) return [];
  if (Array.isArray(value)) return value;
  return [value];
}

// Emit updated value as array or null (if empty)
function emitUpdate(index: number, value: (string | MultiSelectState)[]) {
  const updated = [...props.dropdowns];
  updated[index] = value.length === 0 ? null : value;
  console.log('DropdownFlow emitting update:', updated);
  emit('update:dropdowns', updated);
}

// Set refs
function setDropdownRef(el: Element | ComponentPublicInstance | null, index: number) {
  if (el && '$el' in el) {
    dropdownRefs.value[index] = (el as ComponentPublicInstance).$el as HTMLElement;
  } else {
    dropdownRefs.value[index] = el as HTMLElement | null;
  }
}

// Arrow drawing logic
function updateArrows() {
  arrowPaths.value = [];
  if (!wrapper.value) return;

  const wrapperRect = wrapper.value.getBoundingClientRect();

  for (let i = 0; i < dropdownRefs.value.length - 1; i++) {
    const fromEl = dropdownRefs.value[i];
    const toEl = dropdownRefs.value[i + 1];
    if (!(fromEl && toEl)) continue;

    const from = fromEl.getBoundingClientRect();
    const to = toEl.getBoundingClientRect();

    const startX = from.right - wrapperRect.left;
    const startY = from.top + from.height / 2 - wrapperRect.top;
    const endX = to.left - wrapperRect.left;
    const endY = to.top + to.height / 2 - wrapperRect.top;

    if (Math.abs(from.top - to.top) < 10) {
      // Same line
      arrowPaths.value.push(`M${startX},${startY} L${endX},${endY}`);
    } else {
      // Zig-zag
      const horizontalGap = 30;
      const yBetween = (from.bottom + to.top) / 2 - wrapperRect.top;

      const path = [
        `M${startX},${startY}`,
        `L${startX + horizontalGap},${startY}`,
        `L${startX + horizontalGap},${yBetween}`,
        `L${endX - horizontalGap},${yBetween}`,
        `L${endX - horizontalGap},${endY}`,
        `L${endX},${endY}`,
      ].join(' ');
      arrowPaths.value.push(path);
    }
  }
}

// Watchers
watch(
  () => props.dropdowns,
  (newVal) => {
    console.log('DropdownFlow received dropdowns:', newVal);
    nextTick(updateArrows);
  },
  { immediate: true, deep: true }
);



onMounted(() => {
  nextTick(() => {
    updateArrows();
    window.addEventListener('resize', updateArrows);

    // Watch dropdowns
    dropdownRefs.value.forEach(el => {
      if (!el) return;
      new ResizeObserver(updateArrows).observe(el);
    });

    // Watch wrapper height changes too (important!)
    if (wrapper.value) {
      new ResizeObserver(updateArrows).observe(wrapper.value);
    }
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateArrows);
});
</script>

<style scoped>
.dropdown-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
  padding: 24px;
  padding-left: 48px;
  position: relative;
}

.dropdown {
  flex: 0 0 auto;
  min-width: 10rem;
}

.arrows {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}
</style>
