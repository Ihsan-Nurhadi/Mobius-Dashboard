import { num, pct, rp } from "../format";

export default function KpiRow({ today }) {
  if (!today) return null;

  return (
    <section className="kpi-row" aria-label="Key Performance Indicators Today">
      <div className="kpi-box">
        <div className="kpi-box-label">PoC Energy Today</div>
        <div className="kpi-box-value c-mob">
          {num(today.mobius_kwh)} <small>kWh</small>
        </div>
      </div>

      <div className="kpi-box">
        <div className="kpi-box-label">PLN Energy Today</div>
        <div className="kpi-box-value c-pln">
          {num(today.pln_kwh)} <small>kWh</small>
        </div>
      </div>

      <div className="kpi-box">
        <div className="kpi-box-label">Load Energy Today</div>
        <div className="kpi-box-value c-load">
          {num(today.load_kwh)} <small>kWh</small>
        </div>
      </div>

      <div className="kpi-box">
        <div className="kpi-box-label">PoC Contribution</div>
        <div className="kpi-box-value c-brand">
          {pct(today.contribution_pct)}
        </div>
      </div>

      <div className="kpi-box">
        <div className="kpi-box-label">Est. Saving Today</div>
        <div className="kpi-box-value c-mob">
          {rp(today.saving_rp)}
        </div>
      </div>
    </section>
  );
}
