# app.py
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from gurobipy import Model, GRB, quicksum

st.set_page_config(page_title="Atölye Yerleşim Optimizasyonu", layout="wide")

st.title("Atölye Yerleşim Optimizasyonu (QAP)")

with st.sidebar:
    st.header("Genel Ayarlar")
    N = st.number_input("Birim sayısı (N)", min_value=2, max_value=50, value=10, step=1,
                        help="Akış matrisi NxN olacak.")
    preset = st.checkbox("Örnek verileri otomatik doldur", value=True)

# ---------- 1) BİRİMLER TABLOSU (Tip, Sabit, Koordinat) ----------
st.subheader("1) Birimler (Makine/Tezgah), Sabit işareti ve (varsa) Koordinat")
st.caption("Sabit birimler için (x,y) gir. Hareketli birimler için (x,y) boş bırak.")
if preset and N == 10:
    # Örnek: 5 makine sabit + 5 tezgah serbest (senin verdiğin veriler)
    names = [f"M{i}" for i in range(5)] + [f"T{i}" for i in range(5, 10)]
    tip = ["Makine"] * 5 + ["Tezgah"] * 5
    sabit = [True]*5 + [False]*5
    x = [0, 2, 5, 1, 3] + [None]*5
    y = [0, 3, 1, 6, 0] + [None]*5
else:
    names = [f"Birim{i}" for i in range(N)]
    tip = ["Makine"] * min(N, 1) + ["Tezgah"] * (N - min(N, 1))
    tip = tip[:N]  # güvenlik
    sabit = [False]*N
    x = [None]*N
    y = [None]*N

birimler_df = pd.DataFrame({
    "Birim": names,
    "Tip": tip,
    "Sabit": sabit,
    "x": x,
    "y": y
})

birimler_df = st.data_editor(
    birimler_df,
    num_rows="fixed",
    use_container_width=True,
    column_config={
        "Tip": st.column_config.SelectboxColumn(options=["Makine", "Tezgah"]),
        "Sabit": st.column_config.CheckboxColumn(),
        "x": st.column_config.NumberColumn(format="%.3f"),
        "y": st.column_config.NumberColumn(format="%.3f"),
    }
)

# ---------- 2) BOŞ NOKTALAR (Koordinatlar) ----------
st.subheader("2) Boş Noktalar (Koordinat Listesi)")
st.caption("Hareketli birimler bu noktalara yerleşecek. Toplam pozisyon sayısı = N olmalı (Sabit yerler + Boş noktalar).")

# Otomatik doldurma
sabit_say = int(birimler_df["Sabit"].sum())
bos_ihtiyac = max(N - sabit_say, 0)

if preset and N == 10:
    # Senin örnek bench noktalarından dolduralım
    sample_positions = [(6,2),(4,5),(7,0),(0,7),(6,6)]
    # ihtiyaca göre kes
    sample_positions = sample_positions[:bos_ihtiyac] + [(None, None)]*max(bos_ihtiyac - len(sample_positions), 0)
    bos_df = pd.DataFrame(sample_positions, columns=["x","y"])
else:
    bos_df = pd.DataFrame({"x":[None]*bos_ihtiyac, "y":[None]*bos_ihtiyac})

bos_df = st.data_editor(
    bos_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "x": st.column_config.NumberColumn(format="%.3f"),
        "y": st.column_config.NumberColumn(format="%.3f"),
    }
)

# ---------- 3) AKIŞ MATRİSİ ----------
st.subheader("3) Akış Matrisi (NxN)")
st.caption("Spagetti diyagramındaki gidip-gelmeler. Diagonal genelde 0 olur.")
if preset and N == 10:
    F_default = np.array([
        [0, 3, 5, 2, 4, 6, 1, 3, 2, 4],
        [3, 0, 4, 1, 5, 2, 3, 5, 6, 1],
        [5, 4, 0, 3, 2, 1, 4, 3, 2, 6],
        [2, 1, 3, 0, 6, 4, 5, 2, 1, 3],
        [4, 5, 2, 6, 0, 3, 1, 4, 2, 5],
        [6, 2, 1, 4, 3, 0, 2, 5, 3, 1],
        [1, 3, 4, 5, 1, 2, 0, 3, 4, 6],
        [3, 5, 3, 2, 4, 5, 3, 0, 1, 2],
        [2, 6, 2, 1, 2, 3, 4, 1, 0, 5],
        [4, 1, 6, 3, 5, 1, 6, 2, 5, 0]
    ])
else:
    F_default = np.zeros((N, N), dtype=int)

F_df = pd.DataFrame(F_default, index=[f"{birimler_df.loc[i,'Birim']}" for i in range(N)],
                    columns=[f"{birimler_df.loc[i,'Birim']}" for i in range(N)])

F_df = st.data_editor(F_df, use_container_width=True, num_rows="fixed")

# ---------- Yardımcı: Mesafe ----------
def euclid(a, b):
    return np.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

# ---------- Doğrulamalar ----------
def dogrula(birimler_df, bos_df, N):
    # Sabit olanlar koordinat zorunlu
    sabitler = birimler_df[birimler_df["Sabit"] == True]
    if sabitler[["x","y"]].isna().any().any():
        return False, "Sabit birimlerin tümünde (x,y) olmalı."

    # Toplam pozisyon sayısı = N
    sabit_say = int(birimler_df["Sabit"].sum())
    if len(bos_df) + sabit_say != N:
        return False, f"Toplam pozisyon sayısı N olmalı. Şu an: sabit={sabit_say}, boş={len(bos_df)}, toplam={sabit_say+len(bos_df)}."

    # (0,0) şartı
    pos_list = []
    for _, r in sabitler.iterrows():
        pos_list.append((float(r["x"]), float(r["y"])))
    for _, r in bos_df.iterrows():
        if pd.isna(r["x"]) or pd.isna(r["y"]):
            return False, "Boş noktaların tümünde (x,y) olmalı."
        pos_list.append((float(r["x"]), float(r["y"])))
    if (0.0, 0.0) not in pos_list:
        return False, "En az bir pozisyon (0,0) olmalı."

    # Pozisyon koordinatları benzersiz olsun
    if len(pos_list) != len(set(pos_list)):
        return False, "Pozisyon koordinatları birbirinden farklı olmalı (tekrarlı koordinat var)."

    return True, ""

# ---------- ÇALIŞTIR ----------
col_run1, col_run2 = st.columns([1,1])
with col_run1:
    run = st.button("Optimizasyonu Çalıştır", type="primary")
with col_run2:
    st.caption("İpucu: N büyüdükçe QAP zorlaşır. 20+ için süre artabilir.")

if run:
    ok, msg = dogrula(birimler_df, bos_df, N)
    if not ok:
        st.error(msg)
    else:
        try:
            # Pozisyon listesi: önce sabit birimlerin koordinatları, sonra boş noktalar
            sabit_idx = list(birimler_df[birimler_df["Sabit"] == True].index)
            hareketli_idx = list(birimler_df[birimler_df["Sabit"] == False].index)

            pos_coords = []
            pos_owner_fixed_unit = {}  # {pos_j: unit_i} sabit sahiplik
            # Sabit pozisyonları ekle
            for i in sabit_idx:
                xi = float(birimler_df.loc[i,"x"])
                yi = float(birimler_df.loc[i,"y"])
                pos_coords.append((xi, yi))
                pos_owner_fixed_unit[len(pos_coords)-1] = i

            # Boş pozisyonları ekle
            for _, r in bos_df.iterrows():
                pos_coords.append((float(r["x"]), float(r["y"])))

            # Mesafe matrisi
            nPos = len(pos_coords)
            D = np.zeros((nPos, nPos))
            for j in range(nPos):
                for l in range(nPos):
                    D[j,l] = euclid(pos_coords[j], pos_coords[l])

            # Akış matrisi
            F = F_df.values.astype(float)

            # Gurobi modeli
            m = Model("QAP_Flexible")
            m.Params.OutputFlag = 0  # sessiz

            # Karar değişkeni: x[i,j] = birim i pozisyon j
            x = m.addVars(N, nPos, vtype=GRB.BINARY, name="x")

            # Her birim tam 1 pozisyona
            m.addConstrs(quicksum(x[i,j] for j in range(nPos)) == 1 for i in range(N))
            # Her pozisyona tam 1 birim
            m.addConstrs(quicksum(x[i,j] for i in range(N)) == 1 for j in range(nPos))

            # Sabit birimler: kendi koordinatına kilitle
            # pos_owner_fixed_unit: j -> i
            for j, i_fixed in pos_owner_fixed_unit.items():
                for jj in range(nPos):
                    if jj == j:
                        m.addConstr(x[i_fixed, jj] == 1)
                    else:
                        m.addConstr(x[i_fixed, jj] == 0)

            # Amaç: min sum_{i,k,j,l} F[i,k] * D[j,l] * x[i,j] * x[k,l]
            m.setObjective(
                quicksum(F[i,k] * D[j,l] * x[i,j] * x[k,l]
                         for i in range(N) for k in range(N)
                         for j in range(nPos) for l in range(nPos)),
                GRB.MINIMIZE
            )

            m.optimize()
            st.success(f"Optimizasyon tamamlandı. Amaç değeri (toplam taşıma maliyeti): {m.objVal:.4f}")

            # Atamaları toparla
            assignments = []
            for i in range(N):
                for j in range(nPos):
                    if x[i,j].X > 0.5:
                        assignments.append({
                            "Birim": birimler_df.loc[i,"Birim"],
                            "Tip": birimler_df.loc[i,"Tip"],
                            "Sabit": bool(birimler_df.loc[i,"Sabit"]),
                            "Pozisyon": j,
                            "X": pos_coords[j][0],
                            "Y": pos_coords[j][1]
                        })

            asg_df = pd.DataFrame(assignments)
            st.subheader("4) Metin Çıktısı: Atamalar")
            st.dataframe(asg_df, use_container_width=True)

            # ---------- 5) Görsel Çıktı ----------
            st.subheader("5) Yerleşim Planı (Görsel)")
            fig = plt.figure(figsize=(8, 7))
            ax = plt.gca()
            # Tüm pozisyonları arka plana noktalar olarak çiz
            for j, (cx, cy) in enumerate(pos_coords):
                ax.scatter(cx, cy, s=80, edgecolors="black")
                ax.text(cx, cy+0.15, f"P{j}", ha="center", va="bottom", fontsize=8)

            # Atanan birimleri etiketle
            for row in assignments:
                cx, cy = row["X"], row["Y"]
                label = f"{row['Birim']}"  # ör: M0, T3
                ax.scatter(cx, cy, s=300, edgecolors="black")
                ax.text(cx, cy, label, fontsize=10, ha="center", va="center", color="white", weight="bold")

            ax.set_title("Makine (sabit) ve Tezgah (hareketli) Yerleşim Planı")
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.grid(True)
            ax.set_aspect("equal", adjustable="box")
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Hata: {e}")
