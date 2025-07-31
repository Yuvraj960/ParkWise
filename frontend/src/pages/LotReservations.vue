<template>
  <div class="lot-reservations">
    <h1>Parking Lot #{{ lotId }}</h1>
    <p class="summary">Occupied: {{ occupiedCount }} / {{ totalSpots }}</p>

    <div class="grid">
      <div v-for="spot in summary" :key="spot.spot_number"
        :class="['cell', spot.status === 'O' ? 'occupied' : 'available']">
        {{ spot.status }}
      </div>
    </div>

    <h2>Occupied Spot Details</h2>
    <table v-if="details.length" class="reservation-table">
      <thead>
        <tr>
          <th>User</th>
          <th>Spot</th>
          <th>Vehicle #</th>
          <th>Start</th>
          <th>End</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="res in details" :key="res.spot_number">
          <td>{{ res.username }}</td>
          <td>{{ res.spot_number }}</td>
          <td>{{ res.vehicle_number }}</td>
          <td>{{ formatDate(res.parking_timestamp) }}</td>
          <td>{{ formatDate(res.leaving_timestamp) || '-' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>No occupied spots currently.</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { useUserStore } from '/src/store/user';

const summary = ref([]);
const details = ref([]);
const lotId = useRoute().params.lotId;
const userStore = useUserStore();
const totalSpots = ref(0);
const occupiedCount = ref(0);

const formatDate = (dateStr) => dateStr ? new Date(dateStr).toLocaleString() : null;

onMounted(async () => {
  try {
    const res = await axios.get(`http://localhost:5000/api/reservations/${lotId}`, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });
    summary.value = res.data.summary;
    details.value = res.data.details;
    totalSpots.value = res.data.total_spots;
    occupiedCount.value = res.data.occupied_count;
  } catch (err) {
    console.error('Error loading reservations:', err);
  }
});
</script>

<style scoped>
.lot-reservations {
  padding: 24px;
}

.summary {
  font-weight: bold;
  margin-bottom: 12px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 40px);
  gap: 8px;
  margin-bottom: 24px;
}

.cell {
  width: 40px;
  height: 40px;
  text-align: center;
  line-height: 40px;
  border-radius: 4px;
  font-weight: bold;
  color: white;
}

.cell.occupied {
  background-color: #ef4444;
}

.cell.available {
  background-color: #22c55e;
}

.reservation-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
}

.reservation-table th,
.reservation-table td {
  border: 1px solid #ccc;
  padding: 8px;
  text-align: center;
}
</style>