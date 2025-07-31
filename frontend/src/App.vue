<template>
  <div class="min-h-screen bg-gray-50">
    <Navbar v-if="showNavbar" />
    <router-view />
  </div>
</template>

<script setup>
import Navbar from '/src/components/Navbar.vue';
import { useRoute } from 'vue-router';
import { computed } from 'vue';

const route = useRoute();

const hideNavbarOn = ['/login', '/register'];
const showNavbar = computed(() => !hideNavbarOn.includes(route.path));
</script>

<style scoped>
body {
  font-family: 'Inter', sans-serif;
}
</style>
