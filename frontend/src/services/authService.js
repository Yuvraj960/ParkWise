import axios from 'axios';
const API = 'http://localhost:5000/api';

export default {
  async login({ username, password }) {
    try {
      const res = await axios.post(`${API}/login`, { username, password });
      return res.data;
    } catch (err) {
      alert('Invalid credentials');
      return null;
    }
  },

  async register(data) {
    try {
      await axios.post(`${API}/register`, data);
      alert('Registered successfully');
      return true;
    } catch (err) {
      alert(err.response?.data?.message || 'Registration failed');
      return false;
    }
  }
};
