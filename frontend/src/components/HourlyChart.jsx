import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { num } from "../format";

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
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
        <div style={{ fontWeight: 700, marginBottom: "4px" }}>Jam {label}</div>
        {payload.map((item) => (
          <div
            key={item.name}
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "12px",
              color: item.color,
              fontVariantNumeric: "tabular-nums",
            }}
          >
            <span>{item.name}:</span>
            <b>{num(item.value)} kWh</b>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

export default function HourlyChart({ data, isLoading }) {
  return (
    <div className="card">
      <div className="card-title">Power Performance Today (Hourly)</div>

      <div className="chart-legend">
        <div className="chart-legend-item">
          <span
            className="chart-legend-line"
            style={{ backgroundColor: "var(--load)" }}
          ></span>
          <span>Load</span>
        </div>
        <div className="chart-legend-item">
          <span
            className="chart-legend-line"
            style={{ backgroundColor: "var(--pln)" }}
          ></span>
          <span>PLN</span>
        </div>
        <div className="chart-legend-item">
          <span
            className="chart-legend-line"
            style={{ backgroundColor: "var(--mob)" }}
          ></span>
          <span>PoC</span>
        </div>
      </div>

      <div className="hourly-chart-wrap">
        {isLoading ? (
          <div className="state-box">Memuat grafik per jam…</div>
        ) : !data || data.length === 0 ? (
          <div className="state-box">Tidak ada data pembacaan hari ini.</div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart
              data={data}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
              <XAxis
                dataKey="hour"
                stroke="var(--muted)"
                fontSize={11}
                tickLine={false}
              />
              <YAxis
                stroke="var(--muted)"
                fontSize={11}
                tickLine={false}
                unit=" kWh"
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="load_kwh"
                name="Load"
                stroke="var(--load)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="pln_kwh"
                name="PLN"
                stroke="var(--pln)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="mobius_kwh"
                name="PoC"
                stroke="var(--mob)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
