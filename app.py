import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO

st.set_page_config(
    page_title="Calculadora Expert de Custo de Funcionário",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------
# CSS DOS CARDS (mantido)
# ---------------------------------------------------
st.markdown("""
<style>
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.12);
    transition: all .35s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: #4CAF50 !important;
    box-shadow: 0px 0px 30px rgba(76, 175, 80, 0.55);
    transform: translateY(-10px) scale(1.02);
    background: rgba(76,175,80,0.08);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# FUNÇÃO DE CÁLCULO ORIGINAL CORRETA
# ---------------------------------------------------
def calcular_custos_detalhado(
    salario_bruto,
    regime,
    provisionar,
    passagens_dia,
    valor_passagem,
    vr,
    va,
    saude,
    odonto,
    seguro_vida,
    aux_home,
    epi_ferramentas,
    outros,
    perc_inss=0.20,
    perc_rat=0.02,
    perc_terceiros=0.058
):

    custos = {}

    if "CLT" in regime:

        p_13 = salario_bruto / 12 if provisionar else 0
        p_ferias = salario_bruto / 12 if provisionar else 0
        terco_const = p_ferias / 3 if provisionar else 0

        base_inss = salario_bruto + p_13 + p_ferias
        base_fgts = salario_bruto + p_13 + p_ferias + terco_const

        if regime == "CLT (Lucro Presumido/Real)":
            inss_patronal = base_inss * perc_inss
            rat = base_inss * perc_rat
            terceiros = base_inss * perc_terceiros
        else:
            inss_patronal = 0
            rat = 0
            terceiros = 0

        fgts = base_fgts * 0.08
        multa_fgts = fgts * 0.40

        custo_vt_total = (passagens_dia * valor_passagem) * 22
        desconto_6 = salario_bruto * 0.06
        vt_empresa = max(0, custo_vt_total - desconto_6)

        custos['Salário Base'] = salario_bruto
        custos['Provisão 13º'] = p_13
        custos['Provisão Férias'] = p_ferias
        custos['1/3 Constitucional'] = terco_const
        custos['INSS Patronal'] = inss_patronal
        custos['RAT'] = rat
        custos['Sistema S'] = terceiros
        custos['FGTS'] = fgts
        custos['Multa FGTS'] = multa_fgts
        custos['Vale Transporte'] = vt_empresa
        custos['VR'] = vr
        custos['VA'] = va
        custos['Saúde'] = saude
        custos['Odonto'] = odonto
        custos['Seguro'] = seguro_vida
        custos['Home Office'] = aux_home
        custos['Equipamentos'] = epi_ferramentas
        custos['Outros'] = outros

    else:
        custos['Nota PJ'] = salario_bruto
        custos['Benefícios'] = vr + va
        custos['Saúde'] = saude + odonto + seguro_vida
        custos['Infra'] = aux_home + epi_ferramentas + outros

    total_mensal = sum(custos.values())
    custos['Custo Total Mensal'] = total_mensal
    custos['Custo Total Anual'] = total_mensal * 12

    return custos

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
with st.sidebar:
    st.header("⚙️ Parâmetros Detalhados")

    with st.expander("📌 Dados Contratuais", expanded=True):
        salario_base_input = st.number_input("Salário Bruto (R$)", value=3000.0, step=100.0)
        regime = st.selectbox(
            "Regime de Contratação",
            ["CLT (Simples Nacional)", "CLT (Lucro Presumido/Real)", "PJ"]
        )
        incluir_provisoes = st.checkbox("Provisionar Férias e 13º", value=True)

    with st.expander("🚌 Transporte e Alimentação"):
        v_passagem = st.number_input("Valor Passagem", value=5.50)
        n_passagens = st.number_input("Qtd Passagens/Dia", value=2)
        vr_mensal = st.number_input("VR", value=550.0)
        va_mensal = st.number_input("VA", value=250.0)

    with st.expander("🏥 Saúde"):
        p_saude = st.number_input("Plano de Saúde", value=0.0)
        p_odonto = st.number_input("Odonto", value=0.0)
        s_vida = st.number_input("Seguro", value=0.0)

    with st.expander("💻 Infra"):
        aux_home = st.number_input("Home Office", value=0.0)
        epi_equip = st.number_input("Equipamentos", value=0.0)
        outros_c = st.number_input("Outros", value=0.0)

# ---------------------------------------------------
# TABS
# ---------------------------------------------------
tab_ind, tab_lote = st.tabs(["👤 Cálculo Individual", "📁 Processar Planilha"])

with tab_ind:

    res = calcular_custos_detalhado(
        salario_base_input,
        regime,
        incluir_provisoes,
        n_passagens,
        v_passagem,
        vr_mensal,
        va_mensal,
        p_saude,
        p_odonto,
        s_vida,
        aux_home,
        epi_equip,
        outros_c
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Custo Total Mensal", f"R$ {res['Custo Total Mensal']:,.2f}")

    with c2:
        st.metric("Custo Total Anual", f"R$ {res['Custo Total Anual']:,.2f}")

    with c3:
        mult = res['Custo Total Mensal']/salario_base_input if salario_base_input > 0 else 0
        st.metric("Multiplicador Real", f"{mult:.2f}x")

with tab_lote:
    st.info("Processamento em lote usa exatamente os mesmos parâmetros da sidebar.")
