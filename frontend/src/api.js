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
    let errorDetail = "";
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || (typeof errorData === "string" ? errorData : "");
    } catch {
      // Non-JSON response (e.g. HTML 400 Bad Request from Django DisallowedHost)
    }
    const message =
      errorDetail ||
      (response.status === 400
        ? "API error: 400 Bad Request (Host/IP belum terdaftar di ALLOWED_HOSTS backend)"
        : `API error: ${response.status} ${response.statusText}`);
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


export const downloadPerformanceExcel = async (code, startDate = null, endDate = null) => {
  const q = new URLSearchParams();
  if (startDate) q.append("start_date", startDate);
  if (endDate) q.append("end_date", endDate);
  const queryString = q.toString();

  const url = `/api/sites/${encodeURIComponent(code)}/export-performance/${queryString ? `?${queryString}` : ""}`;
  const headers = {};
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Token ${token}`;
  }

  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`Gagal mengunduh berkas Excel (${response.status} ${response.statusText})`);
  }

  // Determine filename from Content-Disposition if present
  let filename = `Performance_Test_${code}.xlsx`;
  const disposition = response.headers.get("Content-Disposition");
  if (disposition && disposition.includes("filename=")) {
    const match = disposition.match(/filename="?([^";]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(downloadUrl);
};
