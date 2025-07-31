<template>
  <div class="p-6 max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold mb-4">Book Parking Spot</h1>
    
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
      {{ error }}
    </div>
    
    <div v-if="lot" class="bg-white p-6 rounded-lg shadow">
      <h2 class="text-xl font-semibold mb-4">{{ lot.prime_location_name }}</h2>
      <p class="text-gray-600 mb-2">{{ lot.address }}</p>
      <p class="text-green-600 font-semibold mb-4">₹{{ lot.price }}/hour</p>
      <p class="mb-4">Available spots: {{ lot.available_spots }}/{{ lot.number_of_spots }}</p>
      
      <form @submit.prevent="bookSpot" class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-1">Vehicle Number</label>
          <input 
            v-model="vehicleNumber" 
            type="text" 
            required 
            class="w-full border rounded px-3 py-2"
            placeholder="Enter your vehicle number"
          >
        </div>
        
        <button 
          type="submit" 
          :disabled="loading || lot.available_spots === 0"
          class="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {{ loading ? 'Booking...' : 'Book Spot' }}
        </button>
        
        <button 
          type="button"
          @click="router.push('/lots')"
          class="w-full bg-gray-500 text-white py-2 rounded hover:bg-gray-600"
        >
          Back to Lots
        </button>
      </form>
    </div>
    
    <div v-else-if="!error" class="text-center">
      <p>Loading lot details...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '/src/store/user';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const lot = ref(null);
const vehicleNumber = ref('');
const loading = ref(false);
const error = ref('');

const loadLotDetails = async () => {
  try {
    const response = await axios.get('/api/parking-lots', {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });
    
    const lotId = parseInt(route.params.lotId);
    lot.value = response.data.find(l => l.id === lotId);
    
    if (!lot.value) {
      error.value = 'Parking lot not found';
      setTimeout(() => router.push('/lots'), 2000);
    }
  } catch (err) {
    console.error('Error loading lot details:', err);
    error.value = 'Failed to load lot details';
    setTimeout(() => router.push('/lots'), 2000);
  }
};

const bookSpot = async () => {
  if (!vehicleNumber.value.trim()) {
    error.value = 'Please enter vehicle number';
    return;
  }
  
  if (lot.value.available_spots === 0) {
    error.value = 'No available spots';
    return;
  }
  
  loading.value = true;
  error.value = '';
  
  try {
    const response = await axios.post('/api/reserve-spot', {
      lot_id: lot.value.id,
      vehicle_number: vehicleNumber.value.trim()
    }, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });
    
    alert(`Spot booked successfully!\nLot: ${response.data.lot_name}\nSpot: ${response.data.spot_number}\nInitial Cost: ₹${response.data.initial_cost}`);
    router.push('/reservations');
  } catch (err) {
    console.error('Booking error:', err);
    error.value = err.response?.data?.message || 'Failed to book spot';
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadLotDetails();
});
</script>
