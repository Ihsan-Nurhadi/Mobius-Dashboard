// api.js
const TOKEN_KEY = "mobius_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (token) => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
};

const request = async (url, options = {}) => {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Token ${token}`;
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401 && !url.includes("/api/auth/login/")) {
    setToken(null);
    window.location.href = "/login";
    throw new Error("Sesi telah berakhir. Silakan login kembali.");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || `API error: ${response.status} ${response.statusText}`;
    throw new Error(message);
  }

  return response.json();
};

export const apiLogin = (username, password) =>
  request("/api/auth/login/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });

export const apiLogout = () =>
  request("/api/auth/logout/", {
    method: "POST",
  }).finally(() => {
    setToken(null);
  });

export const apiGetMe = () => request("/api/auth/me/");

export const getSites = (statuses = [], regions = []) => {
  const q = new URLSearchParams();
  statuses.forEach((s) => q.append("status", s));
  regions.forEach((r) => q.append("region", r));
  const queryString = q.toString();
  return request(`/api/sites/${queryString ? `?${queryString}` : ""}`);
};

export const getSummary = (code) =>
  request(`/api/sites/${encodeURIComponent(code)}/summary/`);

export const getHourly = (code, date = null) => {
  const q = date ? `?date=${encodeURIComponent(date)}` : "";
  return request(`/api/sites/${encodeURIComponent(code)}/hourly/${q}`);
};

export const getDaily = (code, days = 30) =>
  request(`/api/sites/${encodeURIComponent(code)}/daily/?days=${days}`);
