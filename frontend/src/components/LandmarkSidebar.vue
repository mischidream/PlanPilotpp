<template>
  <div v-if="enabled" class="sidebar" :class="{ open: isOpen }">
    <div class="sidebar-control">
      <button class="sidebar-toggle-button" @click="toggleSidebar">
        <span class="material-icons toggle-icon">
          {{ isOpen ? 'chevron_right' : 'chevron_left' }}
        </span>
      </button>
    </div>
    <div class="sidebar-content">
      <span class="sidebar-content-header">Implied Actions</span>
      <FacetTable
        :key="landmarks.map(f => f.id).join('-')"
        :headers="['Action', 'Objects', 'Timestep']"
        :facets="landmarks"
        :viewMode="'landmarks'"
        :loading="loadingLandmarks"
        :itemsPerPage="landmarks.length"
        class="landmark-table"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import FacetTable from './FacetTable.vue';

const props = defineProps<{
  enabled: boolean,
  landmarks: any[],
  loadingLandmarks: boolean
}>();

const isOpen = ref(true);

const toggleSidebar = () => {
  if (!props.enabled) return;
  isOpen.value = !isOpen.value;
};

watch(() => props.enabled, (val) => {
  if (!val) isOpen.value = false;
  if (val) isOpen.value = true;
});
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: row;
  width: 2.5rem;
  transition: width 0.3s ease;
  overflow: hidden;
  background-color: var(--white-soft);
}

.sidebar-toggle-button {
  width: 2.5rem;
  height: 100%;
  align-items: center;
  cursor: pointer;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  width: 0;
  overflow: hidden;
  transition: width 0.3s ease, padding 0.3s ease;
}

.sidebar-content-header {
  font-size: 1rem;
  font-weight: bold;
}

.sidebar.open {
  width: 30%;
}

.sidebar.open .sidebar-content {
  width: 100%;
  padding: 1rem;
}
</style>