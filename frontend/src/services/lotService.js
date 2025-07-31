import axios from 'axios';
const API = 'http://localhost:5000/api/parking-lots';
const token = () => localStorage.getItem('token');

export default {
  async fetchLots() {
    const res = await axios.get(API, { headers: { Authorization: `Bearer ${token()}` } });
    return res.data;
  },

  async createLot(data) {
    try {
      const res = await axios.post(API, data, {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token()}`
        }
      });
      return res.data;
    } catch (err) {
      console.error('Lot creation failed:', err.response?.data || err.message);
      throw err;
    }
  },

  async updateLot(id, data) {
    const res = await axios.put(`${API}/${id}`, data, { headers: { Authorization: `Bearer ${token()}` } });
    return res.data;
  },

  async deleteLot(id) {
    const res = await axios.delete(`${API}/${id}`, { headers: { Authorization: `Bearer ${token()}` } });
    return res.data;
  }
};

