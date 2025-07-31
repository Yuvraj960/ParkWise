<template>
  <div class="max-w-md mx-auto mt-12">
    <h2 class="text-2xl font-bold mb-6 text-center">Login</h2>
    <form @submit.prevent="handleLogin" class="space-y-4">
      <input v-model="form.username" type="text" placeholder="Username" class="w-full p-2 border rounded" required />
      <input v-model="form.password" type="password" placeholder="Password" class="w-full p-2 border rounded"
        required />
      <button type="submit" class="w-full bg-blue-500 text-white p-2 rounded">Login</button>
    </form>
    <p class="text-sm text-center mt-4">
      Don't have an account?
      <router-link to="/register" class="text-blue-500">Register</router-link>
    </p>
  </div>
</template>

<script>
import { useRouter } from 'vue-router';
import { useUserStore } from '/src/store/user';
import { reactive } from 'vue';

export default {
  name: 'Login',
  setup() {
    const router = useRouter();
    const userStore = useUserStore();
    const form = reactive({ username: '', password: '' });

    const handleLogin = async () => {
      const success = await userStore.login(form);
      if (success) router.push('/dashboard');
    };

    return { form, handleLogin };
  }
};
</script>

<style scoped></style>
