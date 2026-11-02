import { useEffect, useState } from "react";
import { downloadPerformanceExcel } from "../api";

export default function ExportModal({ isOpen, onClose, siteCode, defaultEndDate }) {
  const getInitialEndDate = () => {
    if (defaultEndDate) {
      const d = new Date(defaultEndDate);
      if (!isNaN(d.getTime())) return d.toISOString().split("T")[0];
    }
    return new Date().toISOString().split("T")[0];
  };

  const [endDate, setEndDate] = useState(getInitialEndDate);
  const [startDate, setStartDate] = useState(() => {
    const d = new Date(getInitialEndDate());
    d.setDate(d.getDate() - 29);
    return d.toISOString().split("T")[0];
  });

  const [isDownloading, setIsDownloading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (isOpen) {
      const end = getInitialEndDate();
      const start = new Date(end);
      start.setDate(start.getDate() - 29);

      setEndDate(end);
      setStartDate(start.toISOString().split("T")[0]);
      setErrorMsg("");
      setIsDownloading(false);
    }
  }, [isOpen, defaultEndDate]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && isOpen && !isDownloading) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isDownloading, onClose]);

  if (!isOpen) return null;

  const setPreset = (days) => {
    const end = new Date(getInitialEndDate());
    const start = new Date(end);
    start.setDate(start.getDate() - (days - 1));
    setEndDate(end.toISOString().split("T")[0]);
    setStartDate(start.toISOString().split("T")[0]);
    setErrorMsg("");
  };

  const setMonthPreset = () => {
    const now = new Date(getInitialEndDate());
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    setStartDate(firstDay.toISOString().split("T")[0]);
    setEndDate(now.toISOString().split("T")[0]);
    setErrorMsg("");
  };

  const handleDownload = async (e) => {
    e.preventDefault();
    if (!startDate || !endDate) {
      setErrorMsg("Harap tentukan tanggal awal dan tanggal akhir.");
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setErrorMsg("Tanggal awal tidak boleh melebihi tanggal akhir.");
      return;
    }

    setIsDownloading(true);
    setErrorMsg("");

    try {
      await downloadPerformanceExcel(siteCode, startDate, endDate);
      onClose();
    } catch (err) {
      setErrorMsg(err.message || "Gagal mengunduh berkas Excel. Coba lagi.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={!isDownloading ? onClose : undefined}>
      <div
        className="modal-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="modal-header">
          <div>
            <h2 id="modal-title" className="modal-title">
              Export Data Performance Test
            </h2>
            <p className="modal-subtitle">
              Unduh laporan kinerja energi site <b>{siteCode}</b> dalam format Excel (.xlsx)
            </p>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            disabled={isDownloading}
            aria-label="Tutup Modal"
          >
            ×
          </button>
        </div>

        {errorMsg && (
          <div className="modal-error-box" role="alert">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleDownload} className="modal-form">
          <div className="modal-presets">
            <span className="modal-presets-label">Pilihan Cepat:</span>
            <div className="modal-presets-chips">
              <button
                type="button"
                className="chip-preset"
                onClick={() => setPreset(7)}
                disabled={isDownloading}
              >
                7 Hari
              </button>
              <button
                type="button"
                className="chip-preset"
                onClick={() => setPreset(14)}
                disabled={isDownloading}
              >
                14 Hari
              </button>
              <button
                type="button"
                className="chip-preset"
                onClick={() => setPreset(30)}
                disabled={isDownloading}
              >
                30 Hari
              </button>
              <button
                type="button"
                className="chip-preset"
                onClick={setMonthPreset}
                disabled={isDownloading}
              >
                Bulan Ini
              </button>
            </div>
          </div>

          <div className="date-range-grid">
            <div className="form-group">
              <label htmlFor="export-start-date">Dari Tanggal (Start Date)</label>
              <input
                id="export-start-date"
                type="date"
                className="form-input"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                disabled={isDownloading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="export-end-date">Sampai Tanggal (End Date)</label>
              <input
                id="export-end-date"
                type="date"
                className="form-input"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
                disabled={isDownloading}
              />
            </div>
          </div>

          <div className="modal-info-note">
            Berkas Excel mencakup <b>Ringkasan Harian</b> dengan kalkulasi formula otomatis (Total, Rata-rata, Est. Saving) dan lembar <b>Data Mentah Per Jam</b>.
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn-modal-cancel"
              onClick={onClose}
              disabled={isDownloading}
            >
              Batal
            </button>
            <button
              type="submit"
              className="btn-modal-download"
              disabled={isDownloading}
            >
              {isDownloading ? "Menyiapkan Berkas…" : "📥 Unduh Excel (.xlsx)"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

