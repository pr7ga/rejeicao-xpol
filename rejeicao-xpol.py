import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

st.title("Análise de Rejeição de Polarização Cruzada")

# ==========================
# Upload dos arquivos
# ==========================
st.subheader("Envio dos arquivos CSV")

copol_file = st.file_uploader("Selecione o arquivo de COPOL", type=["csv"])
xpol_file = st.file_uploader("Selecione o arquivo de XPOL", type=["csv"])

# ==========================
# Entradas do usuário
# ==========================
titulo = st.text_input("Título do gráfico", value="Rejeição de Polarização Cruzada")
fator_correcao = st.number_input("Fator de correção (dB) a aplicar em X-POL", value=0.0, step=0.1)

# ==========================
# Processamento
# ==========================
if copol_file and xpol_file:
    # Detecta separador automaticamente
    def read_csv_auto(file):
        data = file.getvalue().decode(errors="replace")
        sep = ";" if data.count(";") > data.count(",") else ","
        return pd.read_csv(io.StringIO(data), sep=sep)
    
    df_copol = read_csv_auto(copol_file)
    df_xpol = read_csv_auto(xpol_file)

    # Normaliza nomes das colunas
    df_copol.columns = [c.strip() for c in df_copol.columns]
    df_xpol.columns = [c.strip() for c in df_xpol.columns]

    # Seleciona colunas específicas
    ang_col = "Azimuth"
    val_col_copol = "Power-dBm"
    val_col_xpol = "Power-dBm"

    # Combina dados pelos ângulos
    df = pd.merge(
        df_copol[[ang_col, val_col_copol]],
        df_xpol[[ang_col, val_col_xpol]],
        on=ang_col,
        suffixes=("_copol", "_xpol")
    )

    # Aplica correção no Xpol
    df["Xpol_corrigido"] = df[f"{val_col_xpol}"] + fator_correcao

    # Calcula rejeição (copol - xpol corrigido)
    df["Rejeição (dB)"] = df[f"{val_col_copol}"] - df["Xpol_corrigido"]

    # ==========================
    # Gráfico Polar
    # ==========================
    st.subheader("Gráfico Polar")

    ang_rad = np.deg2rad(df[ang_col])
    pot = df["Rejeição (dB)"]

    fig = plt.figure(figsize=(7,7))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(ang_rad, pot, color='tab:blue', linewidth=2, label='Rejeição (Co-pol - X-pol corrigido)')
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title(titulo, va='bottom')
    ax.legend(loc='upper right')
    ax.grid(True)

    st.pyplot(fig)

    # ==========================
    # Opção para baixar os dados
    # ==========================
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Baixar dados calculados (CSV)",
        data=csv_buffer.getvalue(),
        file_name="rejeicao_polarizacao.csv",
        mime="text/csv"
    )
