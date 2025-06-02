<template>
  <div class="input-wrapper">
    <label :for="inputId">{{ label }}</label>

    <input
      v-if="type === 'text' || type === 'number'"
      :id="inputId"
      :type="type"
      :placeholder="placeholder"
      v-model="inputValue"
      :disabled="disabled"
      class="input"
    />

    <div v-else-if="type == 'file'" class="file-input-container">
      <input
        ref="fileInput"
        :id="inputId"
        type="file"
        @change="handleFileChange"
        :accept="accept"
        :disabled="disabled"
        class="hidden-input"
      />
      <label :for="inputId" class="file-button" :class="{ disabled: disabled }">
        Choose File
      </label>
      <div class="file-name">
        {{ fileName }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { nanoid } from 'nanoid';
import { debounce } from 'lodash-es';

const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  modelValue: {
    type: [String, Number, File, Object, null],
    default: '',
  },
  type: {
    type: String,
    default: 'text',
    validator: (val: string) => ['text', 'number', 'file'].includes(val),
  },
  placeholder: {
    type: String,
    default: '',
  },
  accept: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue']);

const debouncedEmit = debounce((val: any) => {
  emit('update:modelValue', val);
}, 300);

const inputId = computed(() => `input-${nanoid(6)}`);

const inputValue = ref(props.modelValue);

const fileInput = ref<HTMLInputElement | null>(null);
const selectedFileName = ref('');

watch(
  () => props.modelValue,
  val => (inputValue.value = val)
);

watch(inputValue, val => {
  if (props.type === 'number') {
    const parsed = typeof val === 'string' ? parseFloat(val) : val;
    debouncedEmit(isNaN(parsed as number) ? null : parsed);
  } else if (props.type === 'text' && typeof val === 'string') {
    debouncedEmit(val);
  }
});

const fileName = computed(() => {
  const val = props.modelValue;
  return val && typeof val === 'object' && 'name' in val ? val.name : 'No file selected.';
});

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files ? target.files[0] : null;
  emit('update:modelValue', file);
}
</script>

<style scoped>
.input-wrapper {
  display: flex;
  flex-direction: column;
}

.input {
  padding: 0.5rem;
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  flex: 1;
  min-width: 12.5rem;
  min-height: 2.5rem;
}

.file-input-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.hidden-input {
  display: none;
}

.file-button {
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  background-color: var(--gray-soft);
  cursor: pointer;
  font-size: 0.9rem;
  user-select: none;
  transition:
    background-color 0.2s,
    transform 0.1s ease;
}

.file-button:hover {
  background-color: var(--white-mute);
}

.file-button:active {
  background-color: var(--white-soft);
  transform: scale(0.98);
}

.file-button.disabled {
  background-color: var(--white-mute);
  color: var(--gray-mute);
  cursor: not-allowed;
  pointer-events: none;
}

.file-name {
  font-size: 0.9rem;
  color: var(--text-light-2);
  max-width: 12.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
