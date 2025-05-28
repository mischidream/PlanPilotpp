<template>
  <div v-if="loadingFacetCount || loadingAnswerSetCount || answerSetCount || facetCount">
    <Divider />
    <div class="count">
      <p v-if="loadingAnswerSetCount"><SkeletonCount /></p>
      <p v-else-if="answerSetCount">Answer Sets: {{ answerSetCount }}</p>

      <p v-if="loadingFacetCount"><SkeletonCount /></p>
      <p v-else-if="facetCount">Facets: {{ facetCount }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import Divider from '@/components/Divider.vue';
import SkeletonCount from '@/components/SkeletonCount.vue';

const props = defineProps<{
  loadingAnswerSetCount: boolean;
  loadingFacetCount: boolean;
  answerSetCount: string | null;
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
