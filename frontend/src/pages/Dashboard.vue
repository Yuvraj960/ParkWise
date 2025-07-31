<template>
  <div class="p-6 max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold mb-4">
      {{ userStore.user?.role === 'admin' ? 'Admin Dashboard' : 'User Dashboard' }}
    </h1>
    
    <div v-if="userStore.user?.role === 'admin'" class="mb-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <router-link to="/admin/users" class="block bg-purple-100 p-4 rounded shadow hover:bg-purple-200">
          <h3 class="font-semibold text-purple-800">View All Users</h3>
          <p class="text-purple-600">Manage registered users</p>
        </router-link>
        <router-link to="/exports-reports" class="block bg-blue-100 p-4 rounded shadow hover:bg-blue-200">
          <h3 class="font-semibold text-blue-800">Admin Reports</h3>
          <p class="text-blue-600">Generate reports and manage cache</p>
        </router-link>
      </div>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <router-link to="/lots" class="block bg-green-100 p-4 rounded shadow hover:bg-green-200">
        <h3 class="font-semibold text-green-800">
          {{ userStore.user?.role === 'admin' ? 'Manage Parking Lots' : 'View Parking Lots' }}
        </h3>
        <p class="text-green-600">
          {{ userStore.user?.role === 'admin' ? 'Create, edit, and delete parking lots' : 'Browse available parking spots' }}
        </p>
      </router-link>
      
      <router-link to="/reservations" class="block bg-orange-100 p-4 rounded shadow hover:bg-orange-200">
        <h3 class="font-semibold text-orange-800">
          {{ userStore.user?.role === 'admin' ? 'All Reservations' : 'My Reservations' }}
        </h3>
        <p class="text-orange-600">
          {{ userStore.user?.role === 'admin' ? 'Monitor all user reservations' : 'View your booking history' }}
        </p>
      </router-link>
    </div>

    <div class="dashboard-charts">
      <DashboardCharts :user-role="userStore.user?.role || 'user'" />
    </div>
  </div>
</template>

<script>
import { useUserStore } from '/src/store/user';
import DashboardCharts from '/src/components/DashboardCharts.vue';

export default {
  name: 'Dashboard',
  components: {
    DashboardCharts
  },
  setup() {
    const userStore = useUserStore();
    return { userStore };
  }
};
</script>

<style scoped>
.dashboard-charts {
  margin-top: 2rem;
}
</style>