import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const DEMO_ACCOUNTS = [
  { username: "user_jabodetabek", label: "Jabodetabek", desc: "Site Tangerang & Bekasi" },
  { username: "user_jabar", label: "Jawa Barat", desc: "Site Cilegon, Purwakarta, Karawang, Bandung" },
  { username: "user_jateng", label: "Jawa Tengah", desc: "Site Magelang & Semarang" },
  { username: "admin_nasional", label: "Nasional (Semua)", desc: "Akses seluruh site Indonesia" },
];

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

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

  const from = location.state?.from?.pathname || "/";

  useEffect(() => {
    if (user) {
      navigate(from, { replace: true });
    }
  }, [user, navigate, from]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setErrorMsg("Mohon isi username dan password.");
      return;
    }

    setErrorMsg("");
    setIsSubmitting(true);

    try {
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setErrorMsg(err.message || "Gagal login. Periksa kembali akun Anda.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemo = (acc) => {
    setUsername(acc.username);
    setPassword("mobius123");
    setErrorMsg("");
  };

  return (
    <div className="login-wrapper">
      <div className="login-top-bar">
        <span className="login-brand-tag">POC DASHBOARD</span>
        <button
          type="button"
          className="theme-toggle-btn"
          onClick={toggleTheme}
          title="Ganti Tema (Light/Dark)"
        >
          {theme === "dark" ? "☀ Light" : "☾ Dark"}
        </button>
      </div>

      <div className="login-card">
        <div className="login-card-header">
          <h1 className="login-title">Log In</h1>
          <p className="login-subtitle">
            Akses pemantauan energi PoC site berbasis wilayah kerja
          </p>
        </div>

        {errorMsg && (
          <div className="login-error-box" role="alert">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Masukkan username"
              autoComplete="username"
              required
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Masukkan password"
              autoComplete="current-password"
              required
              disabled={isSubmitting}
            />
          </div>

          <button
            type="submit"
            className="login-submit-btn"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Memverifikasi…" : "Masuk"}
          </button>
        </form>

        <div className="demo-accounts-section">
          <div className="demo-section-label">Pilih Akun Demo Wilayah:</div>
          <div className="demo-chips-grid">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.username}
                type="button"
                className={`demo-chip ${username === acc.username ? "active" : ""}`}
                onClick={() => fillDemo(acc)}
                title={acc.desc}
              >
                <span className="demo-chip-title">{acc.label}</span>
                <span className="demo-chip-user">{acc.username}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

