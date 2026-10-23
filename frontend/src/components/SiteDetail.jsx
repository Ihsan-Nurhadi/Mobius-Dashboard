import { num, rp } from "../format";

export default function SiteDetail({ site }) {
  if (!site) return null;

  const isDone = site.status === "Done";

  return (
    <dl className="site-detail-fields">
      <div className="field-pair">
        <dt>Site ID</dt>
        <dd>{site.code}</dd>
      </div>

      <div className="field-pair">
        <dt>Tenant</dt>
        <dd>
          <span className={`pill tenant ${site.tenant === "Tsel" ? "pill-tsel" : ""}`}>
            {site.tenant}
          </span>
        </dd>
      </div>

      <div className="field-pair">
        <dt>Lokasi</dt>
        <dd>{site.area}</dd>
      </div>

      <div className="field-pair">
        <dt>Status</dt>
        <dd>
          <span className={`pill ${isDone ? "done" : "prog"}`}>
            {site.status}
          </span>
        </dd>
      </div>

      <div className="field-pair">
        <dt>PoC Unit</dt>
        <dd>{site.mobius_unit || "-"}</dd>
      </div>

      <div className="field-pair">
        <dt>Rated Load</dt>
        <dd>{site.rated_load_kw ? `${num(site.rated_load_kw, 1)} kW` : "-"}</dd>
      </div>

      <div className="field-pair">
        <dt>Tarif PLN</dt>
        <dd>{rp(site.tariff_per_kwh)}/kWh</dd>
      </div>

      {site.installed_at && (
        <div className="field-pair">
          <dt>Installed</dt>
          <dd>{site.installed_at}</dd>
        </div>
      )}
    </dl>
  );
}
