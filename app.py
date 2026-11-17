import streamlit as st
import pandas as pd

st.set_page_config(page_title="HR PEB 2027", page_icon="💰", layout="wide")

# ---------- Fungsi bantu ----------
def usd(x):
    return f"USD {x:,.0f}"

def baca_summary(file):
    """Baca tabel di sheet 'Summary RKA' (cari baris yang berisi 'Expenses')."""
    raw = pd.read_excel(file, sheet_name="Summary RKA", header=None)
    baris_header = None
    for i in range(len(raw)):
        if "Expenses" in raw.iloc[i].astype(str).values:
            baris_header = i
            break
    if baris_header is None:
        return None
    df = raw.iloc[baris_header + 1:, :].copy()
    df.columns = raw.iloc[baris_header].astype(str).values
    df = df.loc[:, ~df.columns.str.startswith("nan")]
    df = df[df["Expenses"].notna()]
    df = df[df["Expenses"].astype(str).str.upper() != "TOTAL"]
    for kolom in ["Budget SKK (USD)", "Budget Internal (USD)", "Realisasi (USD)"]:
        df[kolom] = pd.to_numeric(df[kolom], errors="coerce").fillna(0.0)
    return df[["Line", "Expenses", "Budget SKK (USD)", "Budget Internal (USD)", "Realisasi (USD)"]].reset_index(drop=True)

# ---------- Tampilan ----------
st.title("💰 HR PEB 2027 - RKA Budget Tracker")
st.caption("Upload file Excel monitoring Anda. Data hanya dibaca sementara dan tidak disimpan di server.")

file = st.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])
if not file:
    st.info("Silakan upload file Excel dulu.")
    st.stop()

try:
    data = baca_summary(file)
except Exception as e:
    st.error(f"Gagal membaca file. Pastikan ada sheet bernama 'Summary RKA'. Detail: {e}")
    st.stop()

if data is None or data.empty:
    st.error("Tabel di sheet 'Summary RKA' tidak ditemukan.")
    st.stop()

# Pilihan basis budget (sama seperti di template Excel Anda)
basis = st.radio("Basis budget", ["SKK", "Internal"], horizontal=True)
kolom_budget = "Budget SKK (USD)" if basis == "SKK" else "Budget Internal (USD)"

data["Budget"] = data[kolom_budget]
data["Realisasi"] = data["Realisasi (USD)"]

if data["Budget"].sum() == 0:
    st.warning(f"Budget {basis} di sheet Summary masih 0 semua, jadi persentase tidak bisa dihitung.")

# ---------- Simulasi pembayaran ----------
if "simulasi" not in st.session_state:
    st.session_state.simulasi = []

with st.sidebar:
    st.header("➕ Simulasi Pembayaran")
    st.caption("Coba kurangi budget sebelum Anda input ke Excel.")
    pos = st.selectbox("Pos expenses", data["Expenses"].tolist())
    nominal = st.number_input("Nominal (IDR)", min_value=0, step=1_000_000, format="%d")
    kurs = st.number_input("Kurs IDR/USD", min_value=1, value=16000, step=100, format="%d")
    ket = st.text_input("Keterangan (opsional)")
    if st.button("Kurangi budget", width="stretch"):
        if nominal > 0:
            st.session_state.simulasi.append(
                {"Expenses": pos, "Keterangan": ket, "IDR": nominal, "Kurs": kurs, "USD": nominal / kurs}
            )
    if st.session_state.simulasi and st.button("Hapus semua simulasi", width="stretch"):
        st.session_state.simulasi = []
        st.rerun()

sim = pd.DataFrame(st.session_state.simulasi)
if not sim.empty:
    tambahan = sim.groupby("Expenses")["USD"].sum()
    data["Simulasi"] = data["Expenses"].map(tambahan).fillna(0.0)
else:
    data["Simulasi"] = 0.0

data["Total Terpakai"] = data["Realisasi"] + data["Simulasi"]
data["Sisa"] = data["Budget"] - data["Total Terpakai"]
data["Persen"] = (data["Total Terpakai"] / data["Budget"]).where(data["Budget"] > 0, 0.0)

# ---------- Ringkasan ----------
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

if not sim.empty:
    st.info(f"Termasuk simulasi pembayaran sebesar {usd(data['Simulasi'].sum())}. Simulasi tidak mengubah file Excel Anda.")

st.divider()

# ---------- Kartu per pos ----------
st.subheader(f"Status per Pos Budget ({basis})")
kolom = st.columns(2)
for i, r in data.iterrows():
    with kolom[i % 2]:
        with st.container(border=True):
            st.markdown(f"**{r['Expenses']}**  \n<small>Line {r['Line']}</small>", unsafe_allow_html=True)
            st.progress(float(min(max(r["Persen"], 0.0), 1.0)))
            a, b = st.columns(2)
            a.write(f"Budget: **{usd(r['Budget'])}**")
            b.write(f"Terpakai: **{usd(r['Total Terpakai'])}**")
            if r["Budget"] == 0 and r["Total Terpakai"] > 0:
                st.error(f"Tidak ada budget {basis}, tapi ada pemakaian {usd(r['Total Terpakai'])}")
            elif r["Sisa"] < 0:
                st.error(f"OVER BUDGET: {usd(r['Sisa'])}")
            elif r["Persen"] >= 0.8:
                st.warning(f"Sisa {usd(r['Sisa'])} (tinggal {1 - r['Persen']:.0%})")
            else:
                st.success(f"Sisa {usd(r['Sisa'])}")

st.divider()

# ---------- Grafik & tabel ----------
st.subheader("Perbandingan Budget vs Terpakai")
st.bar_chart(data.set_index("Expenses")[["Budget", "Total Terpakai"]])

with st.expander("Lihat tabel lengkap"):
    tampil = data[["Line", "Expenses", "Budget", "Realisasi", "Simulasi", "Sisa", "Persen"]].copy()
    tampil["Persen"] = (tampil["Persen"] * 100).round(1)
    st.dataframe(tampil, width="stretch", hide_index=True)

if not sim.empty:
    st.subheader("Daftar simulasi pembayaran")
    st.dataframe(sim, width="stretch", hide_index=True)
    st.download_button("Unduh daftar simulasi (CSV)", sim.to_csv(index=False), "simulasi.csv", "text/csv")
