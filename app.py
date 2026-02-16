import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO

# ---------------- CONFIGURAÇÃO ----------------
st.set_page_config(
    page_title="Calculadora Expert de Custo de Funcionário",
    page_icon="📊",
    layout="wide"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
div[data-testid="stMetric"] {
    background-color: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid rgba(255,255,255,0.1);
    transition: all .3s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: #4CAF50 !important;
    box-shadow: 0px 0px 25px rgba(76,175,80,.6);
    transform: translateY(-6px);
}
[data-testid="stMetricValue"] {
    font-size: 2rem !important;
    font-weight: 800 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- CONSTANTES ----------------
TETO_INSS_2025 = 8157.41  # Atualizar conforme ano vigente

# ---------------- FUNÇÃO DE CÁLCULO ----------------
def calcular_custos(salario, regime, incluir, n_pass, v_pass, vr, va, saude, odonto, seguro, home, epi, outros, rat_perc=2.0, terceiros_perc=5.8):
    custos = {}

    if "CLT" in regime:
        # Provisões
        decimo = salario / 12 if incluir else 0
        ferias = (salario / 12) + (salario / 3 / 12) if incluir else 0
        
        # FGTS
        fgts = salario * 0.08
        multa = fgts * 0.40

        # Vale Transporte
        vt_total = (n_pass * v_pass) * 22
        desc_max = salario * 0.06
        desc_real = min(vt_total, desc_max)  # Desconta o menor valor
        vt = max(0, vt_total - desc_real)

        # INSS e Encargos (apenas para Lucro Presumido/Real)
        inss = 0
        rat = 0
        terceiros = 0
        
        if regime == "CLT (Lucro Presumido/Real)":
            # Base de cálculo limitada ao teto
            base_inss = min(salario, TETO_INSS_2025)
            
            inss = base_inss * 0.20  # INSS Patronal
            rat = base_inss * (rat_perc / 100)  # RAT conforme grau de risco
            terceiros = base_inss * (terceiros_perc / 100)  # Sistema S

        custos = {
            "Salário Base": salario,
            "13º Salário (Provisão Mensal)": decimo,
            "Férias + 1/3 (Provisão Mensal)": ferias,
            "FGTS Mensal (8%)": fgts,
            "Provisão Multa FGTS (40%)": multa,
            "INSS Patronal (20%)": inss,
            f"RAT ({rat_perc}%)": rat,
            f"Terceiros/Sistema S ({terceiros_perc}%)": terceiros,
            "Vale Transporte (Custo Empresa)": vt,
            "Vale Refeição": vr,
            "Vale Alimentação": va,
            "Plano de Saúde": saude,
            "Plano Odontológico": odonto,
            "Seguro de Vida": seguro,
            "Auxílio Home Office": home,
            "Equipamentos/EPI": epi,
            "Outros Custos": outros,
        }

    else:  # PJ
        custos = {
            "Valor Nota Fiscal (PJ)": salario,
            "Vale Refeição": vr,
            "Vale Alimentação": va,
            "Plano de Saúde": saude,
            "Plano Odontológico": odonto,
            "Seguro de Vida": seguro,
            "Auxílio Home Office": home,
            "Equipamentos": epi,
            "Outros Custos": outros,
        }

    total = sum(custos.values())
    
    # Removendo o salário base do total (não é custo adicional)
    if "CLT" in regime:
        total_sem_salario = total - salario
    else:
        total_sem_salario = total
    
    custos["Custo Total Mensal"] = total_sem_salario
    custos["Custo Total Anual"] = total_sem_salario * 12

    return custos

# ---------------- SIDEBAR ----------------
with st.sidebar:

    st.header("⚙️ Parâmetros Detalhados")

    with st.expander("📌 Dados Contratuais", expanded=True):
        salario = st.number_input("Salário Bruto (R$)", value=3000.0, min_value=0.0)
        regime = st.selectbox("Regime",
                              ["CLT (Simples Nacional)",
                               "CLT (Lucro Presumido/Real)",
                               "PJ"])
        incluir = st.checkbox("Provisionar Férias e 13º", True)

    # Parâmetros adicionais para Lucro Presumido/Real
    rat_perc = 2.0
    terceiros_perc = 5.8
    
    if regime == "CLT (Lucro Presumido/Real)":
        with st.expander("🏭 Encargos Específicos"):
            rat_perc = st.number_input("RAT - Risco Ambiental do Trabalho (%)", value=2.0, min_value=1.0, max_value=3.0, step=0.5)
            terceiros_perc = st.number_input("Terceiros/Sistema S (%)", value=5.8, min_value=0.0, max_value=10.0, step=0.1)
            st.info(f"Teto INSS 2025: R$ {TETO_INSS_2025:,.2f}")

    with st.expander("🚌 Transporte e Alimentação"):
        v_pass = st.number_input("Valor Passagem (R$)", value=5.50, min_value=0.0)
        n_pass = st.number_input("Passagens/Dia", value=2, min_value=0)
        vr = st.number_input("Vale Refeição (R$)", value=550.0, min_value=0.0)
        va = st.number_input("Vale Alimentação (R$)", value=250.0, min_value=0.0)

    with st.expander("🏥 Saúde e Seguros"):
        saude = st.number_input("Plano Saúde (R$)", value=0.0, min_value=0.0)
        odonto = st.number_input("Plano Odonto (R$)", value=0.0, min_value=0.0)
        seguro = st.number_input("Seguro Vida (R$)", value=0.0, min_value=0.0)

    with st.expander("💻 Outros Custos e Infra"):
        home = st.number_input("Auxílio Home Office (R$)", value=0.0, min_value=0.0)
        epi = st.number_input("EPI/Equipamentos (R$)", value=0.0, min_value=0.0)
        outros = st.number_input("Outros Custos (R$)", value=0.0, min_value=0.0)

    st.write("---")

    msg = urllib.parse.quote("Olá Rodrigo! Gostaria de validar a calculadora.")
    st.markdown(f"[WhatsApp](https://wa.me/11977019335?text={msg})")

# ---------------- TABS ----------------
tab1, tab2 = st.tabs(["👤 Cálculo Individual", "📁 Processar Planilha"])

# ---------------- CÁLCULO INDIVIDUAL ----------------
with tab1:

    st.subheader(f"Análise de Custo: {regime}")

    res = calcular_custos(
        salario, regime, incluir,
        n_pass, v_pass, vr, va,
        saude, odonto, seguro,
        home, epi, outros,
        rat_perc, terceiros_perc
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Custo Total Mensal", f"R$ {res['Custo Total Mensal']:,.2f}")
    c2.metric("Custo Total Anual", f"R$ {res['Custo Total Anual']:,.2f}")

    mult = res['Custo Total Mensal'] / salario if salario else 0
    c3.metric("Multiplicador Real", f"{mult:.2f}x")

    # Exibir detalhamento
    df = pd.DataFrame(res.items(), columns=["Descrição", "Valor"])
    df = df[(df["Valor"] > 0) & (~df["Descrição"].str.contains("Total"))]

    df["Valor"] = df["Valor"].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------- PROCESSAR PLANILHA ----------------
with tab2:

    arquivo = st.file_uploader("Suba sua planilha", type=["xlsx", "csv"])

    if arquivo:
        df_input = pd.read_excel(arquivo) if arquivo.name.endswith("xlsx") else pd.read_csv(arquivo)
        st.success("Planilha carregada")

        coluna_salario = st.selectbox("Coluna salário", df_input.columns)
        coluna_grupo = st.selectbox("Coluna para consolidar relatório", df_input.columns)

        if st.button("Calcular"):
            resultados = df_input[coluna_salario].apply(
                lambda x: calcular_custos(
                    x, regime, incluir,
                    n_pass, v_pass, vr, va,
                    saude, odonto, seguro,
                    home, epi, outros,
                    rat_perc, terceiros_perc
                )
            )

            df_final = pd.concat([df_input, pd.DataFrame(list(resultados))], axis=1)
            st.dataframe(df_final)

            # -------- RELATÓRIO CONSOLIDADO --------
            relatorio = (
                df_final
                .groupby(coluna_grupo)["Custo Total Anual"]
                .sum()
                .reset_index()
                .sort_values("Custo Total Anual", ascending=False)
            )

            st.subheader("Relatório Consolidado")
            st.dataframe(relatorio)

            # -------- EXPORTAÇÃO EXCEL COM 2 ABAS --------
            output = BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_final.to_excel(writer, sheet_name="detalhe_custo", index=False)
                relatorio.to_excel(writer, sheet_name="relatorio", index=False)

            st.download_button(
                "Baixar Excel",
                output.getvalue(),
                "custos_funcionarios.xlsx"
            )
