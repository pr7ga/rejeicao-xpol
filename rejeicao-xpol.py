# rejeicao_xpol_layout.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

st.set_page_config(layout="centered")

# --------------------
# CONTROLES NA SIDEBAR
# --------------------
st.sidebar.header("Configurações / Upload")

# Título e subtítulo (inputs na sidebar para permitir renderização no topo do conteúdo principal)
titulo = st.sidebar.text_input("Título (aparecerá primeiro)", value="Rejeição de Polarização Cruzada")
subtitulo = st.sidebar.text_input("Subtítulo (aparecerá abaixo do título)", value="")

# Uploads
copol_file = st.sidebar.file_uploader("Arquivo CO-POL (CSV)", type=["csv"])
xpol_file  = st.sidebar.file_uploader("Arquivo X-POL (CSV)", type=["csv"])

# Aparência
st.sidebar.markdown("---")
tamanho_subtitulo = st.sidebar.number_input("Tamanho do subtítulo (px)", value=14, min_value=8, max_value=40, step=1)
tamanho_rotulos   = st.sidebar.number_input("Tamanho rótulos/legenda (px)", value=10, min_value=6, max_value=24, step=1)
fator_correcao     = st.sidebar.number_input("Fator de correção (dB) a aplicar em X-POL", value=0.0, step=0.1)
padding_chart_top_px = st.sidebar.number_input("Espaçamento acima do gráfico (px)", value=8, min_value=0, max_value=120, step=1)

st.sidebar.markdown("---")
st.sidebar.write("Observação: mantive a fonte padrão do título (não alterada).")

# --------------------
# ÁREA PRINCIPAL (ORDEM EXATA: título -> subtítulo -> gráfico)
# --------------------
# 1) Título (usando st.title — mantém a fonte padrão)
st.title(titulo)

# 2) Subtítulo, logo abaixo
if subtitulo.strip():
    # usamos markdown com estilo inline para controlar o tamanho, centralização e margem inferior
    st.markdown(
        f"<div style='text-align:center; font-size:{tamanho_subtitulo}px; margin-top:4px; margin-bottom: {padding_chart_top_px}px;'>{subtitulo}</div>",
        unsafe_allow_html=True
    )
else:
    # mesmo sem subtítulo, acrescentamos um pequeno espaço antes do gráfico
    st.markdown(f"<div style='height:{padding_chart_top_px}px'></div>", unsafe_allow_html=True)

# 3) Área de processamento e gráfico (aparecerá abaixo do subtítulo)
def read_csv_auto_filelike(uploaded_file):
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

# Se arquivos fornecidos, processa
if copol_file and xpol_file:
    try:
        df_copol = read_csv_auto_filelike(copol_file)
        df_xpol  = read_csv_auto_filelike(xpol_file)
    except Exception as e:
        st.error(f"Erro ao ler arquivos: {e}")
        st.stop()

    # Verificações de colunas
    if "Azimuth" not in df_copol.columns or "Azimuth" not in df_xpol.columns:
        st.error("Coluna 'Azimuth' não encontrada em um dos arquivos.")
        st.stop()
    if "Power-dBm" not in df_copol.columns or "Power-dBm" not in df_xpol.columns:
        st.error("Coluna 'Power-dBm' não encontrada em um dos arquivos.")
        st.stop()

    # Conversões
    df_copol["Azimuth"] = pd.to_numeric(df_copol["Azimuth"], errors="coerce")
    df_xpol["Azimuth"]  = pd.to_numeric(df_xpol["Azimuth"], errors="coerce")
    df_copol["Power-dBm"] = pd.to_numeric(df_copol["Power-dBm"], errors="coerce")
    df_xpol["Power-dBm"]  = pd.to_numeric(df_xpol["Power-dBm"], errors="coerce")

    df_copol = df_copol.sort_values("Azimuth").reset_index(drop=True)
    df_xpol  = df_xpol.sort_values("Azimuth").reset_index(drop=True)

    # Grade comum (união de azimutes)
    angles_union = np.union1d(df_copol["Azimuth"].dropna().unique(), df_xpol["Azimuth"].dropna().unique())
    angles_union = np.sort(angles_union)

    # Interpolar para grade comum
    p_c_grid = interp_to_grid(df_copol["Azimuth"].values, df_copol["Power-dBm"].values, angles_union)
    p_x_grid = interp_to_grid(df_xpol["Azimuth"].values,  df_xpol["Power-dBm"].values,  angles_union)

    # Aplica correção
    p_x_grid_corr = p_x_grid + fator_correcao

    # Calcula rejeição
    rejeicao = p_c_grid - p_x_grid_corr

    # DataFrame resultante
    df_res = pd.DataFrame({
        "Azimuth": angles_union,
        "Power-dBm_copol": p_c_grid,
        "Power-dBm_xpol": p_x_grid_corr,
        "Rejeicao_dB": rejeicao
    })

    # Exibe um resumo
    st.subheader("Resumo dos dados")
    st.write(f"Número de linhas (grade): {len(df_res)}")
    st.dataframe(df_res.head(10))

    # Plot polar — **sem título interno** (porque o título já foi mostrado via st.title)
    st.subheader("Gráfico polar — Rejeição (Co-pol - X-pol corrigido)")
    ang_rad = np.deg2rad(df_res["Azimuth"].values)

    fig = plt.figure(figsize=(7,7))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(ang_rad, df_res["Rejeicao_dB"].values, linewidth=2, label="Rejeição (dB)")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.grid(True)
    ax.legend(loc='upper right', fontsize=tamanho_rotulos)

    # Não definimos ax.set_title(...), assim não mudamos a fonte do título (o título é st.title acima).
    st.pyplot(fig)

    # Download CSV
    csv_buf = io.StringIO()
    df_res.to_csv(csv_buf, index=False)
    st.download_button("📥 Baixar CSV com resultado", csv_buf.getvalue(), file_name="rejeicao_polarizacao_interpolada.csv", mime="text/csv")

else:
    st.info("Envie os arquivos CO-POL e X-POL na barra lateral para processar os dados.")
