import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO

# Configuração da Página
st.set_page_config(
    page_title="Calculadora Expert de Custo de Funcionário",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------
# CSS COM EFEITOS DOS CARDS (MANTIDO)
# ---------------------------------------------------
st.markdown("""
<style>

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.12);
    transition: all .35s ease;
    backdrop-filter: blur(6px);
}

div[data-testid="stMetric"]:hover {
    border-color: #4CAF50 !important;
    box-shadow: 0px 0px 30px rgba(76, 175, 80, 0.55);
    transform: translateY(-10px) scale(1.02);
    background: rgba(76,175,80,0.08);
}

[data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
}

[data-testid="stMetricLabel"] {
    font-weight: 600;
    opacity: 0.8;
}

[data-testid="stTable"] td:nth-child(2) {
    text-align: right !important;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# FUNÇÃO DE CÁLCULO
# ---------------------------------------------------
def calcular_custos_detalhado(
    salario_bruto, regime, ferias_13,
    passagens_dia, valor_passagem,
    vr, va, saude, odonto, seguro_vida,
    aux_home, epi_ferramentas, outros
):
    custos = {}

    if "CLT" in regime:
        p_13 = salario_bruto / 12 if ferias_13 else 0
        p_ferias = (salario_bruto / 12) * 1.33 if ferias_13 else 0
        fgts = salario_bruto * 0.08
        multa_fgts = fgts * 0.40

        inss_patronal = 0
        rat_sis_s = 0

        if regime == "CLT (Lucro Presumido/Real)":
            inss_patronal = salario_bruto * 0.20
            rat_sis_s = salario_bruto * 0.078

        custo_vt_total = (passagens_dia * valor_passagem) * 22
        desc_6 = salario_bruto * 0.06
        vt_empresa = max(0, custo_vt_total - desc_6)

        custos['13º Salário (Provisão)'] = p_13
        custos['Férias + 1/3 (Provisão)'] = p_ferias
        custos['FGTS Mensal'] = fgts
        custos['Provisão Multa FGTS'] = multa_fgts
        custos['INSS Patronal'] = inss_patronal
        custos['RAT/Sistema S'] = rat_sis_s
        custos['Vale Transporte'] = vt_empresa
        custos['Vale Refeição'] = vr
        custos['Vale Alimentação'] = va
        custos['Plano de Saúde'] = saude
        custos['Plano Odontológico'] = odonto
        custos['Seguro de Vida'] = seguro_vida
        custos['Auxílio Home Office'] = aux_home
        custos['Equipamentos'] = epi_ferramentas
        custos['Outros Custos'] = outros

    else:
        custos['Valor Nota Fiscal'] = salario_bruto
        custos['Benefícios'] = vr + va
        custos['Saúde'] = saude + odonto + seguro_vida
        custos['Infra'] = aux_home + epi_ferramentas + outros

    total_m = sum(custos.values())
    custos['Custo Total Mensal'] = total_m
    custos['Custo Total Anual'] = total_m * 12

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
        vr_mensal = st.number_input("Vale Refeição", value=550.0)
        va_mensal = st.number_input("Vale Alimentação", value=250.0)

    with st.expander("🏥 Saúde e Seguros"):
        p_saude = st.number_input("Plano de Saúde", value=0.0)
        p_odonto = st.number_input("Plano Odontológico", value=0.0)
        s_vida = st.number_input("Seguro de Vida", value=0.0)

    with st.expander("💻 Outros Custos e Infra"):
        aux_home = st.number_input("Auxílio Home Office", value=0.0)
        epi_equip = st.number_input("Equipamentos", value=0.0)
        outros_c = st.number_input("Outros Custos", value=0.0)

# ---------------------------------------------------
# TABS
# ---------------------------------------------------
tab_ind, tab_lote = st.tabs(["👤 Cálculo Individual", "📁 Processar Planilha"])

# ---------------------------------------------------
# ABA INDIVIDUAL (CARDS COM EFEITO)
# ---------------------------------------------------
with tab_ind:
    st.subheader(f"Análise de Custo: {regime}")

    res = calcular_custos_detalhado(
        salario_base_input, regime, incluir_provisoes,
        n_passagens, v_passagem,
        vr_mensal, va_mensal,
        p_saude, p_odonto, s_vida,
        aux_home, epi_equip, outros_c
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("Custo Total Mensal", f"R$ {res['Custo Total Mensal']:,.2f}")

    with c2:
        st.metric("Custo Total Anual", f"R$ {res['Custo Total Anual']:,.2f}")

    with c3:
        mult = res['Custo Total Mensal']/salario_base_input if salario_base_input > 0 else 0
        st.metric("Multiplicador Real", f"{mult:.2f}x")

    df_ind = pd.DataFrame(list(res.items()), columns=["Descrição", "Valor"])
    df_ind_filtrado = df_ind[(df_ind['Valor'] > 0) & (~df_ind['Descrição'].str.contains('Total'))]
    st.table(df_ind_filtrado.style.format({"Valor": "R$ {:.2f}"}))

# ---------------------------------------------------
# ABA PROCESSAR PLANILHA
# ---------------------------------------------------
with tab_lote:
    arquivo = st.file_uploader("Suba sua planilha", type=['xlsx', 'csv'])

    if arquivo:
        df_input = pd.read_excel(arquivo) if arquivo.name.endswith('xlsx') else pd.read_csv(arquivo)
        st.success("Planilha carregada!")

        coluna_salario = st.selectbox("Coluna salário", df_input.columns)

        if st.button("Calcular"):
            resultados = df_input[coluna_salario].apply(
                lambda x: calcular_custos_detalhado(
                    x, regime, incluir_provisoes,
                    n_passagens, v_passagem,
                    vr_mensal, va_mensal,
                    p_saude, p_odonto, s_vida,
                    aux_home, epi_equip, outros_c
                )
            )

            df_saida = pd.concat([df_input, pd.DataFrame(list(resultados))], axis=1)
            st.dataframe(df_saida)
