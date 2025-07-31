import { createRouter, createWebHistory } from 'vue-router';
import { useUserStore } from '/src/store/user';

import Home from '/src/pages/Home.vue';
import Login from '/src/pages/Login.vue';
import Register from '/src/pages/Register.vue';
import Dashboard from '/src/pages/Dashboard.vue';
import ParkingLots from '/src/pages/ParkingLots.vue';
import Reservations from '/src/pages/Reservations.vue';
import LotReservations from '/src/pages/LotReservations.vue';
import AdminUsers from '/src/pages/AdminUsers.vue';
import NotFound from '/src/pages/NotFound.vue';
import ExportsReports from '/src/pages/ExportsReports.vue';
import Bookings from '/src/pages/Bookings.vue';
import Unauthorized from '/src/pages/Unauthorized.vue';

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { 
    path: '/dashboard', 
    name: 'Dashboard', 
    component: Dashboard, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/lots', 
    name: 'ParkingLots', 
    component: ParkingLots, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/reservations', 
    name: 'Reservations', 
    component: Reservations, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/admin/users', 
    name: 'AdminUsers', 
    component: AdminUsers, 
    meta: { requiresAuth: true, role: 'admin' } 
  },
  { 
    path: '/exports-reports', 
    name: 'ExportsReports', 
    component: ExportsReports, 
    meta: { requiresAuth: true } 
  },
  {
    path: '/book/:lotId',
    name: 'Bookings',
    component: Bookings,
    meta: { requiresAuth: true, role: 'user' }
  },
  {
    path: '/admin/reservations/:lotId',
    name: 'LotReservations',
    component: LotReservations,
    meta: { requiresAuth: true, role: 'admin' }
  },
  {
    path: '/unauthorized',
    name: 'Unauthorized',
    component: Unauthorized
  },
  { 
    path: '/:pathMatch(.*)*', 
    name: 'NotFound', 
    component: NotFound 
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const userStore = useUserStore();

  if (to.meta.requiresAuth && !userStore.token) {
    next('/login');
  } else if (to.meta.role && userStore.user?.role !== to.meta.role) {
    next('/unauthorized');
  } else {
    next();
  }
});

export default router;