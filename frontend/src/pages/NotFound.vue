<template>
  <div class="flex flex-col items-center justify-center h-screen text-center">
    <h1 class="text-4xl font-bold mb-2">404</h1>
    <p class="text-lg text-gray-600 mb-4">Page not found</p>
    <router-link to="/" class="text-blue-500 underline">Go Home</router-link>
  </div>
</template>

<script>
export default {
  name: 'NotFound'
};
</script>

<style scoped></style>
