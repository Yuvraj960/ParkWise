<template>
  <div class="cost-summary bg-white p-6 rounded-lg shadow-md">
    <h3 class="text-lg font-semibold mb-4 text-gray-800">Cost Summary</h3>
    
    <div class="space-y-3">
      <div class="flex justify-between py-2 border-b border-gray-200">
        <span class="text-gray-600">Base Cost (1 hour):</span>
        <span class="font-semibold">₹{{ breakdown.base_cost?.toFixed(2) || '0.00' }}</span>
      </div>
      
      <div class="flex justify-between py-2 border-b border-gray-200">
        <span class="text-gray-600">Hourly Rate:</span>
        <span class="font-semibold">₹{{ breakdown.hourly_rate?.toFixed(2) || '0.00' }}/hr</span>
      </div>
      
      <div class="flex justify-between py-2 border-b border-gray-200">
        <span class="text-gray-600">Total Duration:</span>
        <span class="font-semibold">{{ breakdown.total_hours?.toFixed(2) || '0.00' }} hours</span>
      </div>
      
      <div v-if="breakdown.additional_hours > 0" class="flex justify-between py-2 border-b border-gray-200">
        <span class="text-gray-600">Additional Hours:</span>
        <span class="font-semibold">{{ breakdown.additional_hours?.toFixed(2) }} hrs</span>
      </div>
      
      <div v-if="breakdown.additional_cost > 0" class="flex justify-between py-2 border-b border-gray-200">
        <span class="text-gray-600">Additional Cost:</span>
        <span class="font-semibold">₹{{ breakdown.additional_cost?.toFixed(2) }}</span>
      </div>
      
      <div class="flex justify-between py-3 border-t-2 border-blue-200 bg-blue-50 px-3 rounded">
        <span class="font-bold text-blue-800">Total Cost:</span>
        <span class="text-xl font-bold text-blue-600">₹{{ breakdown.total_cost?.toFixed(2) || '0.00' }}</span>
      </div>
    </div>
    
    <div v-if="isActive" class="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
      <p class="text-sm text-yellow-800 font-medium">
        ⏰ This reservation is active. Cost updates in real-time.
      </p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  breakdown: {
    type: Object,
    required: true,
    default: () => ({})
  },
  isActive: {
    type: Boolean,
    default: false
  }
});
</script>

<style scoped>
.cost-summary {
  min-width: 280px;
}
</style>