import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, TileLayer, useMap } from "react-leaflet";
import { useQuery } from "@tanstack/react-query";
import { getSites } from "../api";
import FilterBar from "../components/FilterBar";
import SiteCard from "../components/SiteCard";

const STATUS_COLOR = {
  Done: "#1b7f4d",
  "On Progress": "#b7791f",
};

// Helper component to auto-fit bounds on initial load
function BoundsManager({ sites }) {
  const map = useMap();

  useEffect(() => {
    if (sites && sites.length > 0) {
      const bounds = sites.map((s) => [s.latitude, s.longitude]);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 10 });
    }
  }, [sites, map]);

  return null;
}

export default function MapPage() {
  const [tenants, setTenants] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [selected, setSelected] = useState(null);

  const { data: sites = [], isLoading } = useQuery({
    queryKey: ["sites", tenants, statuses],
    queryFn: () => getSites(tenants, statuses),
  });

  // If selected site is filtered out, close the card
  useEffect(() => {
    if (selected && !sites.some((s) => s.code === selected)) {
      setSelected(null);
    }
  }, [sites, selected]);

  return (
    <div className="map-page">
      <FilterBar
        tenants={tenants}
        setTenants={setTenants}
        statuses={statuses}
        setStatuses={setStatuses}
        count={sites.length}
      />

      <MapContainer
        center={[-6.9, 108.5]}
        zoom={8}
        className="map-container"
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxZoom={19}
        />

        <BoundsManager sites={sites} />

        {sites.map((s) => {
          const isSelected = selected === s.code;
          return (
            <CircleMarker
              key={s.code}
              center={[s.latitude, s.longitude]}
              radius={isSelected ? 11 : 8}
              pathOptions={{
                color: isSelected ? "#c5192d" : "#ffffff",
                weight: isSelected ? 3.5 : 2,
                fillColor: STATUS_COLOR[s.status] || "#5b727c",
                fillOpacity: 1,
              }}
              eventHandlers={{
                click: () => setSelected(s.code),
              }}
            />
          );
        })}
      </MapContainer>

      {/* Map Legend */}
      <div className="map-legend" aria-label="Status Legend">
        <div className="legend-item">
          <span className="legend-dot dot-done"></span>
          <span>Done</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot dot-prog"></span>
          <span>On Progress</span>
        </div>
      </div>

      {/* Summary Card */}
      {selected && (
        <SiteCard code={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
