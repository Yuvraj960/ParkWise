<template>
  <div class="lot-container">
    <h1 class="heading">Parking Lots</h1>

    <div v-if="userStore.user.role === 'admin'" class="admin-form">
      <div class="form-toggle">
        <button @click="startAdd" class="form-button">Add New Lot</button>
      </div>

      <div v-if="isEditing || showForm" class="lot-form">
        <h2>{{ isEditing ? 'Edit Parking Lot' : 'Add Parking Lot' }}</h2>
        <form @submit.prevent="submitLot">
          <input v-model="form.prime_location_name" placeholder="Location Name" required />
          <input v-model.number="form.price" placeholder="Price" type="number" required />
          <input v-model="form.address" placeholder="Address" required />
          <input v-model="form.pin_code" placeholder="Pin Code" required />
          <input v-model.number="form.number_of_spots" placeholder="Number of Spots" type="number" required />

          <div class="form-actions">
            <button type="submit" class="form-button">{{ isEditing ? 'Update' : 'Add' }}</button>
            <button type="button" class="bg-red-500 text-white py-2 px-4 rounded" @click="cancelForm">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <div class="lots-list">
      <div v-for="lot in lots" :key="lot.id" class="lot-item">
        <h2>{{ lot.prime_location_name }}</h2>
        <p>Price: ₹{{ lot.price }}</p>
        <p>Address: {{ lot.address }}</p>
        <p>Pin: {{ lot.pin_code }}</p>
        <p>Available: {{ lot.available_spots }} / {{ lot.number_of_spots }}</p>

        <button class="bg-purple-500 text-white py-1 px-2 mx-2 my-2 rounded" v-if="userStore.user.role === 'user'" @click="book(lot.id)">Book</button>
        <button class="bg-purple-500 text-white py-1 px-2 mx-2 my-2 rounded" v-if="userStore.user.role === 'admin'" @click="startEdit(lot)">Edit</button>
        <button class="bg-red-500 text-white py-1 px-2 mx-2 my-2 rounded" v-if="userStore.user.role === 'admin'" @click="deleteLot(lot.id)">Delete</button>
        <button class="bg-green-500 text-white py-1 px-2 mx-2 my-2 rounded" v-if="userStore.user.role === 'admin'" @click="goToReservations(lot.id)">View Reservations</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useUserStore } from '/src/store/user';
import lotService from '/src/services/lotService';
import { useRouter } from 'vue-router';

export default {
  name: 'ParkingLots',
  setup() {
    const userStore = useUserStore();
    const lots = ref([]);
    const form = ref({
      prime_location_name: '',
      price: '',
      address: '',
      pin_code: '',
      number_of_spots: '',
      id: null
    });
    const showForm = ref(false);
    const isEditing = ref(false);
    const router = useRouter();

    const loadLots = async () => {
      lots.value = await lotService.fetchLots();
    };

    const submitLot = async () => {
      if (isEditing.value) {
        await lotService.updateLot(form.value.id, form.value);
      } else {
        await lotService.createLot(form.value);
      }
      cancelForm();
      await loadLots();
    };

    const cancelForm = () => {
      showForm.value = false;
      isEditing.value = false;
      form.value = { prime_location_name: '', price: 0, address: '', pin_code: '', number_of_spots: 1, id: null };
    };

    const startAdd = () => {
      showForm.value = true;
    };

    const startEdit = (lot) => {
      form.value = { ...lot };
      isEditing.value = true;
      showForm.value = true;
    };

    const deleteLot = async (id) => {
      try {
        await lotService.deleteLot(id);
        await loadLots();
      } catch (err) {
        alert(err.response?.data?.message || 'Failed to delete parking lot');
      }
    };

    const book = (lotId) => {
      router.push(`/book/${lotId}`);
    };

    const goToReservations = (lotId) => {
      router.push(`/admin/reservations/${lotId}`);
    };

    onMounted(loadLots);
    return {
      lots,
      showForm,
      form,
      userStore,
      submitLot,
      book,
      goToReservations,
      startEdit,
      cancelForm,
      isEditing,
      startAdd,
      deleteLot
    };
  }
};
</script>

<style scoped>
.lot-container {
  display: flex;
  flex-direction: row;
  gap: 32px;
  padding: 24px;
  flex-wrap: wrap;
}

.admin-form {
  flex: 1;
  min-width: 300px;
}

.lot-form {
  margin-top: 16px;
}

.lots-list {
  flex: 2;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.lot-item {
  border: 1px solid #ccc;
  padding: 12px;
  border-radius: 6px;
  width: 100%;
  max-width: 320px;
}

.form-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.form-button {
  padding: 6px 12px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
