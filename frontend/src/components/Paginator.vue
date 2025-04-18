<template>
  <div class="paginator-wrapper">
    <div class="paginator">
      <button 
        :disabled="currentPage === 1" 
        @click="goToPreviousPage"
        class="paginator-button">
        Previous
      </button>

      <button 
        v-if="currentPage > 3"
        @click="goToPage(1)"
        class="paginator-button">
        1
      </button>
      <span v-if="currentPage > 3" class="ellipsis">...</span>

      <button 
        v-for="page in pageNumbers" 
        :key="page" 
        :class="{ active: page === currentPage }" 
        @click="goToPage(page)"
        class="paginator-button">
        {{ page }}
      </button>

      <span v-if="currentPage < totalPages - 2" class="ellipsis">...</span>
      <button 
        v-if="currentPage < totalPages - 2"
        @click="goToPage(totalPages)"
        class="paginator-button">
        {{ totalPages }}
      </button>

      <button 
        :disabled="currentPage === totalPages" 
        @click="goToNextPage"
        class="paginator-button">
        Next
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { nanoid } from 'nanoid'

// Props for pagination configuration
const props = defineProps({
  totalItems: {
    type: Number,
    required: true,
  },
  itemsPerPage: {
    type: Number,
    default: 10, // Default items per page
  },
})

const emit = defineEmits(['update:currentPage'])

// Reactive state
const currentPage = ref(1)

// Computed property for total pages
const totalPages = computed(() => {
  return Math.ceil(props.totalItems / props.itemsPerPage)
})

// Page numbers to display (5 pages around current page)
const pageNumbers = computed(() => {
  const pages = []
  const start = Math.max(currentPage.value - 2, 1)
  const end = Math.min(currentPage.value + 2, totalPages.value)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

// Watch for currentPage change to emit the updated value
watch(currentPage, (newPage) => {
  emit('update:currentPage', newPage)
})

// Methods to change page
function goToPreviousPage() {
  if (currentPage.value > 1) {
    currentPage.value -= 1
  }
}

function goToNextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value += 1
  }
}

function goToPage(page: number) {
  currentPage.value = page
}
</script>

<style scoped>
.paginator-wrapper {
  display: flex;
  flex-direction: column;
}

.paginator {
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 0.5rem;
}

.paginator-button {
  padding: 0.5rem;
  border: 1px solid var(--border);
  border-radius: var(--border-radius);
  background-color: var(--background-soft);
  color: var(--text-dark-1);
  cursor: pointer;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.paginator-button:disabled {
  background-color: var(--white-soft);
  color: var(--text-light-2);
  cursor: not-allowed;
}

.paginator-button.active {
  font-weight: bold;
  background-color: var(--light-blue);
  color: var(--white);
}

.ellipsis {
  align-self: center;
  color: var(--text-light-2);
  font-weight: bold;
}
</style>
