import axios from 'axios';

const API = 'http://localhost:5000/api';

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { Authorization: `Bearer ${token}` } : {};
};

export default {
    async exportUserDataCSV() {
        try {
            const res = await axios.post(`${API}/export-csv`, {}, {
                headers: getAuthHeaders()
            });
            return res.data;
        } catch (err) {
            console.error('CSV export failed:', err);
            throw err;
        }
    },

    async getTaskStatus(taskId) {
        try {
            const res = await axios.get(`${API}/task-status/${taskId}`, {
                headers: getAuthHeaders()
            });
            return res.data;
        } catch (err) {
            console.error('Task status check failed:', err);
            throw err;
        }
    },

    async downloadCSV(downloadKey) {
        try {
            const res = await axios.get(`${API}/download-csv/${downloadKey}`, {
                headers: getAuthHeaders(),
                responseType: 'blob'
            });
            return res.data;
        } catch (err) {
            console.error('CSV download failed:', err);
            throw err;
        }
    },

    async triggerDailyReminders() {
        try {
            const res = await axios.post(`${API}/trigger-reminders`, {}, {
                headers: getAuthHeaders()
            });
            return res.data;
        } catch (err) {
            console.error('Reminder trigger failed:', err);
            throw err;
        }
    },

    async generateMonthlyReports() {
        try {
            const res = await axios.post(`${API}/generate-reports`, {}, {
                headers: getAuthHeaders()
            });
            return res.data;
        } catch (err) {
            console.error('Report generation failed:', err);
            throw err;
        }
    },

    async clearCache() {
        try {
            const res = await axios.post(`${API}/clear-cache`, {}, {
                headers: getAuthHeaders()
            });
            return res.data;
        } catch (err) {
            console.error('Clear cache failed:', err);
            throw err;
        }
    },

    async getCacheStatus() {
        try {
            const res = await axios.get(`${API}/cache-status`, {
                headers: getAuthHeaders()
            });
            return res.data;
        } catch (err) {
            console.error('Cache status check failed:', err);
            throw err;
        }
    }
};