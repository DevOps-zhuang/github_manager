export const getToken = () => localStorage.getItem('auth_token');
export const getUsername = () => localStorage.getItem('username');

export const setAuth = (token, username) => {
  localStorage.setItem('auth_token', token);
  localStorage.setItem('username', username);
};

export const clearAuth = () => {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('username');
};

export const isAuthenticated = () => !!getToken();
