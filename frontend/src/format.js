// format.js (angka gaya Indonesia: 11,80 dan 1.868,39)
export const num = (n, d = 2) =>
  Number(n ?? 0).toLocaleString("id-ID", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });

export const pct = (n, d = 2) => `${num(n, d)}%`;

export const rp = (n) => `Rp ${Math.round(n ?? 0).toLocaleString("id-ID")}`;

export const formatDate = (isoStr) => {
  if (!isoStr) return "-";
  const d = new Date(isoStr);
  return d.toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};

export const formatTime = (isoStr) => {
  if (!isoStr) return "-";
  const d = new Date(isoStr);
  return d.toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
  });
};
