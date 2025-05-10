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

    <div v-else-if="type == 'file'">
      <div v-if="filePath" class="file-info">
        <p><strong>Selected file:</strong> {{ filePath }}</p>
      </div>
      <input
        :id="inputId"
        type="file"
        @change="handleFileChange"
        :accept="accept"
        :disabled="disabled"
        class="input"
      />
    </div>
  </div>
</template>
  
<script setup lang="ts">
  import { ref, watch, computed } from 'vue'
  import { nanoid } from 'nanoid'
  
  const props = defineProps({
    label: {
      type: String,
      required: true,
    },
    modelValue: {
      type: [String, Number, File, null],
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
      default: false
    }
  })
  
  const emit = defineEmits(['update:modelValue'])
  
  const inputId = computed(() => `input-${nanoid(6)}`)
  
  const inputValue = ref(props.modelValue)
  
  watch(() => props.modelValue, (newVal) => {
    inputValue.value = newVal
  })
  
  watch(inputValue, (val) => {
    if (props.type === 'number') {
      const parsed = typeof val === 'string' ? parseFloat(val) : val
      emit('update:modelValue', isNaN(parsed as number) ? null : parsed)
    } else if (props.type === 'text' && typeof val === 'string') {
      emit('update:modelValue', val)
    }
  })
  
  function handleFileChange(e: Event) {
    const target = e.target as HTMLInputElement
    const file = target.files ? target.files[0] : null
    emit('update:modelValue', file)
  }

  const filePath = computed(() => {
    if (props.type === 'file' && typeof props.modelValue === 'string') {
      return props.modelValue
    }
    return ''
  })
</script>
  
<style scoped>
.input-wrapper {
  display: flex;
  flex-direction: column;
}
.input {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 0.5rem;
  flex: 1;
  min-width: 200px;
  min-height: 40px;
}
</style>
  