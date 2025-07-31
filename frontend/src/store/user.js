import { defineStore } from 'pinia';
import authService from '/src/services/authService';

export const useUserStore = defineStore('user', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || ''
  }),

  actions: {
    async login(credentials) {
      const res = await authService.login(credentials);
      if (res) {
        this.user = res.user;
        this.token = res.access_token;
        localStorage.setItem('user', JSON.stringify(res.user));
        localStorage.setItem('token', res.access_token);
        return true;
      } else {
        this.logout();
        return false;
      }
    },
    async register(data) {
      return await authService.register(data);
    },
    logout() {
      this.user = null;
      this.token = '';
      localStorage.clear();
    }
  }
});
