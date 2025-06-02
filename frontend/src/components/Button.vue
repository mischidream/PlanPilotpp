<template>
  <button :type="type" class="button" :disabled="disabled" @click="$emit('click')">
    <slot>{{ label }}</slot>
  </button>
</template>

<script setup lang="ts">
import type { PropType } from 'vue';

const props = defineProps({
  label: {
    type: String,
    default: 'Click me',
  },
  type: {
    type: String as PropType<'button' | 'submit' | 'reset'>,
    default: 'button',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['click']);
</script>

<style scoped>
.button {
  padding: 0.5rem 1rem;
  background-color: var(--light-blue);
  color: var(--white);
  border: none;
  border-radius: var(--border-radius);
  cursor: pointer;
  min-width: 6.25rem;
  min-height: 2.5rem;
  transition:
    background-color 0.3s,
    opacity 0.3s;
}

.button:hover {
  background-color: var(--deep-blue);
}

.button:disabled {
  background-color: var(--gray-mute);
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
