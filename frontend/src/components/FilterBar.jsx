import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTenants } from "../api";

export default function FilterBar({
  tenants,
  setTenants,
  statuses,
  setStatuses,
  count,
}) {
  const { data: allTenants = [] } = useQuery({
    queryKey: ["tenants"],
    queryFn: getTenants,
  });

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

  const toggleTenant = (t) => {
    setTenants((prev) =>
      prev.includes(t) ? prev.filter((item) => item !== t) : [...prev, t]
    );
  };

  const toggleStatus = (s) => {
    setStatuses((prev) =>
      prev.includes(s) ? prev.filter((item) => item !== s) : [...prev, s]
    );
  };

  return (
    <header className="filter-bar">
      <div className="filter-title">
        <span className="filter-brand">MOBIUS</span>
        <span className="filter-count">{count} Site</span>
      </div>

      <div className="filter-groups">
        {/* Tenant Filter */}
        <div className="filter-group">
          <span className="filter-label">Tenant:</span>
          {allTenants.map((t) => {
            const active = tenants.includes(t);
            return (
              <button
                key={t}
                type="button"
                className={`chip ${active ? "active" : ""}`}
                onClick={() => toggleTenant(t)}
                aria-pressed={active}
              >
                {t}
              </button>
            );
          })}
        </div>

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
