<template>
  <div v-if="solution">
    <div class="controls">
      <Button label="Restart" type="button" @click="restart" :disabled="solution === null"></Button>
      <Button label="Prev" type="button" @click="prevStep" :disabled="step <= -1"></Button>
      <Button
        :label="playing ? 'Pause' : 'Play'"
        type="button"
        @click="togglePlay"
        :disabled="solution === null"
      ></Button>
      <Button
        label="Next"
        type="button"
        @click="nextStep"
        :disabled="step >= sortedFacets.length - 1"
      ></Button>
    </div>

    <p class="description">
      <span>{{ currentActionDescription }}</span>
    </p>

    <div class="svg-wrapper">
      <svg :width="computedSvgWidth" :height="height" class="block-area">
        <!-- Picked-up block (in hand) -->
        <g v-for="(block, idx) in pickedUpBlocks" :key="'picked-' + block.name">
          <rect
            :x="width / 2 - blockWidth / 2 + idx * (blockWidth + 10)"
            :y="50"
            :width="blockWidth"
            :height="blockHeight"
            :fill="block.color"
            rx="4"
            stroke="black"
            stroke-width="3"
          />
          <text
            :x="width / 2 + idx * (blockWidth + 10)"
            :y="50 + blockHeight / 2 + 5"
            text-anchor="middle"
            alignment-baseline="middle"
            fill="white"
            font-size="16"
          >
            {{ block.name }}
          </text>
        </g>

        <!-- Visual blocks on table -->
        <g v-for="(block, index) in visualBlocks" :key="block.name">
          <rect
            :x="block.x"
            :y="block.y"
            :width="blockWidth"
            :height="blockHeight"
            :fill="block.color"
            rx="4"
            :stroke="block.highlight ? 'black' : 'none'"
            :stroke-width="block.highlight ? 3 : 0"
          />
          <text
            :x="block.x + blockWidth / 2"
            :y="block.y + blockHeight / 2 + 5"
            text-anchor="middle"
            alignment-baseline="middle"
            fill="white"
            font-size="16"
          >
            {{ block.name }}
          </text>
        </g>
      </svg>
    </div>
  </div>
  <div v-else>
    <p>No solution loaded. Please load a solution to begin.</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import type { Solution } from '@/models/Solution';
import Button from '@/components/Button.vue';
import type { Block } from '@/models/Block';

// Props
const props = defineProps<{
  solution: Solution | null;
}>();

// Extract all unique block names
const allBlockNames = Array.from(
  new Set(
    props.solution?.facets
      .flatMap(facet => [facet.constant1, facet.constant2])
      .filter((name): name is string => typeof name === 'string')
  )
);

const colorPalette = generateColorPalette(allBlockNames.length);

const blockColors = Object.fromEntries(
  allBlockNames.map((name, i) => [name, colorPalette[i % colorPalette.length]])
) as Record<string, string>;

const getBlockColor = (name: string) => blockColors[name] ?? '#9ca3af';

// Constants
const width = 600;
const height = 300;
const blockWidth = 60;
const blockHeight = 30;

// Reactive state
const step = ref(-1);
const playing = ref(false);
const visualBlocks = ref<Block[]>([]);
const pickedUpBlocks = ref<Block[]>([]);
let interval: number | null = null;

// Step data
const sortedFacets = [...(props.solution?.facets ?? [])]
  .filter(f => f.timestep !== 0)
  .sort((a, b) => a.timestep - b.timestep);

const computedSvgWidth = computed(() => {
  const numStacks = Object.keys(computeStack(step.value)).length;
  const pickupLength = pickedUpBlocks.value.length;
  const pickupWidth = width / 2 - blockWidth / 2 + pickupLength * (blockWidth + 10) + 50;
  return Math.max(width, numStacks * (blockWidth + 20) + 100, pickupWidth);
});

function generateColorPalette(n: number): string[] {
  const colors: string[] = [];
  const saturation = 70;
  const lightness = 50;
  for (let i = 0; i < n; i++) {
    const hue = ((i * 360) / n) % 360;
    colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`);
  }
  return colors;
}

// Compute stack state for all blocks on table
function computeStack(stepIndex: number): Record<string, string[]> {
  const stacks: Record<string, string[]> = {};
  const tableBlocks = new Set(allBlockNames);
  const pickedUpBlocksSet = new Set<string>();

  for (let i = 0; i <= stepIndex; i++) {
    const { action, constant1, constant2 } = sortedFacets[i];

    if (action === 'pick-up') {
      // Remove from any stack and mark as picked up
      for (const key in stacks) stacks[key] = stacks[key].filter(b => b !== constant1);
      tableBlocks.delete(constant1);
      pickedUpBlocksSet.add(constant1);
    } else if (action === 'put-down' || action === 'stack' || action === 'unstack') {
      // If block was picked up, now it's placed down or moved, so remove from pickedUpBlocksSet
      if (pickedUpBlocksSet.has(constant1)) {
        pickedUpBlocksSet.delete(constant1);
      }
    }

    if (action === 'stack' && constant2) {
      // Remove from any stacks
      for (const key in stacks) stacks[key] = stacks[key].filter(b => b !== constant1);
      stacks[constant2] = stacks[constant2] || [];
      stacks[constant2].push(constant1);
      tableBlocks.delete(constant1);
    } else if (action === 'unstack' && constant2) {
      stacks[constant2] = stacks[constant2]?.filter(b => b !== constant1) || [];
      tableBlocks.add(constant1);
    } else if (action === 'put-down') {
      tableBlocks.add(constant1);
    }
  }

  pickedUpBlocks.value = [...pickedUpBlocksSet].map(blockName => ({
    name: blockName,
    x: 0,
    y: 0,
    color: getBlockColor(blockName),
    highlight: true,
  }));

  const result: Record<string, string[]> = {};
  for (const base of tableBlocks) {
    result[base] = [];
    let current = base;
    while (stacks[current]?.length) {
      const top = stacks[current][0];
      result[base].push(top);
      current = top;
    }
  }
  return result;
}

function updateVisualBlocks() {
  if (step.value < 0) {
    visualBlocks.value = allBlockNames.map((name, i) => ({
      name,
      x: 50 + i * (blockWidth + 20),
      y: height - blockHeight - 20,
      color: getBlockColor(name),
      highlight: false,
    }));
    pickedUpBlocks.value = [];
    return;
  }

  const currentStacks = computeStack(step.value);
  const currentFacet = sortedFacets[step.value];
  const shouldHighlight = step.value < sortedFacets.length - 1;
  const active = shouldHighlight
    ? new Set([currentFacet?.constant1, currentFacet?.constant2])
    : new Set();

  const blocks: Block[] = [];
  let column = 0;

  for (const base of Object.keys(currentStacks)) {
    const stack = [base, ...currentStacks[base]];
    stack.forEach((blockName, i) => {
      blocks.push({
        name: blockName,
        x: column * (blockWidth + 20) + 50,
        y: height - (i + 1) * (blockHeight + 5) - 20,
        color: getBlockColor(blockName),
        highlight: active.has(blockName),
      });
    });
    column++;
  }

  visualBlocks.value = blocks;
}

const nextStep = () => {
  if (step.value < sortedFacets.length - 1) {
    step.value++;
    updateVisualBlocks();
  }
};
const prevStep = () => {
  if (step.value > -1) {
    step.value--;
    updateVisualBlocks();
  }
};
const restart = () => {
  step.value = -1;
  updateVisualBlocks();
};
const togglePlay = () => {
  if (playing.value) {
    clearInterval(interval!);
    playing.value = false;
  } else {
    if (step.value >= sortedFacets.length - 1) {
      step.value = -1; // Restart from beginning
    }
    playing.value = true;
    updateVisualBlocks(); // Ensure first visual is updated
    interval = setInterval(() => {
      if (step.value < sortedFacets.length - 1) {
        step.value++;
        updateVisualBlocks();
      } else {
        clearInterval(interval!);
        playing.value = false;
      }
    }, 1000);
  }
};

const currentActionDescription = computed(() => {
  if (step.value < 0) return 'No action yet. Press play or next.';
  if (step.value >= sortedFacets.length - 1) return 'Last step reached.';
  const a = sortedFacets[step.value];
  return `t=${a.timestep}: ${a.action}(${a.constant1}${a.constant2 ? `, ${a.constant2}` : ''})`;
});

onMounted(updateVisualBlocks);
onUnmounted(() => {
  if (interval) clearInterval(interval);
});
</script>

<style scoped>
.controls {
  margin-bottom: 1rem;
  display: flex;
  gap: 1rem;
}

.svg-wrapper {
  overflow-x: auto;
  border: 1px solid var(--border);
  background-color: var(--background-mute);
  border-radius: var(--border-radius);
  margin-bottom: 1rem;
}

.block-area {
  background-color: var(--gray-soft);
}

.description {
  font-weight: bold;
  margin-bottom: 1rem;
  color: var(--text);
}

button {
  padding: 0.5rem 1rem;
  background-color: var(--light-blue);
  color: var(--white);
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
}

button:hover {
  background-color: var(--deep-blue);
}

button:disabled {
  background-color: var(--gray-mute);
  cursor: not-allowed;
}
</style>
