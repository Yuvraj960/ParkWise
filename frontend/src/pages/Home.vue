<template>
  <div>
    <div v-if="user" class="p-6">
      <h1 class="text-2xl font-bold mb-4">Welcome back, {{ user.username }}!</h1>
      <p>You are already logged in. Redirecting...</p>
    </div>

    <div v-else class="text-center p-8">
      <h1 class="text-3xl font-bold mb-6">Welcome to Parking Lot App</h1>
      <div class="flex justify-center space-x-4">
        <router-link to="/login" class="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700">Login</router-link>
        <router-link to="/register"
          class="bg-green-600 text-white px-6 py-3 rounded hover:bg-green-700">Register</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useUserStore } from '/src/store/user';
import { onMounted, computed } from 'vue';

const userStore = useUserStore();
const router = useRouter();
const user = computed(() => userStore.user);

onMounted(() => {
  if (user.value) {
    router.push('/dashboard');
  }
});
</script>

<style scoped></style>
