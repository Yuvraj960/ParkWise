import axios from 'axios';
const API = 'http://localhost:5000/api';
const token = () => localStorage.getItem('token');

export default {
  async reserveSpot(lotId, vehicle_number) {
    try {
      const res = await axios.post(`${API}/reserve-spot`, { lot_id: lotId, vehicle_number }, {
        headers: { Authorization: `Bearer ${token()}` }
      });
      return res.data;
    } catch (err) {
      alert(err.response?.data?.message || 'Reservation failed');
      return null;
    }
  },

  async releaseSpot(reservationId) {
    const res = await axios.put(`${API}/release-spot/${reservationId}`, {}, {
      headers: { Authorization: `Bearer ${token()}` }
    });
    return res.data;
  },

  async fetchMyReservations() {
    const res = await axios.get(`${API}/user-reservations`, {
      headers: { Authorization: `Bearer ${token()}` }
    });
    return res.data;
  }
};
