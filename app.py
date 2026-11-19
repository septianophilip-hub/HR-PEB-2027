import html
import re
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="HR PEB 2027", page_icon="💰", layout="wide")

# =====================================================================
#  KONSTANTA & GAYA
# =====================================================================
TAHAP = ["PR Submit", "Approval", "AP", "Finance", "Paid"]
BULAN_PENDEK = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
NAMA_BULAN = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "may": 5, "jun": 6, "jul": 7,
              "agu": 8, "aug": 8, "sep": 9, "okt": 10, "oct": 10, "nov": 11, "des": 12, "dec": 12}
ABAIKAN = {"idr", "usd", "description", "total", "no.", "no", "month", "desc", "budget",
           "realization", "remaining", "skk migas", "internal"}

BG, TXT, GRID = "#0e1a2b", "#cfd9ea", "#1f3350"
HIJAU, KUNING, MERAH, BIRU = "#2ecc71", "#f5a623", "#ff5c5c", "#3aa0ff"

st.markdown(f"""<style>
.fm-card{{background:{BG};border:1px solid {GRID};border-radius:12px;padding:14px 16px;margin-bottom:12px;color:#e8eef7}}
.fm-top{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}}
.fm-name{{font-weight:700;font-size:1.02rem;color:#ffffff}}
.fm-line{{font-size:.75rem;color:#8fa3bf}}
.fm-bar{{height:10px;background:#1b2b44;border-radius:6px;overflow:hidden;margin:6px 0 4px 0}}
.fm-fill{{height:100%;border-radius:6px}}
.fm-pct{{font-size:.78rem;color:#8fa3bf;margin-bottom:8px}}
.fm-row{{display:flex;justify-content:space-between;font-size:.88rem;padding:2px 0;color:#b8c7dd}}
.fm-row b{{color:#ffffff}}
.fm-row b.pos{{color:{HIJAU}}}
.fm-row b.neg{{color:{MERAH}}}
.fm-row b.mut{{color:#8fa3bf;font-weight:400}}
.pay-card{{background:{BG};border:1px solid {GRID};border-radius:12px;padding:12px 14px;margin-bottom:12px;color:#e8eef7}}
.pay-head{{display:flex;justify-content:space-between;align-items:baseline;gap:8px}}
.pay-title{{font-weight:700;color:#ffffff;font-size:.98rem}}
.pay-badge{{font-size:.75rem;color:{KUNING};white-space:nowrap}}
.pay-doc{{font-size:.8rem;color:#8fa3bf;margin-top:2px}}
.pay-doc b{{color:#e8eef7}}
.pay-amt{{font-size:.88rem;color:#b8c7dd;margin:6px 0 8px 0}}
.pay-amt b{{color:#ffffff}}
.chips{{display:flex;gap:5px;flex-wrap:wrap}}
.chip{{flex:1;min-width:64px;border-radius:8px;padding:5px 6px;font-size:.7rem;text-align:center}}
.chip small{{display:block;font-size:.68rem}}
.chip.on{{background:#10331f;border:1px solid {HIJAU};color:#bff5d3}}
.chip.on small{{color:#ffffff}}
.chip.off{{background:#16233a;border:1px solid #223756;color:#6f86a6}}
</style>""", unsafe_allow_html=True)


def usd(x):
    return f"USD {x:,.0f}"


def idr(x):
    return "Rp " + f"{x:,.0f}".replace(",", ".")


def gaya(chart, judul=None, tinggi=320):
    """Beri tampilan gelap ala Football Manager pada grafik."""
    if judul:
        chart = chart.properties(title=judul)
    return (chart.properties(height=tinggi, padding={"left": 12, "top": 12, "right": 12, "bottom": 12})
            .configure(background=BG)
            .configure_axis(labelColor=TXT, titleColor=TXT, gridColor=GRID, domainColor=GRID, tickColor=GRID)
            .configure_legend(labelColor=TXT, titleColor=TXT, orient="bottom")
            .configure_title(color="#ffffff", anchor="start", fontSize=14)
            .configure_view(stroke=None))


# =====================================================================
#  FUNGSI MEMBACA EXCEL
# =====================================================================
def kosong(x):
    try:
        if pd.isna(x):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(x, str):
        s = x.strip()
        return s == "" or s.startswith("#")
    return False


def angka(x):
    if kosong(x):
        return 0.0
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if pd.isna(v) else v


def teks_dok(x):
    if kosong(x):
        return ""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x).strip()


def parse_bulan(x):
    if not isinstance(x, str):
        return None
    t = x.strip().lower()
    m = re.search(r"(20\d\d)", t)
    bln = NAMA_BULAN.get(t[:3])
    if m and bln:
        return pd.Timestamp(int(m.group(1)), bln, 1)
    return None


def baca_tanggal(x):
    """Kembalikan (tanggal atau None, teks untuk ditampilkan)."""
    if kosong(x):
        return None, ""
    if isinstance(x, (int, float)):
        return None, str(x)
    t = pd.to_datetime(x, errors="coerce", dayfirst=True)
    if pd.isna(t):
        return None, str(x).strip()
    return t, t.strftime("%d/%m/%Y")


def baca_summary(xls):
    raw = xls.parse("Summary RKA", header=None)
    baris = None
    for i in range(len(raw)):
        if "Expenses" in raw.iloc[i].astype(str).values:
            baris = i
            break
    if baris is None:
        return None
    df = raw.iloc[baris + 1:, :].copy()
    df.columns = raw.iloc[baris].astype(str).values
    df = df.loc[:, ~df.columns.str.startswith("nan")]
    df = df[df["Expenses"].notna()]
    # berhenti di baris TOTAL; catatan di bawahnya tidak ikut dibaca
    total_idx = df.index[df["Expenses"].astype(str).str.strip().str.upper() == "TOTAL"]
    if len(total_idx):
        df = df.loc[: total_idx[0]].iloc[:-1]
    df = df[pd.to_numeric(df["Line"], errors="coerce").notna()]
    df["Realisasi Excel"] = pd.to_numeric(df["Realisasi (USD)"], errors="coerce")
    for k in ["Budget SKK (USD)", "Budget Internal (USD)"]:
        df[k] = pd.to_numeric(df[k], errors="coerce").fillna(0.0)
    return df[["Line", "Expenses", "Budget SKK (USD)", "Budget Internal (USD)", "Realisasi Excel"]].reset_index(drop=True)


def petakan_expense(judul, sheet, daftar):
    for e in daftar:
        if judul.strip().lower() == str(e).strip().lower():
            return e
    for e in daftar:
        if str(e).strip().lower() in sheet.lower():
            return e
    if "welfare" in sheet.lower():
        for e in daftar:
            if str(e).strip().lower() == "asuransi kesehatan":
                return e
    return None


def baca_detail(xls, daftar_expense):
    """Cari semua tabel pembayaran (yang punya kolom 'Docs No.') di semua sheet detail."""
    hasil, tak_terpetakan = [], set()
    for sheet in xls.sheet_names:
        if sheet.strip().lower() == "summary rka":
            continue
        g = xls.parse(sheet, header=None)
        n_r, n_c = g.shape
        for r in range(n_r - 1):
            for c in range(n_c):
                v = g.iat[r, c]
                if not (isinstance(v, str) and v.strip().lower().startswith("docs no")):
                    continue
                # kolom "No."
                no_col = None
                for cc in range(c - 1, max(c - 5, -1), -1):
                    t = g.iat[r, cc]
                    if isinstance(t, str) and t.strip().lower() in ("no.", "no"):
                        no_col = cc
                        break
                if no_col is None:
                    no_col = max(c - 2, 0)
                label_cols = list(range(no_col + 1, c))
                if not label_cols:
                    continue
                kepala = g.iat[r, label_cols[0]]
                tipe_bulan = isinstance(kepala, str) and kepala.strip().lower().startswith("month")
                # judul tabel (dicari ke atas)
                judul = ""
                for rr in range(r - 1, max(r - 11, -1), -1):
                    t = g.iat[rr, label_cols[0]]
                    if isinstance(t, str) and t.strip() and t.strip().lower() not in ABAIKAN:
                        judul = t.strip()
                        break
                expense = petakan_expense(judul, sheet, daftar_expense)
                if expense is None:
                    tak_terpetakan.add(f"{judul or '(tanpa judul)'} [{sheet}]")
                    expense = "Belum terpetakan"
                bulan_aktif, bulan_teks, no_aktif = None, "", ""
                for rr in range(r + 2, n_r):
                    no_val = g.iat[rr, no_col]
                    labels = [g.iat[rr, cc] for cc in label_cols]
                    if isinstance(no_val, str) and no_val.strip().lower() in ("no.", "no"):
                        break
                    if any(isinstance(t, str) and t.strip().lower() in ("total", "description")
                           for t in labels + [no_val]):
                        break
                    if tipe_bulan:
                        p = parse_bulan(labels[0])
                        if p is not None:
                            bulan_aktif, bulan_teks = p, str(labels[0]).strip()
                        item = str(labels[-1]).strip() if len(labels) > 1 and not kosong(labels[-1]) else ""
                    else:
                        item = " ".join(str(x).strip() for x in labels if not kosong(x))
                    if not kosong(no_val):
                        no_aktif = teks_dok(no_val)
                    docs = g.iat[rr, c]
                    nominal = angka(g.iat[rr, c + 1]) if c + 1 < n_c else 0.0
                    kurs = angka(g.iat[rr, c + 2]) if c + 2 < n_c else 0.0
                    tahap = [g.iat[rr, c + 4 + i] if c + 4 + i < n_c else None for i in range(5)]
                    if not (not kosong(docs) or nominal > 0 or any(not kosong(t) for t in tahap)):
                        continue
                    if kurs > 0:
                        nilai_usd = nominal / kurs
                    else:
                        nilai_usd = angka(g.iat[rr, c + 3]) if c + 3 < n_c else 0.0
                    tgl, teks = [], []
                    for t in tahap:
                        d, s = baca_tanggal(t)
                        tgl.append(d)
                        teks.append(s)
                    terakhir = "Belum diproses"
                    for i in range(4, -1, -1):
                        if teks[i]:
                            terakhir = TAHAP[i]
                            break
                    valid = [d for d in tgl if d is not None]
                    if tipe_bulan and bulan_aktif is not None:
                        periode = bulan_aktif
                    elif valid:
                        periode = min(valid).replace(day=1).normalize()
                    else:
                        periode = pd.NaT
                    if tipe_bulan and bulan_teks:
                        label_bulan = bulan_teks
                    elif valid:
                        label_bulan = BULAN_PENDEK[min(valid).month - 1] + " " + str(min(valid).year)
                    else:
                        label_bulan = "-"
                    baris = {"Expense": expense, "Kategori": judul, "No": no_aktif, "Bulan": label_bulan,
                             "Item": item, "No. Dokumen": teks_dok(docs), "IDR": nominal, "Kurs": kurs,
                             "USD": nilai_usd, "Periode": periode, "Status Terakhir": terakhir,
                             "Kurs kosong": nominal > 0 and kurs <= 0}
                    for i, nama in enumerate(TAHAP):
                        baris[nama] = teks[i]
                    hasil.append(baris)
    df = pd.DataFrame(hasil)
    if not df.empty:
        df["Periode"] = pd.to_datetime(df["Periode"])
    return df, sorted(tak_terpetakan)


# =====================================================================
#  UPLOAD
# =====================================================================
st.title("👋 Halo, Philip")
st.subheader("HR PEB 2027 · RKA Budget Tracker")
st.caption("Upload file Excel monitoring Anda. Data hanya dibaca sementara dan tidak disimpan di server.")

file = st.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])
if not file:
    st.info("Silakan upload file Excel dulu.")
    st.stop()

try:
    xls = pd.ExcelFile(file)
    data = baca_summary(xls)
except Exception as e:
    st.error(f"Gagal membaca file. Pastikan ada sheet bernama 'Summary RKA'. Detail: {e}")
    st.stop()

if data is None or data.empty:
    st.error("Tabel di sheet 'Summary RKA' tidak ditemukan.")
    st.stop()

try:
    trx, tak_terpetakan = baca_detail(xls, data["Expenses"].tolist())
except Exception as e:
    trx, tak_terpetakan = pd.DataFrame(), []
    st.warning(f"Detail pembayaran belum bisa dibaca ({e}). Dashboard memakai angka dari sheet Summary RKA.")

if tak_terpetakan:
    st.warning("Tabel berikut belum cocok dengan nama di Summary RKA: " + "; ".join(tak_terpetakan))

# =====================================================================
#  PERHITUNGAN
# =====================================================================
basis = st.radio("Basis budget", ["SKK", "Internal"], horizontal=True)
kolom_budget = "Budget SKK (USD)" if basis == "SKK" else "Budget Internal (USD)"
data["Budget"] = data[kolom_budget]

if trx.empty:
    data["Realisasi"] = data["Realisasi Excel"].fillna(0.0)
else:
    data["Realisasi"] = data["Expenses"].map(trx.groupby("Expense")["USD"].sum()).fillna(0.0)

if data["Budget"].sum() == 0:
    st.warning(f"Budget {basis} di sheet Summary masih 0 semua, jadi persentase tidak bisa dihitung.")

data["Total Terpakai"] = data["Realisasi"]
data["Sisa"] = data["Budget"] - data["Total Terpakai"]
data["Persen"] = (data["Total Terpakai"] / data["Budget"]).where(data["Budget"] > 0, 0.0)
# Realisasi dibebankan ke basis yang dipilih; budget lainnya ditampilkan utuh
if basis == "SKK":
    data["Sisa SKK"] = data["Budget SKK (USD)"] - data["Total Terpakai"]
    data["Sisa Internal"] = data["Budget Internal (USD)"]
else:
    data["Sisa SKK"] = data["Budget SKK (USD)"]
    data["Sisa Internal"] = data["Budget Internal (USD)"] - data["Total Terpakai"]

urutan = data["Expenses"].tolist()

# =====================================================================
#  BAGIAN ATAS: ANGKA BUDGET
# =====================================================================
total_budget = data["Budget"].sum()
total_pakai = data["Total Terpakai"].sum()
total_sisa = total_budget - total_pakai
persen_total = total_pakai / total_budget if total_budget > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Budget", usd(total_budget))
c2.metric("Terpakai", usd(total_pakai))
c3.metric("Sisa", usd(total_sisa))
c4.metric("Utilisasi", f"{persen_total:.1%}")
st.progress(min(max(persen_total, 0.0), 1.0))

st.divider()

# =====================================================================
#  BAGIAN TENGAH: GRAFIK
# =====================================================================
st.header("📊 Grafik Budget")


def kartu(r):
    p = r["Persen"]
    warna = MERAH if p >= 1 else (KUNING if p >= 0.8 else HIJAU)
    lebar = min(max(p, 0), 1) * 100
    pct_txt = f"{p:.0%} terpakai" if r["Budget"] > 0 else "budget belum diisi"

    def baris_sisa(nama, budget, sisa):
        if budget <= 0 and sisa == 0:
            return f'<div class="fm-row"><span>{nama}</span><b class="mut">belum ada budget</b></div>'
        kelas = "neg" if sisa < 0 else "pos"
        return f'<div class="fm-row"><span>{nama}</span><b class="{kelas}">{usd(sisa)}</b></div>'

    return (f'<div class="fm-card"><div class="fm-top"><span class="fm-name">{html.escape(str(r["Expenses"]))}</span>'
            f'<span class="fm-line">Line {html.escape(str(r["Line"]))}</span></div>'
            f'<div class="fm-bar"><div class="fm-fill" style="width:{lebar:.0f}%;background:{warna}"></div></div>'
            f'<div class="fm-pct">{pct_txt}</div>'
            f'<div class="fm-row"><span>Terpakai</span><b>{usd(r["Total Terpakai"])}</b></div>'
            f'{baris_sisa("Sisa SKK", r["Budget SKK (USD)"], r["Sisa SKK"])}'
            f'{baris_sisa("Sisa Internal", r["Budget Internal (USD)"], r["Sisa Internal"])}</div>')


kolom_kartu = st.columns(4)
for i, (_, r) in enumerate(data.iterrows()):
    with kolom_kartu[i % 4]:
        st.markdown(kartu(r), unsafe_allow_html=True)
st.caption(f"Realisasi dibebankan ke budget {basis} (sesuai pilihan basis di atas). Budget lainnya ditampilkan utuh.")

# --- tahun & deret bulanan keseluruhan
if not trx.empty and trx["Periode"].notna().any():
    tahun = int(trx["Periode"].dropna().dt.year.mode().iloc[0])
else:
    tahun = 2027


def deret_bulanan(df):
    b = pd.DataFrame({"Periode": [pd.Timestamp(tahun, m, 1) for m in range(1, 13)], "Bulan": BULAN_PENDEK})
    if df is not None and not df.empty:
        g = df.dropna(subset=["Periode"]).groupby("Periode")["USD"].sum()
        b["Pengeluaran"] = b["Periode"].map(g).fillna(0.0)
    else:
        b["Pengeluaran"] = 0.0
    return b


g1, g2 = st.columns(2)

with g1:
    ov = data[["Expenses", "Budget", "Total Terpakai", "Sisa", "Persen"]].copy()
    panjang = pd.concat([
        pd.DataFrame({"Expenses": ov["Expenses"], "Jenis": "Terpakai", "Nilai": ov["Total Terpakai"], "Urut": 0}),
        pd.DataFrame({"Expenses": ov["Expenses"], "Jenis": "Sisa", "Nilai": ov["Sisa"].clip(lower=0), "Urut": 1}),
    ])
    batang = alt.Chart(panjang).mark_bar().encode(
        y=alt.Y("Expenses:N", sort=urutan, title=None),
        x=alt.X("Nilai:Q", stack="zero", title="USD"),
        color=alt.Color("Jenis:N", scale=alt.Scale(domain=["Terpakai", "Sisa"], range=[KUNING, BIRU]),
                        legend=alt.Legend(title=None)),
        order=alt.Order("Urut:Q"),
        tooltip=[alt.Tooltip("Expenses:N"), alt.Tooltip("Jenis:N"), alt.Tooltip("Nilai:Q", format=",.0f")])
    ov["Ujung"] = ov[["Budget", "Total Terpakai"]].max(axis=1)
    ov["Label"] = ov.apply(lambda r: f"{r['Persen']:.0%}" if r["Budget"] > 0 else "-", axis=1)
    teks = alt.Chart(ov).mark_text(align="left", dx=5, color=TXT).encode(
        y=alt.Y("Expenses:N", sort=urutan), x="Ujung:Q", text="Label:N")
    st.altair_chart(gaya(batang + teks, f"Budget {basis}: terpakai vs sisa per kategori", 340), width="stretch")

with g2:
    bln_all = deret_bulanan(trx)
    aktif = bln_all[bln_all["Pengeluaran"] > 0]
    if total_budget > 0 and not aktif.empty:
        terakhir = aktif.index.max()
        sisa_list = [("Awal", total_budget)]
        kum = 0.0
        for idx in range(terakhir + 1):
            kum += bln_all.loc[idx, "Pengeluaran"]
            sisa_list.append((bln_all.loc[idx, "Bulan"], total_budget - kum))
        d_sisa = pd.DataFrame(sisa_list, columns=["Label", "Sisa"])
        urut_x = ["Awal"] + BULAN_PENDEK
        dasar = alt.Chart(d_sisa).encode(
            x=alt.X("Label:N", sort=urut_x, title=None, axis=alt.Axis(labelAngle=0),
                    scale=alt.Scale(domain=urut_x)),
            y=alt.Y("Sisa:Q", title="USD", scale=alt.Scale(domain=[0, total_budget * 1.03])),
            tooltip=[alt.Tooltip("Label:N", title="Akhir bulan"), alt.Tooltip("Sisa:Q", title="Sisa budget", format=",.0f")])
        area = dasar.mark_area(color=HIJAU, opacity=0.25, line={"color": HIJAU})
        titik = dasar.mark_point(color=HIJAU, filled=True, size=70)
        st.altair_chart(gaya(area + titik, f"Pergerakan sisa budget {basis} per bulan (semua kategori)", 340), width="stretch")
    else:
        st.info("Grafik pergerakan sisa budget akan muncul setelah ada pembayaran yang punya tanggal atau bulan di Excel.")

if not trx.empty:
    tanpa_bulan = int(trx["Periode"].isna().sum())
    if tanpa_bulan:
        st.caption(f"⚠️ {tanpa_bulan} pembayaran belum punya bulan/tanggal proses, jadi belum masuk grafik bulanan "
                   "(isi tanggal PR Submit di Excel).")

st.divider()

# =====================================================================
#  BAGIAN BAWAH: DETAIL PER KATEGORI
# =====================================================================
st.header("📋 Detail per Kategori")


def no_line(x):
    try:
        return str(int(float(x)))
    except (TypeError, ValueError):
        return str(x)


pilihan = [f"{no_line(r['Line'])} - {r['Expenses']}" for _, r in data.iterrows()]
pilih = st.selectbox("Pilih kategori", pilihan)
r = data.iloc[pilihan.index(pilih)]
nama = r["Expenses"]

t = trx[trx["Expense"] == nama].copy() if not trx.empty else pd.DataFrame()
sudah_paid = t.loc[t["Paid"] != "", "USD"].sum() if not t.empty else 0.0


def nilai_budget(x):
    return usd(x) if x > 0 else "Belum diisi"


st.markdown(f"### {pilih}")
d1, d2, d3, d4, d5 = st.columns(5)
d1.metric("Budget SKK", nilai_budget(r["Budget SKK (USD)"]))
d2.metric("Budget Internal", nilai_budget(r["Budget Internal (USD)"]))
d3.metric("Sudah keluar", usd(r["Total Terpakai"]))
d4.metric("Sisa SKK", usd(r["Sisa SKK"]))
d5.metric("Sisa Internal", usd(r["Sisa Internal"]) if (r["Budget Internal (USD)"] > 0 or r["Sisa Internal"] != 0) else "Belum diisi")
if r["Budget"] > 0:
    st.progress(min(max(r["Persen"], 0.0), 1.0))
    st.caption(f"{r['Persen']:.1%} dari budget {basis} sudah terpakai. "
               f"Dari total yang keluar, {usd(sudah_paid)} sudah berstatus Paid.")

if t.empty:
    st.info("Belum ada pembayaran yang terisi untuk kategori ini di Excel.")
else:
    bln = deret_bulanan(t)
    aktif_k = bln[bln["Pengeluaran"] > 0]
    rata = aktif_k["Pengeluaran"].mean() if len(aktif_k) else 0.0
    jatah = r["Budget"] / 12 if r["Budget"] > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"Total ({len(t)} pembayaran)", usd(t["USD"].sum()))
    m2.metric("Rata-rata per bulan", usd(rata) if len(aktif_k) else "-")
    if len(aktif_k):
        puncak = aktif_k.loc[aktif_k["Pengeluaran"].idxmax()]
        m3.metric("Bulan tertinggi", f"{puncak['Bulan']} ({usd(puncak['Pengeluaran'])})")
    else:
        m3.metric("Bulan tertinggi", "-")
    if len(aktif_k) >= 2:
        selisih = aktif_k["Pengeluaran"].iloc[-1] - aktif_k["Pengeluaran"].iloc[-2]
        arah = "naik" if selisih > 0 else ("turun" if selisih < 0 else "stabil")
        m4.metric(f"Tren ({aktif_k['Bulan'].iloc[-1]} vs {aktif_k['Bulan'].iloc[-2]})",
                  arah.capitalize(), f"{selisih:+,.0f} USD", delta_color="inverse")
    else:
        m4.metric("Tren", "-", help="Butuh minimal 2 bulan yang ada pengeluaran")

    if len(aktif_k):
        k1, k2 = st.columns(2)
        with k1:
            bar = alt.Chart(bln).mark_bar(color=BIRU, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                x=alt.X("Bulan:N", sort=BULAN_PENDEK, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Pengeluaran:Q", title="USD"),
                tooltip=[alt.Tooltip("Bulan:N"), alt.Tooltip("Pengeluaran:Q", format=",.0f")])
            nama_rata, nama_jatah = "Rata-rata per bulan", "Jatah per bulan (budget ÷ 12)"
            garis_df = pd.DataFrame({"Garis": [nama_rata, nama_jatah], "Nilai": [rata, jatah]})
            garis_df = garis_df[garis_df["Nilai"] > 0]
            garis = alt.Chart(garis_df).mark_rule(strokeWidth=2).encode(
                y="Nilai:Q",
                color=alt.Color("Garis:N", scale=alt.Scale(domain=[nama_rata, nama_jatah], range=[KUNING, HIJAU]),
                                legend=alt.Legend(title=None)),
                strokeDash=alt.StrokeDash("Garis:N", scale=alt.Scale(domain=[nama_rata, nama_jatah],
                                                                     range=[[1, 0], [6, 4]]), legend=None))
            st.altair_chart(gaya(bar + garis, f"{nama}: pengeluaran per bulan", 300), width="stretch")
        with k2:
            bln["Kumulatif"] = bln["Pengeluaran"].cumsum()
            sampai = bln[bln["Pengeluaran"] > 0].index.max()
            kum_df = bln.loc[:sampai]
            batas = max(r["Budget"], kum_df["Kumulatif"].max()) * 1.05
            garis_kum = alt.Chart(kum_df).mark_line(color=KUNING, point=alt.OverlayMarkDef(color=KUNING, size=70)).encode(
                x=alt.X("Bulan:N", sort=BULAN_PENDEK, title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Kumulatif:Q", title="USD", scale=alt.Scale(domain=[0, batas])),
                tooltip=[alt.Tooltip("Bulan:N"), alt.Tooltip("Kumulatif:Q", format=",.0f", title="Total terpakai")])
            lapis = garis_kum
            if r["Budget"] > 0:
                batas_budget = alt.Chart(pd.DataFrame({"y": [r["Budget"]]})).mark_rule(
                    color=MERAH, strokeDash=[6, 4], strokeWidth=2).encode(y="y:Q")
                lapis = garis_kum + batas_budget
            st.altair_chart(gaya(lapis, f"{nama}: progres pengeluaran (garis merah = budget {basis})", 300),
                            width="stretch")
    else:
        st.info("Grafik bulanan akan muncul setelah pembayaran punya bulan atau tanggal proses (mis. tanggal PR Submit).")

    # --- rincian pembayaran (kartu siap presentasi)
    st.markdown("#### Rincian setiap pembayaran")
    banyak_sub = t["Kategori"].nunique() > 1

    def kartu_bayar(b):
        bagian = []
        if banyak_sub and b["Kategori"]:
            bagian.append(b["Kategori"])
        if b["Item"]:
            bagian.append(b["Item"])
        if b["Bulan"] and b["Bulan"] != "-":
            bagian.append(b["Bulan"])
        judul = " • ".join(bagian) if bagian else "Pembayaran"
        no = f"#{b['No']} " if b["No"] else ""
        dok = f"No. Dokumen: <b>{html.escape(b['No. Dokumen'])}</b>" if b["No. Dokumen"] else "No. Dokumen: belum diisi"
        kurs_txt = f" @ {b['Kurs']:,.0f}".replace(",", ".") if b["Kurs"] > 0 else " (kurs belum diisi)"
        chips = ""
        for nama_tahap in TAHAP:
            isi = b[nama_tahap]
            if isi:
                chips += f'<div class="chip on">{nama_tahap}<small>{html.escape(isi)}</small></div>'
            else:
                chips += f'<div class="chip off">{nama_tahap}<small>-</small></div>'
        status = b["Status Terakhir"]
        badge = "✅ Paid" if status == "Paid" else status
        return (f'<div class="pay-card"><div class="pay-head"><span class="pay-title">{no}{html.escape(judul)}</span>'
                f'<span class="pay-badge">{html.escape(badge)}</span></div>'
                f'<div class="pay-doc">{dok}</div>'
                f'<div class="pay-amt">{idr(b["IDR"])}{kurs_txt} = <b>USD {b["USD"]:,.2f}</b></div>'
                f'<div class="chips">{chips}</div></div>')

    kolom_bayar = st.columns(2)
    for i, (_, b) in enumerate(t.iterrows()):
        with kolom_bayar[i % 2]:
            st.markdown(kartu_bayar(b), unsafe_allow_html=True)
    st.caption(f"Total: {idr(t['IDR'].sum())}  •  {usd(t['USD'].sum())}  •  {len(t)} pembayaran")
    if t["Kurs kosong"].any():
        st.warning(f"{int(t['Kurs kosong'].sum())} pembayaran punya nominal IDR tetapi Kurs masih kosong, "
                   "sehingga nilai USD-nya dihitung 0.")

    with st.expander("Lihat sebagai tabel"):
        tampil = t.copy()
        tampil["IDR"] = tampil["IDR"].apply(idr)
        tampil["Kurs"] = tampil["Kurs"].apply(lambda x: f"{x:,.0f}".replace(",", ".") if x > 0 else "-")
        tampil["USD"] = tampil["USD"].apply(lambda x: f"{x:,.2f}")
        kolom_tampil = ["No", "Kategori", "Bulan", "Item", "No. Dokumen", "IDR", "Kurs", "USD"] + TAHAP + ["Status Terakhir"]
        if not banyak_sub:
            kolom_tampil.remove("Kategori")
        if (tampil["Item"] == "").all():
            kolom_tampil.remove("Item")
        st.dataframe(tampil[kolom_tampil], hide_index=True, width="stretch")

# =====================================================================
#  CEK KONSISTENSI
# =====================================================================
st.divider()
with st.expander("🔎 Cek konsistensi dengan sheet Summary RKA"):
    cek = data[["Expenses", "Realisasi Excel", "Realisasi"]].copy()

    def catatan(r):
        if pd.isna(r["Realisasi Excel"]):
            return "Summary Excel error (#DIV/0!). Dashboard menghitung sendiri dari rincian."
        if abs(r["Realisasi Excel"] - r["Realisasi"]) > 1:
            return "Ada selisih, mohon dicek."
        return "Sama"

    cek["Catatan"] = cek.apply(catatan, axis=1)
    cek = cek.rename(columns={"Realisasi Excel": "Realisasi di Summary (USD)", "Realisasi": "Realisasi di Dashboard (USD)"})
    st.dataframe(cek, hide_index=True, width="stretch")
