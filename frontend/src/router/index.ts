import { createRouter, createWebHistory } from 'vue-router';
import PlanSpaceNavigationView from '@/views/PlanSpaceNavigationView.vue';
import StartView from '@/views/StartView.vue';
import VisualizationView from '@/views/VisualizationView.vue';
import PlanModificationView from '@/views/PlanModificationView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/start',
      name: 'start',
      component: StartView,
    },
    {
      path: '/plan-space-navigation',
      name: 'plan-space-navigation',
      component: PlanSpaceNavigationView,
    },
    {
      path: '/visualization',
      name: 'visualization',
      component: VisualizationView,
    },
    {
      path: '/plan-modification',
      name: 'plan-modification',
      component: PlanModificationView,
    },
  ],
});

export default router;
