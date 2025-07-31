<template>
  <div class="p-6">
    <h1 class="text-xl font-bold mb-4">All Registered Users</h1>
    <div v-if="users.length === 0">No users found.</div>
    <table v-else class="min-w-full bg-white border">
      <thead>
        <tr class="bg-gray-100">
          <th class="border px-4 py-2">ID</th>
          <th class="border px-4 py-2">Username</th>
          <th class="border px-4 py-2">Email</th>
          <th class="border px-4 py-2">Phone</th>
          <th class="border px-4 py-2">Joined</th>
          <th class="border px-4 py-2">Reservations</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td class="border px-4 py-2">{{ u.id }}</td>
          <td class="border px-4 py-2">{{ u.username }}</td>
          <td class="border px-4 py-2">{{ u.email }}</td>
          <td class="border px-4 py-2">{{ u.phone }}</td>
          <td class="border px-4 py-2">{{ new Date(u.created_at).toLocaleDateString() }}</td>
          <td class="border px-4 py-2">{{ u.total_reservations }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import adminService from '/src/services/adminService';

export default {
  name: 'AdminUsers',
  setup() {
    const users = ref([]);

    const loadUsers = async () => {
      users.value = await adminService.fetchAllUsers();
    };

    onMounted(() => loadUsers());

    return { users };
  }
};
</script>

<style scoped></style>
