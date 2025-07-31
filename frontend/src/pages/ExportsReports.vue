<template>
  <div class="exports-reports p-6 max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">{{ userStore.user?.role === 'admin' ? 'Admin Reports & Exports' : 'Export Your Data' }}</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- User Data Export - Available to all users -->
      <div class="card p-6 border rounded-lg bg-white shadow">
        <h2 class="text-xl font-semibold mb-4">Export Your Data</h2>
        <p class="text-gray-600 mb-4">
          Download your parking history as a CSV file
        </p>
        <button @click="exportUserData" :disabled="isExporting"
                class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50">
          <span v-if="isExporting">Exporting...</span>
          <span v-else>Export CSV</span>
        </button>
      </div>

      <!-- Admin Controls - Only visible to admins -->
      <div v-if="userStore.user?.role === 'admin'" class="card p-6 border rounded-lg bg-white shadow">
        <h2 class="text-xl font-semibold mb-4">Admin Controls</h2>
        
        <div class="space-y-3">
          <button @click="triggerReminders" :disabled="isProcessing"
                  class="w-full bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 disabled:opacity-50">
            Send Daily Reminders
          </button>
          
          <button @click="generateReports" :disabled="isProcessing"
                  class="w-full bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 disabled:opacity-50">
            Generate Monthly Reports
          </button>
        </div>
      </div>

      <!-- Redis Cache Status - Only visible to admins -->
      <div v-if="userStore.user?.role === 'admin'" class="card p-6 border rounded-lg bg-white shadow">
        <h2 class="text-xl font-semibold mb-4">Cache Status</h2>
        <div class="space-y-2">
          <div class="flex justify-between">
            <span>Parking Lots Cache:</span>
            <span :class="cacheStatus.parkingLots ? 'text-green-600' : 'text-red-600'">
              {{ cacheStatus.parkingLots ? 'Active' : 'Expired' }}
            </span>
          </div>
          <button @click="clearCache" 
                  class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 text-sm">
            Clear Cache
          </button>
        </div>
      </div>

      <!-- Task Monitor - Full width, user-specific -->
      <div :class="userStore.user?.role === 'admin' ? 'md:col-span-2' : 'md:col-span-1'">
        <TaskMonitor ref="taskMonitor" :user-role="userStore.user?.role" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from '/src/store/user';
import celeryService from '/src/services/celeryService';
import TaskMonitor from '/src/components/TaskMonitor.vue';

const userStore = useUserStore();
const taskMonitor = ref(null);
const isExporting = ref(false);
const isProcessing = ref(false);

const cacheStatus = ref({
  parkingLots: false
});

const exportUserData = async () => {
  try {
    isExporting.value = true;
    const result = await celeryService.exportUserDataCSV();
    
    taskMonitor.value?.addTask({
      task_id: result.task_id,
      name: 'CSV Export',
      user_role: userStore.user?.role,
      user_id: userStore.user?.id
    });
    
    alert('Export started! Check the task monitor for progress.');
  } catch (err) {
    console.error('Export error:', err);
    alert('Failed to start export. Please check if you are logged in.');
  } finally {
    isExporting.value = false;
  }
};

const triggerReminders = async () => {
  if (userStore.user?.role !== 'admin') {
    alert('Admin access required');
    return;
  }
  
  try {
    isProcessing.value = true;
    const result = await celeryService.triggerDailyReminders();
    
    taskMonitor.value?.addTask({
      task_id: result.task_id,
      name: 'Daily Reminders',
      user_role: 'admin',
      user_id: userStore.user?.id
    });
    
    alert('Reminders task started!');
  } catch (err) {
    console.error('Reminders error:', err);
    alert('Failed to trigger reminders. Admin access required.');
  } finally {
    isProcessing.value = false;
  }
};

const generateReports = async () => {
  if (userStore.user?.role !== 'admin') {
    alert('Admin access required');
    return;
  }
  
  try {
    isProcessing.value = true;
    const result = await celeryService.generateMonthlyReports();
    
    taskMonitor.value?.addTask({
      task_id: result.task_id,
      name: 'Monthly Reports',
      user_role: 'admin',
      user_id: userStore.user?.id
    });
    
    alert('Report generation started!');
  } catch (err) {
    console.error('Reports error:', err);
    alert('Failed to generate reports. Admin access required.');
  } finally {
    isProcessing.value = false;
  }
};

const clearCache = async () => {
  if (userStore.user?.role !== 'admin') {
    alert('Admin access required');
    return;
  }
  
  try {
    await celeryService.clearCache();
    alert('Cache cleared successfully');
    checkCacheStatus();
  } catch (err) {
    console.error('Clear cache error:', err);
    alert('Failed to clear cache. Admin access required.');
  }
};

const checkCacheStatus = async () => {
  if (userStore.user?.role !== 'admin') {
    return;
  }
  
  try {
    const status = await celeryService.getCacheStatus();
    cacheStatus.value = status;
  } catch (err) {
    console.error('Failed to check cache status:', err);
  }
};

onMounted(() => {
  if (userStore.user?.role === 'admin') {
    checkCacheStatus();
  }
});
</script>