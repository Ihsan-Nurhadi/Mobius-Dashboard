import { useMemo } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  LabelList,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { num, pct, rp } from "../format";

function CustomTrendTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const dataItem = payload[0].payload;
    return (
      <div
        style={{
          background: "var(--surface)",
          border: "1px solid var(--line)",
          borderRadius: "6px",
          padding: "8px 12px",
          fontSize: "12px",
          color: "var(--ink)",
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: "4px" }}>
          Tanggal: {label}
        </div>
        <div style={{ color: "var(--load)", fontVariantNumeric: "tabular-nums" }}>
          Load: <b>{num(dataItem.load_kwh)} kWh</b>
        </div>
        <div style={{ color: "var(--pln)", fontVariantNumeric: "tabular-nums" }}>
          PLN: <b>{num(dataItem.pln_kwh)} kWh</b>
        </div>
        <div style={{ color: "var(--mob)", fontVariantNumeric: "tabular-nums" }}>
          PoC: <b>{num(dataItem.mobius_kwh)} kWh</b>
        </div>
        <div style={{ color: "var(--brand)", fontVariantNumeric: "tabular-nums" }}>
          Kontribusi: <b>{pct(dataItem.contribution_pct)}</b>
        </div>
        <div style={{ color: "var(--ink)", fontVariantNumeric: "tabular-nums" }}>
          Est. Saving: <b>{rp(dataItem.saving_rp)}</b>
        </div>
      </div>
    );
  }
  return null;
}

export default function TrendChart({ data, isLoading }) {
  const chartData = useMemo(() => {
    if (!data || !data.length) return [];
    return data.map((d) => {
      const dt = new Date(d.date);
      const dayNum = dt.getDate();
      const monthShort = dt.toLocaleDateString("id-ID", { month: "short" });
      return {
        ...d,
        label: `${dayNum} ${monthShort}`,
        shortDay: `${dayNum}`,
      };
    });
  }, [data]);

  // Aggregate 30-day totals
  const totals = useMemo(() => {
    if (!data || !data.length) return null;
    const pln = data.reduce((acc, cur) => acc + (cur.pln_kwh || 0), 0);
    const mobius = data.reduce((acc, cur) => acc + (cur.mobius_kwh || 0), 0);
    const load = pln + mobius;
    const saving = data.reduce((acc, cur) => acc + (cur.saving_rp || 0), 0);
    const avgContrib = load > 0 ? (mobius / load) * 100 : 0;
    const avgLoad = load / data.length;

    return {
      pln: round(pln, 2),
      mobius: round(mobius, 2),
      load: round(load, 2),
      saving,
      avgContrib: round(avgContrib, 2),
      avgLoad,
    };
  }, [data]);

  function round(val, d = 2) {
    const factor = Math.pow(10, d);
    return Math.round(val * factor) / factor;
  }

  // Detect dip days (load < 75% of average load)
  const isDipDay = (item) => {
    if (!totals || !totals.avgLoad) return false;
    return item.load_kwh < totals.avgLoad * 0.75;
  };

  return (
    <div className="card trend-section">
      <div className="card-title">30-Day Performance Trend</div>

      {totals && (
        <div className="trend-summary-row">
          <div>
            Total Load: <b>{num(totals.load)} kWh</b>
          </div>
          <div>
            Total PLN: <b>{num(totals.pln)} kWh</b>
          </div>
          <div>
            Total PoC: <b className="c-mob">{num(totals.mobius)} kWh</b>
          </div>
          <div>
            Avg. Contribution: <b className="c-brand">{pct(totals.avgContrib)}</b>
          </div>
          <div>
            Total Saving: <b className="c-mob">{rp(totals.saving)}</b>
          </div>
        </div>
      )}

      <div className="chart-legend">
        <div className="chart-legend-item">
          <span
            className="chart-legend-line"
            style={{ backgroundColor: "var(--load)" }}
          ></span>
          <span>Load (kWh)</span>
        </div>
        <div className="chart-legend-item">
          <span
            className="chart-legend-line"
            style={{ backgroundColor: "var(--pln)" }}
          ></span>
          <span>PLN (kWh)</span>
        </div>
        <div className="chart-legend-item">
          <span
            className="chart-legend-line"
            style={{ backgroundColor: "var(--mob)" }}
          ></span>
          <span>PoC (kWh)</span>
        </div>
        <div className="chart-legend-item">
          <span
            style={{
              display: "inline-block",
              width: "12px",
              height: "12px",
              backgroundColor: "var(--mob)",
              opacity: 0.25,
              borderRadius: "2px",
            }}
          ></span>
          <span>PoC Contribution (%)</span>
        </div>
      </div>

      <div className="trend-chart-wrap">
        {isLoading ? (
          <div className="state-box">Memuat grafik tren 30 hari…</div>
        ) : !chartData.length ? (
          <div className="state-box">Data tren tidak tersedia.</div>
        ) : (
          <ResponsiveContainer width="100%" height={290}>
            <ComposedChart
              data={chartData}
              margin={{ top: 20, right: 10, left: -20, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
              <XAxis
                dataKey="label"
                stroke="var(--muted)"
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                yAxisId="left"
                stroke="var(--muted)"
                fontSize={11}
                tickLine={false}
                unit=" kWh"
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                domain={[0, 40]}
                stroke="var(--mob)"
                fontSize={10}
                tickLine={false}
                unit="%"
              />
              <Tooltip content={<CustomTrendTooltip />} />

              {/* Bar for Contribution % */}
              <Bar
                yAxisId="right"
                dataKey="contribution_pct"
                name="Contribution %"
                fill="var(--mob)"
                fillOpacity={0.16}
                radius={[2, 2, 0, 0]}
              >
                <LabelList
                  dataKey="contribution_pct"
                  position="top"
                  formatter={(v) => `${Math.round(v)}%`}
                  style={{
                    fill: "var(--mob)",
                    fontSize: "10px",
                    fontWeight: 600,
                  }}
                />
              </Bar>

              {/* Lines for Load, PLN, Mobius */}
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="load_kwh"
                name="Load"
                stroke="var(--load)"
                strokeWidth={2.2}
                dot={false}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="pln_kwh"
                name="PLN"
                stroke="var(--pln)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="mobius_kwh"
                name="PoC"
                stroke="var(--mob)"
                strokeWidth={2}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* 30-Day Daily Table (scrollable with sticky first column) */}
      {chartData.length > 0 && (
        <div className="trend-table-container">
          <table className="trend-table">
            <thead>
              <tr>
                <th>Metrik / Hari</th>
                {chartData.map((d) => (
                  <th key={d.date} title={d.date}>
                    {d.shortDay}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Row 1: Mobius Contr. */}
              <tr>
                <td>
                  <span className="c-mob" style={{ fontWeight: 600 }}>
                    PoC Contr.
                  </span>
                </td>
                {chartData.map((d) => (
                  <td key={d.date} className={isDipDay(d) ? "c-load" : "c-mob"}>
                    {pct(d.contribution_pct, 0)}
                  </td>
                ))}
              </tr>

              {/* Row 2: MOBIUS (kWh) */}
              <tr>
                <td>
                  <span className="c-mob">PoC (kWh)</span>
                </td>
                {chartData.map((d) => (
                  <td key={d.date} className={isDipDay(d) ? "c-load" : ""}>
                    {num(d.mobius_kwh, 1)}
                  </td>
                ))}
              </tr>

              {/* Row 3: PLN (kWh) */}
              <tr>
                <td>
                  <span className="c-pln">PLN (kWh)</span>
                </td>
                {chartData.map((d) => (
                  <td key={d.date} className={isDipDay(d) ? "c-load" : ""}>
                    {num(d.pln_kwh, 1)}
                  </td>
                ))}
              </tr>

              {/* Row 4: LOAD (kWh) */}
              <tr>
                <td>
                  <span className="c-load">LOAD (kWh)</span>
                </td>
                {chartData.map((d) => (
                  <td
                    key={d.date}
                    style={isDipDay(d) ? { color: "var(--warn)", fontWeight: 700 } : {}}
                  >
                    {num(d.load_kwh, 1)}
                  </td>
                ))}
              </tr>

              {/* Row 5: Est. Saving */}
              <tr>
                <td>
                  <span className="c-brand">Est. Saving</span>
                </td>
                {chartData.map((d) => (
                  <td key={d.date} className={isDipDay(d) ? "c-load" : ""}>
                    {num(d.saving_rp / 1000, 1)}k
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
