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
    # Lê os arquivos CSV
    df_copol = pd.read_csv(copol_file)
    df_xpol = pd.read_csv(xpol_file)

    # Normaliza os nomes das colunas
    df_copol.columns = [c.strip().lower() for c in df_copol.columns]
    df_xpol.columns = [c.strip().lower() for c in df_xpol.columns]

    # Identifica as colunas de ângulo e potência
    ang_col = [c for c in df_copol.columns if "ang" in c or "azim" in c or "grau" in c][0]
    val_col_copol = [c for c in df_copol.columns if "ampl" in c or "gain" in c or "pot" in c][0]
    val_col_xpol = [c for c in df_xpol.columns if "ampl" in c or "gain" in c or "pot" in c][0]

    # Combina dados pelos ângulos
    df = pd.merge(df_copol[[ang_col, val_col_copol]], 
                  df_xpol[[ang_col, val_col_xpol]], 
                  on=ang_col, suffixes=("_copol", "_xpol"))

    # Aplica correção no Xpol
    df["xpol_corrigido"] = df[f"{val_col_xpol}"] + fator_correcao

    # Calcula rejeição (copol - xpol corrigido)
    df["rejeicao"] = df[f"{val_col_copol}"] - df["xpol_corrigido"]

    # ==========================
    # Gráfico Polar
    # ==========================
    st.subheader("Gráfico Polar")

    ang_rad = np.deg2rad(df[ang_col])
    pot = df["rejeicao"]

    fig = plt.figure(figsize=(7,7))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(ang_rad, pot, color='tab:blue', label='Rejeição (Co-pol - X-pol corrigido)')
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_title(titulo, va='bottom')
    ax.legend(loc='upper right')

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
