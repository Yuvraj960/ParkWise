<template>
  <nav class="bg-gray-800 text-white px-6 py-3 flex justify-between items-center">
    <div class="flex items-center space-x-4">
      <router-link 
        :to="user ? '/dashboard' : '/'" 
        class="text-xl font-bold"
      >
        🏙️ ParkingApp
      </router-link>
      <template v-if="user">
      <router-link to="/lots" class="hover:text-gray-300">Parking Lots</router-link>
      <router-link v-if="user?.role === 'admin'" to="/dashboard" class="hover:text-gray-300">Dashboard</router-link>
      <router-link v-if="user?.role === 'user'" to="/reservations" class="hover:text-gray-300">My Bookings</router-link>
      <router-link v-if="user" to="/exports-reports" class="hover:text-gray-300">Reports</router-link>
      </template>
    </div>
    <div>
      <span v-if="user" class="mr-4">Hi, {{ user.username }}</span>
      <button v-if="user" @click="logout" class="bg-red-500 hover:bg-red-600 px-3 py-1 rounded">Logout</button>
      <router-link v-else to="/login" class="bg-blue-500 hover:bg-blue-600 px-3 py-1 rounded">Login</router-link>
    </div>
  </nav>
</template>

<script setup>
import { useUserStore } from '/src/store/user';
import { useRouter } from 'vue-router';
import { computed } from 'vue';

const userStore = useUserStore();
const router = useRouter();
const user = computed(() => userStore.user);

function logout() {
  userStore.logout();
  router.push('/');
}
</script>
