<template>
  <div class="charts-container">
    <div v-if="userRole === 'admin'" class="admin-charts">
      <h2 class="text-xl font-bold mb-4">Admin Statistics</h2>
      
      <div class="chart-section mb-6">
        <h3 class="text-lg font-semibold mb-2">Monthly Revenue</h3>
        <div class="chart-wrapper">
          <canvas ref="revenueChart"></canvas>
        </div>
      </div>
      
      <div class="chart-section mb-6">
        <h3 class="text-lg font-semibold mb-2">Parking Lot Utilization</h3>
        <div class="chart-wrapper">
          <canvas ref="utilizationChart"></canvas>
        </div>
      </div>
      
      <div class="chart-section mb-6">
        <h3 class="text-lg font-semibold mb-2">Daily Reservations (Last 7 Days)</h3>
        <div class="chart-wrapper">
          <canvas ref="trendsChart"></canvas>
        </div>
      </div>
    </div>
    
    <div v-else class="user-charts">
      <h2 class="text-xl font-bold mb-4">Your Parking Statistics</h2>
      
      <div class="chart-section mb-6">
        <h3 class="text-lg font-semibold mb-2">Monthly Spending</h3>
        <div class="chart-wrapper">
          <canvas ref="userSpendingChart"></canvas>
        </div>
      </div>
      
      <div class="chart-section mb-6">
        <h3 class="text-lg font-semibold mb-2">Parking Duration Distribution</h3>
        <div class="chart-wrapper">
          <canvas ref="userDurationChart"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import {
  Chart,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  BarController,
  LineController,
  DoughnutController,
  PieController,
  Filler,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import axios from 'axios';
import { useUserStore } from '/src/store/user';

Chart.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  BarController,
  LineController,
  DoughnutController,
  PieController,
  Filler,
  Title,
  Tooltip,
  Legend
);

const props = defineProps({
  userRole: {
    type: String,
    required: true
  }
});

const userStore = useUserStore();

const revenueChart = ref(null);
const utilizationChart = ref(null);
const trendsChart = ref(null);
const userSpendingChart = ref(null);
const userDurationChart = ref(null);

let revenueChartInstance = null;
let utilizationChartInstance = null;
let trendsChartInstance = null;
let userSpendingChartInstance = null;
let userDurationChartInstance = null;

const createRevenueChart = (data) => {
  const ctx = revenueChart.value?.getContext('2d');
  if (!ctx) return;
  
  revenueChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.months,
      datasets: [{
        label: 'Revenue (₹)',
        data: data.revenue,
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Monthly Revenue Overview'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return '₹' + value.toLocaleString();
            }
          }
        }
      }
    }
  });
};

const createUtilizationChart = (data) => {
  const ctx = utilizationChart.value?.getContext('2d');
  if (!ctx) return;
  
  utilizationChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.lots,
      datasets: [{
        label: 'Utilization %',
        data: data.utilization,
        backgroundColor: [
          'rgba(239, 68, 68, 0.5)',
          'rgba(34, 197, 94, 0.5)',
          'rgba(59, 130, 246, 0.5)',
          'rgba(168, 85, 247, 0.5)',
          'rgba(245, 158, 11, 0.5)'
        ],
        borderColor: [
          'rgb(239, 68, 68)',
          'rgb(34, 197, 94)',
          'rgb(59, 130, 246)',
          'rgb(168, 85, 247)',
          'rgb(245, 158, 11)'
        ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Parking Lot Utilization'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return context.label + ': ' + context.parsed + '%';
            }
          }
        }
      }
    }
  });
};

const createTrendsChart = (data) => {
  const ctx = trendsChart.value?.getContext('2d');
  if (!ctx) return;
  
  trendsChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.days,
      datasets: [{
        label: 'Reservations',
        data: data.reservations,
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Daily Reservation Trends'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      }
    }
  });
};

const createUserSpendingChart = (data) => {
  const ctx = userSpendingChart.value?.getContext('2d');
  if (!ctx) return;
  
  userSpendingChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.months,
      datasets: [{
        label: 'Spending (₹)',
        data: data.spending,
        backgroundColor: 'rgba(168, 85, 247, 0.1)',
        borderColor: 'rgb(168, 85, 247)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Your Monthly Spending'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function(value) {
              return '₹' + value.toLocaleString();
            }
          }
        }
      }
    }
  });
};

const createUserDurationChart = (data) => {
  const ctx = userDurationChart.value?.getContext('2d');
  if (!ctx) return;
  
  const totalDuration = data.durations.reduce((a, b) => a + b, 0);
  
  let chartData, chartLabels;
  if (totalDuration === 0) {
    chartData = [1];
    chartLabels = ['No parking history available'];
  } else {
    chartData = data.durations;
    chartLabels = ['< 1 hour', '1-3 hours', '3-6 hours', '6+ hours'];
  }
  
  userDurationChartInstance = new Chart(ctx, {
    type: 'pie',
    data: {
      labels: chartLabels,
      datasets: [{
        data: chartData,
        backgroundColor: totalDuration === 0 ? 
          ['rgba(156, 163, 175, 0.5)'] : 
          [
            'rgba(245, 158, 11, 0.5)',
            'rgba(59, 130, 246, 0.5)',
            'rgba(34, 197, 94, 0.5)',
            'rgba(239, 68, 68, 0.5)'
          ],
        borderColor: totalDuration === 0 ? 
          ['rgb(156, 163, 175)'] :
          [
            'rgb(245, 158, 11)',
            'rgb(59, 130, 246)',
            'rgb(34, 197, 94)',
            'rgb(239, 68, 68)'
          ],
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Parking Duration Distribution'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              if (totalDuration === 0) {
                return 'No parking history';
              }
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((context.parsed / total) * 100).toFixed(1);
              return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
            }
          }
        }
      }
    }
  });
};

const loadAdminStatistics = async () => {
  try {
    const response = await axios.get('/api/admin/statistics', {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });
    
    const data = response.data;
    // console.log('Admin statistics data:', data); // Debug log
    
    createRevenueChart(data.revenue);
    createUtilizationChart(data.utilization);
    createTrendsChart(data.trends);
  } catch (error) {
    console.error('Failed to load admin statistics:', error);
  }
};

const loadUserStatistics = async () => {
  try {
    const response = await axios.get('/api/user/statistics', {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    });
    
    const data = response.data;
    
    createUserSpendingChart(data.spending);
    createUserDurationChart(data.duration);
  } catch (error) {
    console.error('Failed to load user statistics:', error);
  }
};

onMounted(() => {
  if (props.userRole === 'admin') {
    loadAdminStatistics();
  } else {
    loadUserStatistics();
  }
});

onUnmounted(() => {
  // Cleanup chart instances
  if (revenueChartInstance) revenueChartInstance.destroy();
  if (utilizationChartInstance) utilizationChartInstance.destroy();
  if (trendsChartInstance) trendsChartInstance.destroy();
  if (userSpendingChartInstance) userSpendingChartInstance.destroy();
  if (userDurationChartInstance) userDurationChartInstance.destroy();
});
</script>

<style scoped>
.charts-container {
  padding: 20px;
}

.chart-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.chart-wrapper {
  position: relative;
  height: 300px;
  width: 100%;
}

.admin-charts,
.user-charts {
  max-width: 1200px;
  margin: 0 auto;
}
</style>