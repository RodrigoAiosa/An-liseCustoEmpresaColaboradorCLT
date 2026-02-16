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

# ---------------- FUNÇÃO DE CÁLCULO ----------------
def calcular_custos(salario, regime, incluir, n_pass, v_pass, vr, va, saude, odonto, seguro, home, epi, outros):
    custos = {}

    if "CLT" in regime:

        decimo = salario / 12 if incluir else 0
        ferias = ((salario / 12) + ((salario / 3) / 12)) if incluir else 0
        fgts = salario * 0.08
        multa = fgts * 0.40

        vt_total = (n_pass * v_pass) * 22
        desc = salario * 0.06
        vt = max(0, vt_total - desc)

        inss = 0
        rat = 0
        if regime == "CLT (Lucro Presumido/Real)":
            inss = salario * 0.20
            rat = salario * 0.078

        custos = {
            "13º Salário (Provisão)": decimo,
            "Férias + 1/3 (Provisão)": ferias,
            "FGTS Mensal": fgts,
            "Provisão Multa FGTS (40%)": multa,
            "INSS Patronal": inss,
            "RAT/Sistema S/Terceiros": rat,
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

    else:
        custos = {
            "Valor Nota Fiscal": salario,
            "Benefícios": vr + va,
            "Saúde/Seguros": saude + odonto + seguro,
            "Infraestrutura": home + epi + outros,
        }

    total = sum(custos.values())
    custos["Custo Total Mensal"] = total
    custos["Custo Total Anual"] = total * 12

    return custos

# ---------------- SIDEBAR ----------------
with st.sidebar:

    st.header("⚙️ Parâmetros Detalhados")

    with st.expander("📌 Dados Contratuais", expanded=True):
        salario = st.number_input("Salário Bruto (R$)", 3000.0)
        regime = st.selectbox("Regime",
                              ["CLT (Simples Nacional)",
                               "CLT (Lucro Presumido/Real)",
                               "PJ"])
        incluir = st.checkbox("Provisionar Férias e 13º", True)

    with st.expander("🚌 Transporte e Alimentação"):
        v_pass = st.number_input("Valor Passagem", 5.5)
        n_pass = st.number_input("Passagens/Dia", 2)
        vr = st.number_input("Vale Refeição", 550.0)
        va = st.number_input("Vale Alimentação", 250.0)

    with st.expander("🏥 Saúde e Seguros"):
        saude = st.number_input("Plano Saúde", 0.0)
        odonto = st.number_input("Plano Odonto", 0.0)
        seguro = st.number_input("Seguro Vida", 0.0)

    with st.expander("💻 Outros Custos e Infra"):
        home = st.number_input("Auxílio Home Office", 0.0)
        epi = st.number_input("EPI/Equipamentos", 0.0)
        outros = st.number_input("Outros Custos", 0.0)

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
        home, epi, outros
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Custo Total Mensal", f"R$ {res['Custo Total Mensal']:,.2f}")
    c2.metric("Custo Total Anual", f"R$ {res['Custo Total Anual']:,.2f}")

    mult = res['Custo Total Mensal'] / salario if salario else 0
    c3.metric("Multiplicador Real", f"{mult:.2f}x")

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
                    home, epi, outros
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
