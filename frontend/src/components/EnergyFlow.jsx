import { num, pct } from "../format";

export default function EnergyFlow({ today }) {
  if (!today) return null;

  const latest = today.latest_hour;

  return (
    <div className="card">
      <div className="card-title">Energy Flow (Today)</div>

      <div className="energy-flow-container">
        <div className="energy-flow-svg-wrap">
          <svg
            viewBox="0 0 340 130"
            className="flow-svg"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="7"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--muted)" />
              </marker>
            </defs>

            {/* Connecting lines */}
            {/* PLN to Mobius */}
            <line
              x1="85"
              y1="40"
              x2="135"
              y2="40"
              stroke="var(--muted)"
              strokeWidth="2"
              strokeDasharray="4 4"
              markerEnd="url(#arrow)"
            />

            {/* Mobius to Load */}
            <line
              x1="205"
              y1="40"
              x2="255"
              y2="40"
              stroke="var(--muted)"
              strokeWidth="2"
              strokeDasharray="4 4"
              markerEnd="url(#arrow)"
            />

            {/* Node 1: PLN */}
            <g transform="translate(15, 12)">
              <rect
                width="70"
                height="56"
                rx="6"
                fill="var(--surface-alt)"
                stroke="var(--pln)"
                strokeWidth="1.5"
              />
              <text
                x="35"
                y="22"
                textAnchor="middle"
                fill="var(--pln)"
                fontWeight="700"
                fontSize="11"
                fontFamily="var(--font-display)"
              >
                PLN
              </text>
              <text
                x="35"
                y="42"
                textAnchor="middle"
                fill="var(--ink)"
                fontWeight="600"
                fontSize="11"
                fontVariantNumeric="tabular-nums"
              >
                {num(today.pln_kwh)}
              </text>
              <text
                x="35"
                y="52"
                textAnchor="middle"
                fill="var(--muted)"
                fontSize="8.5"
              >
                kWh
              </text>
            </g>

            {/* Node 2: MOBIUS */}
            <g transform="translate(135, 12)">
              <rect
                width="70"
                height="56"
                rx="6"
                fill="var(--mob-bg)"
                stroke="var(--mob)"
                strokeWidth="1.5"
              />
              <text
                x="35"
                y="22"
                textAnchor="middle"
                fill="var(--mob)"
                fontWeight="700"
                fontSize="11"
                fontFamily="var(--font-display)"
              >
                MOBIUS
              </text>
              <text
                x="35"
                y="42"
                textAnchor="middle"
                fill="var(--ink)"
                fontWeight="600"
                fontSize="11"
                fontVariantNumeric="tabular-nums"
              >
                +{num(today.mobius_kwh)}
              </text>
              <text
                x="35"
                y="52"
                textAnchor="middle"
                fill="var(--muted)"
                fontSize="8.5"
              >
                kWh
              </text>
            </g>

            {/* Node 3: LOAD */}
            <g transform="translate(255, 12)">
              <rect
                width="70"
                height="56"
                rx="6"
                fill="var(--surface-alt)"
                stroke="var(--load)"
                strokeWidth="1.5"
              />
              <text
                x="35"
                y="22"
                textAnchor="middle"
                fill="var(--load-ink)"
                fontWeight="700"
                fontSize="11"
                fontFamily="var(--font-display)"
              >
                LOAD
              </text>
              <text
                x="35"
                y="42"
                textAnchor="middle"
                fill="var(--ink)"
                fontWeight="600"
                fontSize="11"
                fontVariantNumeric="tabular-nums"
              >
                {num(today.load_kwh)}
              </text>
              <text
                x="35"
                y="52"
                textAnchor="middle"
                fill="var(--muted)"
                fontSize="8.5"
              >
                kWh
              </text>
            </g>

            {/* Subtext info */}
            <text
              x="170"
              y="98"
              textAnchor="middle"
              fill="var(--mob)"
              fontWeight="600"
              fontSize="11"
              fontFamily="var(--font-body)"
            >
              PLN input lifted by {pct(today.lift_pct)}
            </text>
            <text
              x="170"
              y="114"
              textAnchor="middle"
              fill="var(--muted)"
              fontSize="9.5"
              fontFamily="var(--font-body)"
            >
              Mobius Contribution: {pct(today.contribution_pct)}
            </text>
          </svg>
        </div>

        {/* Latest Hour Equation */}
        {latest ? (
          <div className="flow-equation">
            Latest Hour Equation:
            <br />
            <b className="c-load">Load {num(latest.load_kwh)} kW</b> ={" "}
            <span className="c-pln">PLN {num(latest.pln_kwh)} kW</span> +{" "}
            <span className="c-mob">Mobius {num(latest.mobius_kwh)} kW</span>
          </div>
        ) : (
          <div className="flow-equation">
            Total Today:
            <br />
            <b className="c-load">Load {num(today.load_kwh)} kWh</b> ={" "}
            <span className="c-pln">PLN {num(today.pln_kwh)} kWh</span> +{" "}
            <span className="c-mob">Mobius {num(today.mobius_kwh)} kWh</span>
          </div>
        )}
      </div>
    </div>
  );
}
