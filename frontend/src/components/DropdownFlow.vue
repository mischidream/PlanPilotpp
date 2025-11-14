<template>
  <div class="dropdown-wrapper" ref="wrapper">
    <div
      v-for="(value, index) in timeline"
      :key="index"
      class="dropdown"
      :ref="el => setRef(el, index)"
    >
      <DropdownFlowField
        :id="index"
        :modelValue="props.selectedValues[index] ?? undefined"
        :facets="value.facets"
        @update="val => emitUpdate(val, index)"
        @refresh="emitRefresh"
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
import DropdownFlowField from './DropdownFlowField.vue';
import type { MultiSelectState } from '@/models/MultiSelectState';
import type { TimelineStep } from '@/models/TimelineStep';
import type { TimelineFacet } from '@/models/TimelineFacet';
import { TimelineStepType } from '@/models/TimelineStepType';
import type { Facet } from '@/models/Facet';
import { formatFacetOption } from '@/utils/formatFacetOption';

// Props
const props = defineProps({
  timeline: {
    type: Array as PropType<TimelineStep[]>,
    default: () => [],
  },
  selectedValues: {
    type: Array as PropType<(MultiSelectState[] | null)[]>,
    default: () => [],
  },
});

const emit = defineEmits<{
  (e: 'update:commands', payload: { commands: string[]; timestepNumber: number }): void;
  (e: 'refresh', timestepNumber: number): void;
}>();

// Refs
const dropdownRefs = ref<(HTMLElement | null)[]>([]);
const wrapper = ref<HTMLElement | null>(null);
const arrowPaths = ref<string[]>([]);

function emitUpdate(commands: string[], timestepNumber: number) {
  emit('update:commands', { commands, timestepNumber });
}

function emitRefresh(timestepNumber?: number) {
  if (timestepNumber === undefined) return;
  emit('refresh', timestepNumber);
}

function setRef(el: Element | ComponentPublicInstance | null, index: number) {
  dropdownRefs.value[index] =
    el instanceof HTMLElement
      ? el
      : el && '$el' in el
        ? ((el as ComponentPublicInstance).$el as HTMLElement)
        : null;
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

    const arrowYOffset = 12;

    const startX = from.right - wrapperRect.left;
    const startY = from.top + from.height / 2 - wrapperRect.top + arrowYOffset;
    const endX = to.left - wrapperRect.left;
    const endY = to.top + to.height / 2 - wrapperRect.top + arrowYOffset;

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
