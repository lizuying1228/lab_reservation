import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('../views/LoginView.vue'), meta: { guest: true } },
    { path: '/register', component: () => import('../views/RegisterView.vue'), meta: { guest: true } },
    {
      path: '/', component: () => import('../layouts/MainLayout.vue'),
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: '工作台' } },
        { path: 'reservations', component: () => import('../views/ReservationsView.vue'), meta: { title: '预约管理' } },
        { path: 'labs', component: () => import('../views/LabsView.vue'), meta: { title: '实验室管理' } },
        { path: 'times', component: () => import('../views/ReservationTimesView.vue'), meta: { title: '预约时段' } },
        { path: 'students', component: () => import('../views/StudentsView.vue'), meta: { title: '学生管理' } },
        { path: 'labadmins', component: () => import('../views/LabAdminsView.vue'), meta: { title: '管理员管理' } },
        { path: 'users', component: () => import('../views/UsersView.vue'), meta: { title: '用户管理' } },
        { path: 'profile', component: () => import('../views/ProfileView.vue'), meta: { title: '个人资料' } }
      ]
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  const hasToken = !!localStorage.getItem('access')
  if (to.meta.guest) return hasToken ? '/dashboard' : true
  if (!hasToken) return '/login'
  if (!auth.profile) {
    try { await auth.loadIdentity() } catch { auth.clearLocal(); return '/login' }
  }
  if (to.path === '/users' && auth.role !== 'superuser') return '/dashboard'
  if (to.path === '/labadmins' && auth.role !== 'superuser') return '/dashboard'
  if (to.path === '/students' && auth.role === 'student') return '/dashboard'
  return true
})

export default router
