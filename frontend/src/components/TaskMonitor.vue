<template>
  <div class="task-monitor p-4 border rounded-lg bg-gray-50">
    <h3 class="text-lg font-semibold mb-3">
      {{ userRole === 'admin' ? 'Admin Background Tasks' : 'Your Background Tasks' }}
    </h3>
    
    <div v-if="filteredTasks.length === 0" class="text-gray-500">
      No active tasks
    </div>

    <div v-for="task in filteredTasks" :key="task.id" class="task-item mb-3 p-3 bg-white rounded border">
      <div class="flex justify-between items-center">
        <div>
          <span class="font-medium">{{ task.name }}</span>
          <div class="text-sm text-gray-600">
            ID: {{ task.id.substring(0, 8) }}...
            <span v-if="userRole === 'admin'" class="ml-2 text-xs bg-gray-200 px-1 rounded">
              {{ task.user_role || 'system' }}
            </span>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <span :class="getStatusClass(task.status)" class="px-2 py-1 rounded text-xs font-medium">
            {{ task.status }}
          </span>
          <button v-if="task.status === 'PENDING'" @click="checkStatus(task.id)" 
                  class="text-blue-500 text-sm hover:underline">
            Refresh
          </button>
          <button v-if="task.status === 'SUCCESS' && task.downloadKey" 
                  @click="downloadFile(task.downloadKey)"
                  class="bg-green-500 text-white px-2 py-1 rounded text-xs hover:bg-green-600">
            Download
          </button>
          <button @click="removeTask(task.id)"
                  class="text-red-500 text-xs hover:underline">
            Remove
          </button>
        </div>
      </div>
      
      <div v-if="task.progress" class="mt-2">
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div class="bg-blue-600 h-2 rounded-full" :style="`width: ${task.progress}%`"></div>
        </div>
        <div class="text-xs text-gray-600 mt-1">{{ task.progress }}% complete</div>
      </div>
      
      <div v-if="task.error" class="mt-2 text-red-600 text-sm">
        Error: {{ task.error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useUserStore } from '/src/store/user';
import celeryService from '/src/services/celeryService';

const props = defineProps({
  userRole: {
    type: String,
    default: 'user'
  }
});

const userStore = useUserStore();
const tasks = ref([]);
let pollInterval = null;

// Filter tasks based on user role and user ID
const filteredTasks = computed(() => {
  const currentUserId = userStore.user?.id;
  
  return tasks.value.filter(task => {
    // Show task if it belongs to the current user
    if (task.user_id === currentUserId) {
      return true;
    }
    
    // For admin users, also show admin-specific tasks
    if (props.userRole === 'admin' && task.user_role === 'admin') {
      return true;
    }
    
    // For backward compatibility, show tasks without user_id if they're admin tasks
    if (props.userRole === 'admin' && !task.user_id && ['Daily Reminders', 'Monthly Reports'].includes(task.name)) {
      return true;
    }
    
    return false;
  });
});

const getStorageKey = () => {
  const userId = userStore.user?.id || 'anonymous';
  const role = props.userRole || 'user';
  return `activeTasks_${role}_${userId}`;
};

const getStatusClass = (status) => {
  switch (status) {
    case 'PENDING': return 'bg-yellow-100 text-yellow-800';
    case 'SUCCESS': return 'bg-green-100 text-green-800';
    case 'FAILURE': return 'bg-red-100 text-red-800';
    case 'PROGRESS': return 'bg-blue-100 text-blue-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

const addTask = (taskData) => {
  const newTask = {
    id: taskData.task_id,
    name: taskData.name || 'Background Task',
    status: 'PENDING',
    progress: 0,
    downloadKey: null,
    user_role: taskData.user_role || props.userRole,
    user_id: taskData.user_id || userStore.user?.id,
    timestamp: new Date().toISOString()
  };
  
  tasks.value.push(newTask);
  saveTasksToStorage();
  startPolling();
};

const removeTask = (taskId) => {
  tasks.value = tasks.value.filter(t => t.id !== taskId);
  saveTasksToStorage();
  
  if (filteredTasks.value.length === 0) {
    stopPolling();
  }
};

const checkStatus = async (taskId) => {
  try {
    const result = await celeryService.getTaskStatus(taskId);
    const taskIndex = tasks.value.findIndex(t => t.id === taskId);
    
    if (taskIndex !== -1) {
      tasks.value[taskIndex].status = result.status;
      tasks.value[taskIndex].progress = result.progress || 0;
      
      if (result.status === 'SUCCESS' && result.result?.download_key) {
        tasks.value[taskIndex].downloadKey = result.result.download_key;
      }
      
      if (result.status === 'FAILURE') {
        tasks.value[taskIndex].error = result.error;
      }
      
      saveTasksToStorage();
    }
  } catch (err) {
    console.error('Failed to check task status:', err);
  }
};

const downloadFile = async (downloadKey) => {
  try {
    const blob = await celeryService.downloadCSV(downloadKey);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `parking_data_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert('Failed to download file');
  }
};

const saveTasksToStorage = () => {
  localStorage.setItem(getStorageKey(), JSON.stringify(tasks.value));
};

const loadTasksFromStorage = () => {
  const storageKey = getStorageKey();
  const savedTasks = localStorage.getItem(storageKey);
  
  if (savedTasks) {
    try {
      const parsedTasks = JSON.parse(savedTasks);
      
      // Filter tasks older than 24 hours
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      tasks.value = parsedTasks.filter(task => {
        if (!task.timestamp) return true; // Keep tasks without timestamp for backward compatibility
        return new Date(task.timestamp) > oneDayAgo;
      });
      
      saveTasksToStorage();
    } catch (e) {
      console.error('Failed to parse saved tasks:', e);
      tasks.value = [];
    }
  }
};

const startPolling = () => {
  if (pollInterval) return;
  
  pollInterval = setInterval(() => {
    const pendingTasks = filteredTasks.value.filter(t => t.status === 'PENDING' || t.status === 'PROGRESS');
    
    if (pendingTasks.length === 0) {
      stopPolling();
      return;
    }
    
    pendingTasks.forEach(task => {
      checkStatus(task.id);
    });
  }, 2000);
};

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
};

onMounted(() => {
  loadTasksFromStorage();
  
  // Start polling if there are pending tasks
  if (filteredTasks.value.some(t => t.status === 'PENDING' || t.status === 'PROGRESS')) {
    startPolling();
  }
});

onUnmounted(() => {
  stopPolling();
  saveTasksToStorage();
});

defineExpose({ addTask });
</script>