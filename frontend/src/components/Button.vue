<template>
    <button
      :type="type"
      class="button"
      @click="$emit('click')"
    >
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
    }
  })
  
  defineEmits(['click'])
</script>
  
<style scoped>
  .button {
    padding: 0.5rem 1rem;
    background-color: var(--light-blue);
    color: white;
    border: none;
    border-radius: var(--border-radius);
    cursor: pointer;
    min-width: 100px;
  }
  .button:hover {
    background-color: var(--deep-blue);
  }
</style>
  