import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function FilterBar({ statuses, setStatuses, count }) {
  const { user, logout } = useAuth();

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("mobius-theme") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("mobius-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  };

  const toggleStatus = (s) => {
    setStatuses((prev) =>
      prev.includes(s) ? prev.filter((item) => item !== s) : [...prev, s]
    );
  };

  const regionName = user?.region?.name || "Nasional";

  return (
    <header className="filter-bar">
      <div className="filter-title">
        <span className="filter-brand">POC DASHBOARD</span>
        <span className="region-indicator-badge" title={`Wilayah Kerja: ${regionName}`}>
          Wilayah: <b>{regionName}</b>
        </span>
        <span className="filter-count">{count} Site</span>
      </div>

      <div className="filter-groups">
        {/* Status Filter */}
        <div className="filter-group">
          <span className="filter-label">Status:</span>
          {["Done", "On Progress"].map((s) => {
            const active = statuses.includes(s);
            return (
              <button
                key={s}
                type="button"
                className={`chip ${active ? "active" : ""}`}
                onClick={() => toggleStatus(s)}
                aria-pressed={active}
              >
                {s}
              </button>
            );
          })}
        </div>

        {/* User Info & Actions */}
        <div className="user-action-group">
          <span className="user-pill" title={`Login sebagai ${user?.username || "Pengguna"}`}>
            👤 {user?.username}
          </span>

          <button
            type="button"
            className="logout-btn"
            onClick={logout}
            title="Keluar dari akun"
          >
            Logout
          </button>
        </div>

        {/* Theme Toggle */}
        <button
          type="button"
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title="Ganti Tema (Light/Dark)"
        >
          {theme === "dark" ? "☀ Light" : "☾ Dark"}
        </button>
      </div>
    </header>
  );
}
