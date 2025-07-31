import axios from 'axios';
const API = 'http://localhost:5000/api/admin';
const token = () => localStorage.getItem('token');

export default {
  async fetchAllUsers() {
    const res = await axios.get(`${API}/users`, {
      headers: { Authorization: `Bearer ${token()}` }
    });
    return res.data;
  }
};
