# rejeicao_xpol_interpolacao.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

st.set_page_config(layout="centered")
st.title("Rejeição de Polarização Cruzada — (Power-dBm, com interpolação)")

# ======================
# Campos de entrada
# ======================
copol_file = st.file_uploader("Arquivo CO-POL (CSV)", type=["csv"])
xpol_file  = st.file_uploader("Arquivo X-POL (CSV)", type=["csv"])

st.markdown("---")

# Campos de texto
titulo = st.text_input("Título do gráfico", value="Rejeição de Polarização Cruzada")
subtitulo = st.text_input("Subtítulo (opcional)", value="")

# Configurações visuais
st.markdown("### Aparência do gráfico")
col1, col2, col3 = st.columns(3)
with col1:
    tamanho_titulo = st.number_input("Tamanho do título", value=16, min_value=8, max_value=32, step=1)
with col2:
    tamanho_subtitulo = st.number_input("Tamanho do subtítulo", value=12, min_value=6, max_value=28, step=1)
with col3:
    tamanho_rotulos = st.number_input("Tamanho dos rótulos/legenda", value=10, min_value=6, max_value=20, step=1)

fator_correcao = st.number_input("Fator de correção (dB) a aplicar em X-POL", value=0.0, step=0.1)

# ======================
# Funções auxiliares
# ======================
def read_csv_auto(uploaded_file):
    raw = uploaded_file.getvalue().decode(errors="replace")
    sep = ";" if raw.count(";") > raw.count(",") else ","
    df = pd.read_csv(io.StringIO(raw), sep=sep)
    df.columns = [c.strip() for c in df.columns]
    return df

def interp_to_grid(az, p, grid):
    mask = ~np.isnan(az) & ~np.isnan(p)
    az2, p2 = az[mask], p[mask]
    if len(az2) == 0:
        return np.full_like(grid, np.nan, dtype=float)
    order = np.argsort(az2)
    az2, p2 = az2[order], p2[order]
    return np.interp(grid, az2, p2, left=p2[0], right=p2[-1])

# ======================
# Processamento principal
# ======================
if copol_file and xpol_file:
    df_copol = read_csv_auto(copol_file)
    df_xpol  = read_csv_auto(xpol_file)

    if "Azimuth" not in df_copol.columns or "Azimuth" not in df_xpol.columns:
        st.error("Coluna 'Azimuth' não encontrada em um dos arquivos.")
    elif "Power-dBm" not in df_copol.columns or "Power-dBm" not in df_xpol.columns:
        st.error("Coluna 'Power-dBm' não encontrada em um dos arquivos.")
    else:
        # Conversões e ordenação
        df_copol["Azimuth"] = pd.to_numeric(df_copol["Azimuth"], errors="coerce")
        df_xpol["Azimuth"]  = pd.to_numeric(df_xpol["Azimuth"], errors="coerce")
        df_copol["Power-dBm"] = pd.to_numeric(df_copol["Power-dBm"], errors="coerce")
        df_xpol["Power-dBm"]  = pd.to_numeric(df_xpol["Power-dBm"], errors="coerce")

        df_copol = df_copol.sort_values("Azimuth").reset_index(drop=True)
        df_xpol  = df_xpol.sort_values("Azimuth").reset_index(drop=True)

        # Grade comum
        angles_union = np.union1d(df_copol["Azimuth"].dropna().unique(), df_xpol["Azimuth"].dropna().unique())
        angles_union = np.sort(angles_union)

        # Interpola
        p_c_grid = interp_to_grid(df_copol["Azimuth"].values, df_copol["Power-dBm"].values, angles_union)
        p_x_grid = interp_to_grid(df_xpol["Azimuth"].values, df_xpol["Power-dBm"].values, angles_union)

        # Correção e cálculo
        p_x_grid_corr = p_x_grid + fator_correcao
        rejeicao = p_c_grid - p_x_grid_corr

        df_res = pd.DataFrame({
            "Azimuth": angles_union,
            "Power-dBm_copol": p_c_grid,
            "Power-dBm_xpol":  p_x_grid_corr,
            "Rejeicao_dB": rejeicao
        })

        # ======================
        # Exibição de dados
        # ======================
        st.subheader("Resumo dos dados")
        st.write("Linhas resultantes:", len(df_res))
        st.write(df_res.head(10))

        # ======================
        # Gráfico polar
        # ======================
        st.subheader("Gráfico polar — Rejeição (Co-pol - X-pol corrigido)")
        ang_rad = np.deg2rad(df_res["Azimuth"].values)
        fig = plt.figure(figsize=(7,7))
        ax = fig.add_subplot(111, polar=True)
        ax.plot(ang_rad, df_res["Rejeicao_dB"].values, linewidth=2, label="Rejeição (dB)")

        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.grid(True)
        ax.legend(loc='upper right', fontsize=tamanho_rotulos)

        # Títulos configuráveis
        ax.set_title(titulo, va='bottom', fontsize=tamanho_titulo, fontweight='bold')
        if subtitulo.strip():
            plt.figtext(0.5, 0.05, subtitulo, ha='center', fontsize=tamanho_subtitulo)

        st.pyplot(fig)

        # ======================
        # Download CSV
        # ======================
        csv_buf = io.StringIO()
        df_res.to_csv(csv_buf, index=False)
        st.download_button(
            "📥 Baixar CSV com resultado",
            csv_buf.getvalue(),
            file_name="rejeicao_polarizacao_interpolada.csv",
            mime="text/csv"
        )
