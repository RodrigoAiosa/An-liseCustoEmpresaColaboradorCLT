import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO

st.set_page_config(page_title="Calculadora Expert de Custo de Funcionário", page_icon="📊", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>
div[data-testid="stMetric"] {
    background-color: rgba(255, 255, 255, 0.05);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: 0.3s;
}
div[data-testid="stMetric"]:hover {
    border-color: #4CAF50 !important;
    box-shadow: 0px 0px 20px rgba(76, 175, 80, 0.6);
}
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------- FUNÇÃO ----------------
def calcular_custos_detalhado(
    salario_bruto, regime, ferias_13,
    passagens_dia, valor_passagem,
    vr, va, saude, odonto, seguro_vida,
    aux_home, epi_ferramentas, outros
):

    custos = {}

    if "CLT" in regime:

        p_13 = salario_bruto / 12 if ferias_13 else 0
        p_ferias = ((salario_bruto / 12) * 1.3333) if ferias_13 else 0
        fgts = salario_bruto * 0.08
        multa_fgts = fgts * 0.40

        inss_patronal = 0
        rat = 0

        if regime == "CLT (Lucro Presumido/Real)":
            inss_patronal = salario_bruto * 0.20
            rat = salario_bruto * 0.078

        custo_vt = (passagens_dia * valor_passagem) * 22
        desconto_6 = salario_bruto * 0.06
        vt_empresa = max(0, custo_vt - desconto_6)

        custos = {
            "Salário Base": salario_bruto,
            "13º (Provisão)": p_13,
            "Férias + 1/3 (Provisão)": p_ferias,
            "FGTS": fgts,
            "Provisão Multa FGTS": multa_fgts,
            "INSS Patronal": inss_patronal,
            "RAT/Sistema S": rat,
            "Vale Transporte": vt_empresa,
            "Vale Refeição": vr,
            "Vale Alimentação": va,
            "Plano Saúde": saude,
            "Plano Odonto": odonto,
            "Seguro Vida": seguro_vida,
            "Auxílio Home Office": aux_home,
            "EPI/Equipamentos": epi_ferramentas,
            "Outros Custos": outros,
        }

    else:  # PJ

        custos = {
            "Nota Fiscal": salario_bruto,
            "VR/VA": vr + va,
            "Saúde/Seguros": saude + odonto + seguro_vida,
            "Infraestrutura": aux_home + epi_ferramentas + outros,
        }

    total_mensal = sum(custos.values())
    custos["Custo Total Mensal"] = total_mensal
    custos["Custo Total Anual"] = total_mensal * 12

    return custos

# ---------------- SIDEBAR ----------------
with st.sidebar:

    st.header("⚙️ Parâmetros")

    salario = st.number_input("Salário Bruto (R$)", value=3000.0)
    regime = st.selectbox("Regime",
        ["CLT (Simples Nacional)", "CLT (Lucro Presumido/Real)", "PJ"])
    incluir = st.checkbox("Provisionar Férias e 13º", True)

    st.subheader("Transporte")
    v_passagem = st.number_input("Valor Passagem", value=5.5)
    n_pass = st.number_input("Passagens/Dia", value=2)

    st.subheader("Benefícios")
    vr = st.number_input("Vale Refeição", value=550.0)
    va = st.number_input("Vale Alimentação", value=250.0)

    st.subheader("Saúde/Seguros")
    saude = st.number_input("Plano Saúde", value=0.0)
    odonto = st.number_input("Plano Odonto", value=0.0)
    seguro = st.number_input("Seguro Vida", value=0.0)

    st.subheader("Infra")
    home = st.number_input("Auxílio Home Office", value=0.0)
    epi = st.number_input("EPI/Equipamentos", value=0.0)
    outros = st.number_input("Outros Custos", value=0.0)

# ---------------- TABS ----------------
tab1, tab2 = st.tabs(["👤 Cálculo Individual", "📁 Processar Planilha"])

# ---------------- ABA INDIVIDUAL ----------------
with tab1:

    res = calcular_custos_detalhado(
        salario, regime, incluir,
        n_pass, v_passagem,
        vr, va, saude, odonto, seguro,
        home, epi, outros
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Custo Mensal", f"R$ {res['Custo Total Mensal']:,.2f}")
    col2.metric("Custo Anual", f"R$ {res['Custo Total Anual']:,.2f}")
    mult = res["Custo Total Mensal"]/salario if salario > 0 else 0
    col3.metric("Multiplicador", f"{mult:.2f}x")

    df = pd.DataFrame(res.items(), columns=["Descrição", "Valor"])
    df = df[~df["Descrição"].str.contains("Total")]

    st.dataframe(df.style.format({"Valor": "R$ {:,.2f}"}), use_container_width=True)

# ---------------- ABA LOTE ----------------
with tab2:

    arquivo = st.file_uploader("Enviar planilha", type=["xlsx", "csv"])

    if arquivo:

        df_input = pd.read_excel(arquivo) if arquivo.name.endswith("xlsx") else pd.read_csv(arquivo)

        coluna_sal = st.selectbox("Coluna Salário", df_input.columns)
        coluna_dep = st.selectbox("Coluna Departamento", df_input.columns)

        if st.button("Calcular"):

            resultados = df_input[coluna_sal].apply(
                lambda x: calcular_custos_detalhado(
                    x, regime, incluir,
                    n_pass, v_passagem,
                    vr, va, saude, odonto, seguro,
                    home, epi, outros
                )
            )

            df_resultados = pd.DataFrame(resultados.tolist())

            df_final = pd.concat([df_input, df_resultados], axis=1)

            resumo = df_final.groupby(coluna_dep)["Custo Total Anual"].sum().reset_index()

            st.dataframe(resumo.style.format(
                {"Custo Total Anual": "R$ {:,.2f}"}
            ))

            output = BytesIO()

            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_final.to_excel(writer, index=False, sheet_name="Detalhado")
                resumo.to_excel(writer, index=False, sheet_name="Resumo")

            st.download_button(
                "Baixar Excel",
                data=output.getvalue(),
                file_name="relatorio_custos.xlsx"
            )
