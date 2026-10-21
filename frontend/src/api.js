// api.js
const get = (url) =>
  fetch(url).then((r) => {
    if (!r.ok) {
      throw new Error(`API error: ${r.status} ${r.statusText}`);
    }
    return r.json();
  });

export const getTenants = () => get("/api/tenants/");

export const getSites = (tenants = [], statuses = []) => {
  const q = new URLSearchParams();
  tenants.forEach((t) => q.append("tenant", t));
  statuses.forEach((s) => q.append("status", s));
  const queryString = q.toString();
  return get(`/api/sites/${queryString ? `?${queryString}` : ""}`);
};

export const getSummary = (code) => get(`/api/sites/${encodeURIComponent(code)}/summary/`);

export const getHourly = (code, date = null) => {
  const q = date ? `?date=${encodeURIComponent(date)}` : "";
  return get(`/api/sites/${encodeURIComponent(code)}/hourly/${q}`);
};

export const getDaily = (code, days = 30) =>
  get(`/api/sites/${encodeURIComponent(code)}/daily/?days=${days}`);
