import io
from datetime import date, datetime, time, timedelta
from django.utils import timezone
from django.db.models import Sum, Max
from django.db.models.functions import TruncDate
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from .services import calc, reference_time, local_midnight


def build_performance_excel(site, start_date=None, end_date=None):
    """
    Menghasilkan file Excel (.xlsx) data performance test site
    dengan desain minimalis sesuai tema Mobius Dashboard.
    """
    ref = reference_time(site)
    ref_date = timezone.localtime(ref).date()

    if not end_date:
        end_date = ref_date
    if not start_date:
        start_date = end_date - timedelta(days=29)

    # Convert to timezone-aware range
    start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
    end_dt = timezone.make_aware(datetime.combine(end_date, time.max))

    # Query daily data
    daily_qs = (
        site.readings.filter(ts__gte=start_dt, ts__lte=end_dt)
        .annotate(day=TruncDate("ts"))
        .values("day")
        .annotate(pln=Sum("pln_kwh"), mobius=Sum("mobius_kwh"))
        .order_by("day")
    )

    daily_rows = [
        {"date": r["day"], **calc(r["pln"], r["mobius"], site.tariff_per_kwh)}
        for r in daily_qs
    ]

    # Query hourly raw data
    hourly_qs = (
        site.readings.filter(ts__gte=start_dt, ts__lte=end_dt)
        .order_by("ts")
    )
    hourly_rows = [
        {
            "ts": timezone.localtime(r.ts),
            **calc(r.pln_kwh, r.mobius_kwh, site.tariff_per_kwh),
        }
        for r in hourly_qs
    ]

    # Initialize openpyxl workbook
    wb = openpyxl.Workbook()

    # Palette
    C_SLATE = "12303A"       # Header utama
    C_BRAND = "C5192D"       # Aksen Merah Mobius
    C_BRAND_LIGHT = "FEF2F3"
    C_SURFACE_ALT = "F4F8FA" # Latar kartu / zebra baris
    C_LINE = "D3DFE3"        # Border tipis
    C_WHITE = "FFFFFF"
    C_MUTED = "5B727C"
    C_POC = "0E9A55"         # Hijau Mobius
    C_PLN = "2563D8"         # Biru PLN
    C_LOAD = "9A6700"        # Oranye / Gold Load

    # Fonts
    font_title = Font(name="Segoe UI", size=15, bold=True, color=C_SLATE)
    font_subtitle = Font(name="Segoe UI", size=10, italic=True, color=C_MUTED)
    font_section = Font(name="Segoe UI", size=11, bold=True, color=C_SLATE)
    font_th = Font(name="Segoe UI", size=10, bold=True, color=C_WHITE)
    font_body = Font(name="Segoe UI", size=10, color=C_SLATE)
    font_body_bold = Font(name="Segoe UI", size=10, bold=True, color=C_SLATE)
    font_body_poc = Font(name="Segoe UI", size=10, bold=True, color=C_POC)
    font_body_pln = Font(name="Segoe UI", size=10, color=C_PLN)
    font_body_load = Font(name="Segoe UI", size=10, bold=True, color=C_LOAD)
    font_kpi_label = Font(name="Segoe UI", size=8, bold=True, color=C_MUTED)
    font_kpi_val = Font(name="Segoe UI", size=13, bold=True, color=C_SLATE)

    # Fills
    fill_header = PatternFill(start_color=C_SLATE, end_color=C_SLATE, fill_type="solid")
    fill_alt = PatternFill(start_color=C_SURFACE_ALT, end_color=C_SURFACE_ALT, fill_type="solid")
    fill_meta = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_brand_light = PatternFill(start_color=C_BRAND_LIGHT, end_color=C_BRAND_LIGHT, fill_type="solid")
    fill_total = PatternFill(start_color="E9F0F2", end_color="E9F0F2", fill_type="solid")

    # Borders
    thin_side = Side(border_style="thin", color=C_LINE)
    border_all = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    border_bottom_double = Border(left=thin_side, right=thin_side, top=thin_side, bottom=Side(border_style="double", color=C_SLATE))

    # Alignments
    align_left = Alignment(horizontal="left", vertical="center")
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # Number Formats
    FMT_KWH = "#,##0.00"
    FMT_PCT = "0.0%"
    FMT_RP = '"Rp "#,##0'
    FMT_DATE = "YYYY-MM-DD"
    FMT_DATETIME = "YYYY-MM-DD HH:MM"

    # =========================================================================
    # SHEET 1: RINGKASAN HARIAN
    # =========================================================================
    ws1 = wb.active
    ws1.title = "Kinerja Harian"
    ws1.views.sheetView[0].showGridLines = True

    # 1. Judul Laporan
    ws1["A1"] = "MOBIUS PoC PERFORMANCE TEST REPORT"
    ws1["A1"].font = font_title
    ws1["A2"] = f"Laporan Kinerja Penghematan Energi • Periode: {start_date.isoformat()} s/d {end_date.isoformat()}"
    ws1["A2"].font = font_subtitle

    # 2. Kotak Metadata Site (Row 4-6)
    region_name = site.region.name if site.region else "-"
    meta_info = [
        ("Site ID", site.code, "Wilayah", region_name),
        ("Lokasi", site.area, "Unit PoC", site.mobius_unit or "-"),
        ("Rated Load", f"{site.rated_load_kw} kW", "Tarif PLN", f"Rp {site.tariff_per_kwh:,.2f} / kWh"),
    ]

    for r_idx, row_data in enumerate(meta_info, start=4):
        ws1[f"A{r_idx}"] = row_data[0]
        ws1[f"A{r_idx}"].font = Font(name="Segoe UI", size=9, bold=True, color=C_MUTED)
        ws1[f"A{r_idx}"].fill = fill_meta
        ws1[f"A{r_idx}"].border = border_all

        ws1[f"B{r_idx}"] = row_data[1]
        ws1[f"B{r_idx}"].font = font_body_bold
        ws1[f"B{r_idx}"].fill = fill_meta
        ws1[f"B{r_idx}"].border = border_all

        ws1[f"C{r_idx}"] = ""
        ws1[f"C{r_idx}"].fill = fill_meta
        ws1[f"C{r_idx}"].border = border_all

        ws1[f"D{r_idx}"] = row_data[2]
        ws1[f"D{r_idx}"].font = Font(name="Segoe UI", size=9, bold=True, color=C_MUTED)
        ws1[f"D{r_idx}"].fill = fill_meta
        ws1[f"D{r_idx}"].border = border_all

        ws1[f"E{r_idx}"] = row_data[3]
        ws1[f"E{r_idx}"].font = font_body_bold
        ws1[f"E{r_idx}"].fill = fill_meta
        ws1[f"E{r_idx}"].border = border_all

        ws1[f"F{r_idx}"] = ""
        ws1[f"F{r_idx}"].fill = fill_meta
        ws1[f"F{r_idx}"].border = border_all

        ws1[f"G{r_idx}"] = ""
        ws1[f"G{r_idx}"].fill = fill_meta
        ws1[f"G{r_idx}"].border = border_all

        ws1.merge_cells(f"B{r_idx}:C{r_idx}")
        ws1.merge_cells(f"E{r_idx}:G{r_idx}")

    # 3. Header Tabel Harian (Row 8)
    table_headers = [
        ("A8", "No.", align_center),
        ("B8", "Tanggal", align_center),
        ("C8", "Beban / Load (kWh)", align_right),
        ("D8", "Pasokan PLN (kWh)", align_right),
        ("E8", "Pasokan PoC (kWh)", align_right),
        ("F8", "Kontribusi PoC (%)", align_right),
        ("G8", "Est. Penghematan (Rp)", align_right),
    ]

    for cell_ref, text, aln in table_headers:
        cell = ws1[cell_ref]
        cell.value = text
        cell.font = font_th
        cell.fill = fill_header
        cell.alignment = aln
        cell.border = border_all
    ws1.row_dimensions[8].height = 24

    # 4. Data Rows
    start_row = 9
    current_row = start_row

    for idx, row in enumerate(daily_rows, start=1):
        is_even = idx % 2 == 0
        row_fill = fill_alt if is_even else None

        c_no = ws1.cell(row=current_row, column=1, value=idx)
        c_no.alignment = align_center

        c_date = ws1.cell(row=current_row, column=2, value=row["date"])
        c_date.alignment = align_center
        c_date.number_format = FMT_DATE

        c_load = ws1.cell(row=current_row, column=3, value=row["load_kwh"])
        c_load.alignment = align_right
        c_load.number_format = FMT_KWH
        c_load.font = font_body_load

        c_pln = ws1.cell(row=current_row, column=4, value=row["pln_kwh"])
        c_pln.alignment = align_right
        c_pln.number_format = FMT_KWH
        c_pln.font = font_body_pln

        c_poc = ws1.cell(row=current_row, column=5, value=row["mobius_kwh"])
        c_poc.alignment = align_right
        c_poc.number_format = FMT_KWH
        c_poc.font = font_body_poc

        # Contribution pct as fraction for Excel percentage format (e.g. 0.185 -> 18.5%)
        pct_val = (row["contribution_pct"] / 100.0) if row["contribution_pct"] else 0.0
        c_pct = ws1.cell(row=current_row, column=6, value=pct_val)
        c_pct.alignment = align_right
        c_pct.number_format = FMT_PCT
        c_pct.font = font_body_bold

        c_save = ws1.cell(row=current_row, column=7, value=row["saving_rp"])
        c_save.alignment = align_right
        c_save.number_format = FMT_RP
        c_save.font = font_body_bold

        for col in range(1, 8):
            cell = ws1.cell(row=current_row, column=col)
            cell.border = border_all
            if not cell.font or cell.font == font_body:
                cell.font = font_body
            if row_fill and col not in (3, 5): # biarkan sedikit kontras
                cell.fill = row_fill

        ws1.row_dimensions[current_row].height = 20
        current_row += 1

    last_data_row = current_row - 1

    # 5. Summary / Total Row
    if daily_rows:
        ws1.cell(row=current_row, column=1, value="")
        ws1.cell(row=current_row, column=2, value="TOTAL")
        ws1.cell(row=current_row, column=2).font = font_body_bold
        ws1.cell(row=current_row, column=2).alignment = align_center

        ws1.cell(row=current_row, column=3, value=f"=SUM(C{start_row}:C{last_data_row})").number_format = FMT_KWH
        ws1.cell(row=current_row, column=4, value=f"=SUM(D{start_row}:D{last_data_row})").number_format = FMT_KWH
        ws1.cell(row=current_row, column=5, value=f"=SUM(E{start_row}:E{last_data_row})").number_format = FMT_KWH
        ws1.cell(row=current_row, column=6, value=f"=E{current_row}/C{current_row}").number_format = FMT_PCT
        ws1.cell(row=current_row, column=7, value=f"=SUM(G{start_row}:G{last_data_row})").number_format = FMT_RP

        for col in range(1, 8):
            cell = ws1.cell(row=current_row, column=col)
            cell.fill = fill_total
            cell.font = font_body_bold
            cell.border = border_all
            if col >= 3:
                cell.alignment = align_right

        current_row += 1

        # Average Row
        ws1.cell(row=current_row, column=1, value="")
        ws1.cell(row=current_row, column=2, value="RATA-RATA").font = font_body_bold
        ws1.cell(row=current_row, column=2).alignment = align_center

        ws1.cell(row=current_row, column=3, value=f"=AVERAGE(C{start_row}:C{last_data_row})").number_format = FMT_KWH
        ws1.cell(row=current_row, column=4, value=f"=AVERAGE(D{start_row}:D{last_data_row})").number_format = FMT_KWH
        ws1.cell(row=current_row, column=5, value=f"=AVERAGE(E{start_row}:E{last_data_row})").number_format = FMT_KWH
        ws1.cell(row=current_row, column=6, value=f"=AVERAGE(F{start_row}:F{last_data_row})").number_format = FMT_PCT
        ws1.cell(row=current_row, column=7, value=f"=AVERAGE(G{start_row}:G{last_data_row})").number_format = FMT_RP

        for col in range(1, 8):
            cell = ws1.cell(row=current_row, column=col)
            cell.fill = fill_alt
            cell.font = font_body_bold
            cell.border = border_bottom_double
            if col >= 3:
                cell.alignment = align_right

    # =========================================================================
    # SHEET 2: DETAIL DATA PER JAM (RAW HOURLY READINGS)
    # =========================================================================
    ws2 = wb.create_sheet(title="Data Mentah Per Jam")
    ws2.views.sheetView[0].showGridLines = True

    ws2["A1"] = f"DATA PEMBACAAN ENERGI PER JAM - SITE {site.code}"
    ws2["A1"].font = font_title
    ws2["A2"] = f"Total {len(hourly_rows)} baris data jam • Periode: {start_date.isoformat()} s/d {end_date.isoformat()}"
    ws2["A2"].font = font_subtitle

    h_headers = [
        ("A4", "No.", align_center),
        ("B4", "Waktu (Timestamp)", align_center),
        ("C4", "Jam", align_center),
        ("D4", "Beban / Load (kWh)", align_right),
        ("E4", "Pasokan PLN (kWh)", align_right),
        ("F4", "Pasokan PoC (kWh)", align_right),
        ("G4", "Kontribusi PoC (%)", align_right),
        ("H4", "Est. Penghematan (Rp)", align_right),
    ]

    for cell_ref, text, aln in h_headers:
        cell = ws2[cell_ref]
        cell.value = text
        cell.font = font_th
        cell.fill = fill_header
        cell.alignment = aln
        cell.border = border_all
    ws2.row_dimensions[4].height = 22

    h_row_curr = 5
    for h_idx, h_data in enumerate(hourly_rows, start=1):
        is_even = h_idx % 2 == 0
        r_fill = fill_alt if is_even else None

        c_no = ws2.cell(row=h_row_curr, column=1, value=h_idx)
        c_no.alignment = align_center

        c_ts = ws2.cell(row=h_row_curr, column=2, value=h_data["ts"].strftime("%Y-%m-%d %H:%M"))
        c_ts.alignment = align_center

        c_hr = ws2.cell(row=h_row_curr, column=3, value=h_data["ts"].strftime("%H:00"))
        c_hr.alignment = align_center

        c_load = ws2.cell(row=h_row_curr, column=4, value=h_data["load_kwh"])
        c_load.alignment = align_right
        c_load.number_format = FMT_KWH

        c_pln = ws2.cell(row=h_row_curr, column=5, value=h_data["pln_kwh"])
        c_pln.alignment = align_right
        c_pln.number_format = FMT_KWH

        c_poc = ws2.cell(row=h_row_curr, column=6, value=h_data["mobius_kwh"])
        c_poc.alignment = align_right
        c_poc.number_format = FMT_KWH
        c_poc.font = font_body_poc

        h_pct = (h_data["contribution_pct"] / 100.0) if h_data["contribution_pct"] else 0.0
        c_pct = ws2.cell(row=h_row_curr, column=7, value=h_pct)
        c_pct.alignment = align_right
        c_pct.number_format = FMT_PCT

        c_save = ws2.cell(row=h_row_curr, column=8, value=h_data["saving_rp"])
        c_save.alignment = align_right
        c_save.number_format = FMT_RP

        for col in range(1, 9):
            cell = ws2.cell(row=h_row_curr, column=col)
            cell.border = border_all
            if not cell.font:
                cell.font = font_body
            if r_fill and col != 6:
                cell.fill = r_fill

        h_row_curr += 1

    # Auto-adjust column widths for both sheets
    for ws in [ws1, ws2]:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = cell.value
                if val is not None:
                    # Ignore title in A1 when computing width
                    if cell.row in (1, 2) and col_letter == "A":
                        continue
                    length = len(str(val))
                    if length > max_len:
                        max_len = length
            ws.column_dimensions[col_letter].width = max(max_len + 5, 12)

    # Save to buffer
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()

