<template>
  <div v-if="loadingFacetCount || loadingSolutionCount || solutionCount || facetCount">
    <Divider />
    <div class="count">
      <p v-if="loadingSolutionCount"><SkeletonCount /></p>
      <p v-else-if="solutionCount">Solutions: {{ solutionCount }}</p>

      <p v-if="loadingFacetCount"><SkeletonCount /></p>
      <p v-else-if="facetCount">Facets: {{ facetCount }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import Divider from '@/components/Divider.vue';
import SkeletonCount from '@/components/SkeletonCount.vue';

const props = defineProps<{
  loadingSolutionCount: boolean;
  loadingFacetCount: boolean;
  solutionCount: string | null;
  facetCount: string | null;
}>();
</script>

<style scoped>
.count {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}
</style>
