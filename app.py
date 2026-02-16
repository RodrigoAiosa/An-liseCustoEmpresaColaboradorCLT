import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO

# ---------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------
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
    background-color: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 15px;
    border: 1px solid rgba(255,255,255,0.1);
    transition: all 0.4s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: #4CAF50 !important;
    box-shadow: 0px 0px 25px rgba(76,175,80,0.6);
    transform: translateY(-8px);
}
[data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# FUNÇÃO DE CÁLCULO — MODELO ORIGINAL CORRETO
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
    perc_inss,
    perc_rat,
    perc_terceiros
):

    custos = {}

    if "CLT" in regime:

        # PROVISÕES
        p_13 = salario_bruto / 12 if provisionar else 0
        p_ferias = salario_bruto / 12 if provisionar else 0
        terco_const = p_ferias / 3 if provisionar else 0

        # BASES
        base_inss = salario_bruto + p_13 + p_ferias
        base_fgts = salario_bruto + p_13 + p_ferias + terco_const

        # ENCARGOS (Somente fora Simples)
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

        # VALE TRANSPORTE
        custo_vt_total = (passagens_dia * valor_passagem) * 22
        desconto_6 = salario_bruto * 0.06
        vt_empresa = max(0, custo_vt_total - desconto_6)

        # LANÇAMENTOS DETALHADOS
        custos['Salário Base'] = salario_bruto
        custos['Provisão 13º'] = p_13
        custos['Provisão Férias'] = p_ferias
        custos['1/3 Constitucional Férias'] = terco_const
        custos['INSS Patronal'] = inss_patronal
        custos['RAT'] = rat
        custos['Sistema S / Terceiros'] = terceiros
        custos['FGTS (8%)'] = fgts
        custos['Provisão Multa FGTS (40%)'] = multa_fgts
        custos['Vale Transporte (Empresa)'] = vt_empresa
        custos['Vale Refeição'] = vr
        custos['Vale Alimentação'] = va
        custos['Plano de Saúde'] = saude
        custos['Plano Odontológico'] = odonto
        custos['Seguro de Vida'] = seguro_vida
        custos['Auxílio Home Office'] = aux_home
        custos['EPI / Equipamentos'] = epi_ferramentas
        custos['Outros Custos'] = outros

    else:
        # MODELO PJ
        custos['Valor Nota Fiscal'] = salario_bruto
        custos['Benefícios (VR + VA)'] = vr + va
        custos['Saúde / Seguros'] = saude + odonto + seguro_vida
        custos['Infraestrutura / Outros'] = aux_home + epi_ferramentas + outros

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
        provisionar = st.checkbox("Provisionar Férias e 13º", value=True)

        st.markdown("### Encargos Patronais (%)")
        perc_inss = st.number_input("INSS Patronal (%)", value=20.0) / 100
        perc_rat = st.number_input("RAT (%)", value=2.0) / 100
        perc_terceiros = st.number_input("Sistema S / Terceiros (%)", value=5.8) / 100

    with st.expander("🚌 Transporte e Alimentação"):
        v_passagem = st.number_input("Valor Unitário Passagem (R$)", value=5.50)
        n_passagens = st.number_input("Qtd Passagens/Dia", value=2)
        vr_mensal = st.number_input("Vale Refeição (Mensal)", value=550.0)
        va_mensal = st.number_input("Vale Alimentação (Mensal)", value=250.0)

    with st.expander("🏥 Saúde"):
        p_saude = st.number_input("Plano de Saúde", value=0.0)
        p_odonto = st.number_input("Plano Odontológico", value=0.0)
        s_vida = st.number_input("Seguro de Vida", value=0.0)

    with st.expander("💻 Infra"):
        aux_home = st.number_input("Auxílio Home Office", value=0.0)
        epi_equip = st.number_input("EPI / Equipamentos", value=0.0)
        outros_c = st.number_input("Outros Custos", value=0.0)

# ---------------------------------------------------
# ABA INDIVIDUAL
# ---------------------------------------------------
st.subheader(f"Análise de Custo: {regime}")

res = calcular_custos_detalhado(
    salario_base_input,
    regime,
    provisionar,
    n_passagens,
    v_passagem,
    vr_mensal,
    va_mensal,
    p_saude,
    p_odonto,
    s_vida,
    aux_home,
    epi_equip,
    outros_c,
    perc_inss,
    perc_rat,
    perc_terceiros
)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Custo Total Mensal", f"R$ {res['Custo Total Mensal']:,.2f}")

with c2:
    st.metric("Custo Total Anual", f"R$ {res['Custo Total Anual']:,.2f}")

with c3:
    mult = res['Custo Total Mensal']/salario_base_input if salario_base_input > 0 else 0
    st.metric("Multiplicador Real", f"{mult:.2f}x")
