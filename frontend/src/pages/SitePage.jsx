import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getDaily, getHourly, getSummary } from "../api";
import { formatDate, formatTime, num, rp } from "../format";
import { useAuth } from "../context/AuthContext";
import EnergyFlow from "../components/EnergyFlow";
import HourlyChart from "../components/HourlyChart";
import KpiRow from "../components/KpiRow";
import TrendChart from "../components/TrendChart";
import ExportModal from "../components/ExportModal";

export default function SitePage() {
  const { code } = useParams();
  const { user, logout } = useAuth();
  const [isExportOpen, setIsExportOpen] = useState(false);

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

  const {
    data: summaryData,
    isLoading: isSummaryLoading,
    isError: isSummaryError,
  } = useQuery({
    queryKey: ["summary", user?.username, code],
    queryFn: () => getSummary(code),
  });

  const { data: hourlyData, isLoading: isHourlyLoading } = useQuery({
    queryKey: ["hourly", user?.username, code],
    queryFn: () => getHourly(code),
  });

  const { data: dailyData, isLoading: isDailyLoading } = useQuery({
    queryKey: ["daily", user?.username, code],
    queryFn: () => getDaily(code, 30),
  });

  if (isSummaryLoading) {
    return (
      <div className="site-page">
        <div className="state-box">Memuat data dashboard site {code}…</div>
      </div>
    );
  }

  if (isSummaryError || !summaryData) {
    return (
      <div className="site-page">
        <div className="state-box error-text">
          Gagal memuat data site {code} (atau site berada di luar wilayah Anda).{" "}
          <Link to="/" style={{ marginLeft: "8px", textDecoration: "underline" }}>
            Kembali ke Peta
          </Link>
        </div>
      </div>
    );
  }

  const { site, today } = summaryData;
  const isDone = site.status === "Done";

  return (
    <div className="site-page">
      {/* 1. Header Bar */}
      <header className="site-page-top">
        <div className="site-page-nav">
          <Link to="/" className="back-link" title="Kembali ke Peta">
            ← Peta
          </Link>
          <div className="site-page-title-box">
            <h1>Site {site.code}</h1>
            <p>
              {site.area} &bull; Wilayah: <b>{site.region}</b>
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button
            type="button"
            className="btn-export-excel"
            onClick={() => setIsExportOpen(true)}
            title="Export data performance test ke Excel"
          >
            📥 Export Excel
          </button>

          <div className="cutoff-badge">
            Update Cut Off:
            <b>
              {formatDate(today.cutoff)} | {formatTime(today.cutoff)}
            </b>
          </div>

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

      {/* 2. Site Detail Strip */}
      <section className="site-strip" aria-label="Site Details">
        <div className="strip-item">
          <dt>Site ID</dt>
          <dd>{site.code}</dd>
        </div>
        <div className="strip-item">
          <dt>Wilayah</dt>
          <dd>
            <span className="pill region-pill">
              {site.region || "-"}
            </span>
          </dd>
        </div>
        <div className="strip-item">
          <dt>Status</dt>
          <dd>
            <span className={`pill ${isDone ? "done" : "prog"}`}>
              {site.status}
            </span>
          </dd>
        </div>
        <div className="strip-item">
          <dt>PoC Unit</dt>
          <dd>{site.mobius_unit || "-"}</dd>
        </div>
        <div className="strip-item">
          <dt>Rated Load</dt>
          <dd>{site.rated_load_kw ? `${num(site.rated_load_kw, 1)} kW` : "-"}</dd>
        </div>
        <div className="strip-item">
          <dt>Tarif PLN</dt>
          <dd>{rp(site.tariff_per_kwh)}/kWh</dd>
        </div>
        <div className="strip-item">
          <dt>Installed</dt>
          <dd>{site.installed_at ? formatDate(site.installed_at) : "-"}</dd>
        </div>
      </section>

      {/* 3. Today KPI Row */}
      <KpiRow today={today} />

      {/* 4. Mid Section (Energy Flow + Hourly Chart) */}
      <section className="mid-grid">
        <EnergyFlow today={today} />
        <HourlyChart data={hourlyData} isLoading={isHourlyLoading} />
      </section>

      {/* 5. 30-Day Trend Chart & Table */}
      <TrendChart
        data={dailyData}
        isLoading={isDailyLoading}
        onExportClick={() => setIsExportOpen(true)}
      />

      {/* 6. Export Performance Modal */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        siteCode={site.code}
        defaultEndDate={today.cutoff}
      />
    </div>
  );
}
