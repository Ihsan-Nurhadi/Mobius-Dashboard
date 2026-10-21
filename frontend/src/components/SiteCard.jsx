import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getSummary } from "../api";
import SiteDetail from "./SiteDetail";
import { num, pct, rp, formatTime } from "../format";

export default function SiteCard({ code, onClose }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["summary", code],
    queryFn: () => getSummary(code),
  });

  return (
    <aside className="site-card" aria-label={`Ringkasan site ${code}`}>
      <div className="card-header-row">
        <div>
          <h2 className="site-card-title">{code}</h2>
          <div className="site-card-sub">Site Summary</div>
        </div>
        <button
          className="site-card-close"
          onClick={onClose}
          aria-label="Tutup Ringkasan"
          type="button"
        >
          ×
        </button>
      </div>

      {isLoading && <p className="muted">Memuat data site…</p>}
      {isError && (
        <p className="error-text">Data site gagal dimuat. Coba klik titik lagi.</p>
      )}

      {data && (
        <>
          <SiteDetail site={data.site} />

          <h3 className="section-title">
            Hari ini (Cut-off {formatTime(data.today.cutoff)})
          </h3>

          <dl className="kpi-grid">
            <div className="kpi-item">
              <dt>Mobius Energy</dt>
              <dd className="c-mob">{num(data.today.mobius_kwh)} kWh</dd>
            </div>
            <div className="kpi-item">
              <dt>PLN Energy</dt>
              <dd className="c-pln">{num(data.today.pln_kwh)} kWh</dd>
            </div>
            <div className="kpi-item">
              <dt>Load Energy</dt>
              <dd className="c-load">{num(data.today.load_kwh)} kWh</dd>
            </div>
            <div className="kpi-item">
              <dt>Mobius Contribution</dt>
              <dd className="c-brand">{pct(data.today.contribution_pct)}</dd>
            </div>
            <div className="kpi-item">
              <dt>Est. Saving</dt>
              <dd>{rp(data.today.saving_rp)}</dd>
            </div>
          </dl>

          <p className="flow-line">
            PLN <b>{num(data.today.pln_kwh)}</b> → Mobius <b>+{num(data.today.mobius_kwh)}</b> → Load <b>{num(data.today.load_kwh)} kWh</b>
          </p>

          <Link className="btn" to={`/sites/${code}`}>
            Buka Dashboard Site →
          </Link>
        </>
      )}
    </aside>
  );
}
