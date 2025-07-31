<template>
  <div class="all-reservations">
    <h1>{{ userStore.user.role === 'admin' ? 'All Reservations' : 'Your Reservations' }}</h1>
    <div v-if="loading">Loading reservations...</div>
    <div v-else>
      <div v-if="userStore.user.role === 'user'" class="summary-cards mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-blue-100 p-4 rounded-lg">
          <h3 class="font-semibold text-blue-800">Total Reservations</h3>
          <p class="text-2xl font-bold text-blue-600">{{ reservations.length }}</p>
        </div>
        <div class="bg-green-100 p-4 rounded-lg">
          <h3 class="font-semibold text-green-800">Total Spent</h3>
          <p class="text-2xl font-bold text-green-600">₹{{ totalSpent.toFixed(2) }}</p>
        </div>
        <div class="bg-purple-100 p-4 rounded-lg">
          <h3 class="font-semibold text-purple-800">Total Hours</h3>
          <p class="text-2xl font-bold text-purple-600">{{ totalHours.toFixed(1) }}h</p>
        </div>
        <div class="bg-indigo-100 p-4 rounded-lg">
          <h3 class="font-semibold text-indigo-800">Avg. Session</h3>
          <p class="text-2xl font-bold text-indigo-600">{{ averageSession.toFixed(1) }}h</p>
        </div>
      </div>

      <div v-if="reservations.length === 0" class="text-center py-8">
        <p class="text-gray-500 text-lg">No reservations found.</p>
        <router-link to="/lots" class="mt-4 inline-block bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
          Book a Parking Spot
        </router-link>
      </div>

      <table v-else class="reservation-table">
        <thead>
          <tr>
            <th v-if="userStore.user.role === 'admin'">User</th>
            <th>Lot</th>
            <th>Spot</th>
            <th>Vehicle #</th>
            <th>Start</th>
            <th>End</th>
            <th>Duration</th>
            <th>Cost</th>
            <th>Status</th>
            <th v-if="userStore.user.role === 'user'">Action</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="res in reservations" :key="res.id">
            <tr>
              <td v-if="userStore.user.role === 'admin'">{{ res.username }}</td>
              <td>{{ res.lot_name || res.lot }}</td>
              <td>{{ res.spot_number }}</td>
              <td>{{ res.vehicle_number }}</td>
              <td>{{ formatDate(res.parking_timestamp) }}</td>
              <td>{{ formatDate(res.leaving_timestamp) }}</td>
              <td>{{ res.cost_breakdown?.total_hours?.toFixed(1) || '0' }}h</td>
              <td class="font-semibold">₹{{ (res.cost_breakdown?.total_cost || res.parking_cost || 0).toFixed(2) }}</td>
              <td>
                <span :class="['badge', res.status === 'active' ? 'red' : 'green']">
                  {{ res.status }}
                </span>
              </td>
              <td v-if="userStore.user.role === 'user' && res.status === 'active'">
                <button @click="release(res.id)"
                  class="bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600">
                  Release
                </button>
              </td>
              <td v-else-if="userStore.user.role === 'user'">
                <span class="text-gray-400">-</span>
              </td>
              <td>
                <button @click="toggleDetails(res.id)" class="bg-blue-500 text-white px-2 py-1 rounded text-sm hover:bg-blue-600">
                  {{ expandedDetails[res.id] ? 'Hide' : 'Show' }}
                </button>
              </td>
            </tr>

            <tr v-show="expandedDetails[res.id]" class="breakdown-row">
              <td :colspan="getColspan()" class="bg-gray-50 p-4">
                <CostSummary :breakdown="res.cost_breakdown || {}" :isActive="res.status === 'active'" />
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import { useUserStore } from '/src/store/user';
import CostSummary from '/src/components/CostSummary.vue';

const reservations = ref([]);
const loading = ref(true);
const userStore = useUserStore();
const expandedDetails = ref({});

const formatDate = (dt) => dt ? new Date(dt).toLocaleString() : '-';

const totalSpent = computed(() => {
  return reservations.value.reduce((sum, res) => {
    return sum + (res.cost_breakdown?.total_cost || res.parking_cost || 0);
  }, 0);
});

const totalHours = computed(() => {
  return reservations.value.reduce((sum, res) => {
    return sum + (res.cost_breakdown?.total_hours || 0);
  }, 0);
});

const averageSession = computed(() => {
  const completedReservations = reservations.value.filter(res => res.status === 'completed');
  if (completedReservations.length === 0) return 0;
  
  const totalHours = completedReservations.reduce((sum, res) => {
    return sum + (res.cost_breakdown?.total_hours || 0);
  }, 0);
  
  return totalHours / completedReservations.length;
});

const getColspan = () => {
  return userStore.user.role === 'admin' ? 11 : 10;
};

const toggleDetails = (reservationId) => {
  expandedDetails.value[reservationId] = !expandedDetails.value[reservationId];
};

const release = async (reservationId) => {
  if (!confirm('Are you sure you want to release this parking spot?')) {
    return;
  }
  
  try {
    const response = await axios.put(`/api/release-spot/${reservationId}`, {}, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });

    if (response.data.cost_breakdown) {
      alert(`Spot released successfully!\nTotal Cost: ₹${response.data.cost_breakdown.total_cost}\nDuration: ${response.data.cost_breakdown.total_hours.toFixed(2)} hours`);
    } else {
      alert('Spot released successfully');
    }

    await loadReservations();
  } catch (err) {
    console.error('Release error:', err);
    alert(err.response?.data?.message || 'Failed to release spot');
  }
};

const loadReservations = async () => {
  try {
    const endpoint = userStore.user.role === 'admin'
      ? '/api/all-reservations'
      : '/api/user-reservations';

    const res = await axios.get(endpoint, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });
    
    reservations.value = res.data;
    console.log('Loaded reservations:', res.data); // Debug log
  } catch (err) {
    console.error('Failed to fetch reservations', err);
    alert('Failed to load reservations. Please try again.');
  } finally {
    loading.value = false;
  }
};

onMounted(loadReservations);
</script>

<style scoped>
.all-reservations {
  padding: 24px;
}

.reservation-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 16px;
}

.reservation-table th,
.reservation-table td {
  padding: 10px;
  border: 1px solid #ccc;
  text-align: center;
}

.reservation-table th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.breakdown-row {
  background-color: #f8f9fa;
}

.cost-breakdown {
  text-align: left;
}

.badge {
  padding: 4px 8px;
  border-radius: 4px;
  color: white;
  font-weight: bold;
}

.badge.red {
  background-color: #e11d48;
}

.badge.green {
  background-color: #10b981;
}

.summary-cards {
  margin-bottom: 1.5rem;
}
</style>