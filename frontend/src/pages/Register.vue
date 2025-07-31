<template>
  <div class="max-w-md mx-auto mt-12">
    <h2 class="text-2xl font-bold mb-6 text-center">Register</h2>
    <form @submit.prevent="handleRegister" class="space-y-4">
      <input v-model="form.username" type="text" placeholder="Username" class="w-full p-2 border rounded" required />
      <input v-model="form.email" type="email" placeholder="Email" class="w-full p-2 border rounded" required />
      <input v-model="form.phone" type="text" placeholder="Phone (optional)" class="w-full p-2 border rounded" />
      <input v-model="form.password" type="password" placeholder="Password" class="w-full p-2 border rounded" required />
      <button type="submit" class="w-full bg-green-500 text-white p-2 rounded">Register</button>
    </form>
    <p class="text-sm text-center mt-4">
      Already have an account?
      <router-link to="/login" class="text-blue-500">Login</router-link>
    </p>
  </div>
</template>

<script>
import { useRouter } from 'vue-router';
import { useUserStore } from '/src/store/user';
import { reactive } from 'vue';

export default {
  name: 'Register',
  setup() {
    const router = useRouter();
    const userStore = useUserStore();
    const form = reactive({ username: '', email: '', phone: '', password: '' });

    const handleRegister = async () => {
      const success = await userStore.register(form);
      if (success) router.push('/login');
    };

    return { form, handleRegister };
  }
};
</script>

<style scoped></style>
