import { createRouter, createWebHistory } from 'vue-router'
import PlanPilotView from '@/views/PlanPilotView.vue'
import StartView from '@/views/StartView.vue'
import VisualizationView from '@/views/VisualizationView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/start',
      name: 'start',
      component: StartView,
    },
    {
      path: '/planpilot',
      name: 'planpilot',
      component: PlanPilotView,
    },
    {
      path: '/visualization',
      name: 'visualization',
      component: VisualizationView
    }
  ],
})

export default router