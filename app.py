import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO

# ---------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------
st.set_page_config(
    page_title="Calculadora Expert de Custo de Funcionário",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------
# ESTILIZAÇÃO
# ---------------------------------------------------
st.markdown("""
<style>
div[data-testid="stMetric"] {
    background-color: rgba(255, 255, 255, 0.05);
    padding: 20px;
    border-radius: 15px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# FUNÇÃO DE CÁLCULO
# ---------------------------------------------------
def calcular_custos_detalhado(
    salario_bruto,
    regime,
    incluir_provisoes,
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

        p_13 = salario_bruto / 12 if incluir_provisoes else 0
        p_ferias = salario_bruto / 12 if incluir_provisoes else 0
        terco_const = p_ferias / 3 if incluir_provisoes else 0

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
        custos['FGTS'] = fgts
        custos['INSS Patronal'] = inss_patronal
        custos['Benefícios'] = vr + va + vt_empresa
        custos['Saúde'] = saude + odonto + seguro_vida
        custos['Infra'] = aux_home + epi_ferramentas + outros
        custos['Provisões'] = p_13 + p_ferias + terco_const + multa_fgts

    else:
        custos['Nota PJ'] = salario_bruto
        custos['Benefícios'] = vr + va
        custos['Saúde'] = saude + odonto + seguro_vida
        custos['Infra'] = aux_home + epi_ferramentas + outros

    total = sum(custos.values())
    custos['Total Mensal'] = total
    custos['Total Anual'] = total * 12

    return custos

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
with st.sidebar:
    st.header("⚙️ Parâmetros Detalhados")

    with st.expander("📌 Dados Contratuais", expanded=True):
        salario_base_input = st.number_input("Salário Bruto (R$)", value=3000.0)
        regime = st.selectbox(
            "Regime de Contratação",
            ["CLT (Simples Nacional)", "CLT (Lucro Presumido/Real)", "PJ"]
        )
        incluir_provisoes = st.checkbox("Provisionar Férias e 13º", value=True)

        perc_inss = st.number_input("INSS (%)", value=20.0) / 100
        perc_rat = st.number_input("RAT (%)", value=2.0) / 100
        perc_terceiros = st.number_input("Terceiros (%)", value=5.8) / 100

    with st.expander("🚌 Transporte e Alimentação"):
        v_passagem = st.number_input("Passagem", value=5.50)
        n_passagens = st.number_input("Qtd/dia", value=2)
        vr_mensal = st.number_input("VR", value=550.0)
        va_mensal = st.number_input("VA", value=250.0)

    with st.expander("🏥 Saúde"):
        p_saude = st.number_input("Saúde", value=0.0)
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

# ---------------------------------------------------
# INDIVIDUAL
# ---------------------------------------------------
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
        outros_c,
        perc_inss,
        perc_rat,
        perc_terceiros
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("Custo Mensal", f"R$ {res['Total Mensal']:,.2f}")
    c2.metric("Custo Anual", f"R$ {res['Total Anual']:,.2f}")
    c3.metric("Multiplicador", f"{res['Total Mensal']/salario_base_input:.2f}x")

# ---------------------------------------------------
# PROCESSAR PLANILHA
# ---------------------------------------------------
with tab_lote:

    st.subheader("Processamento em lote")

    arquivo = st.file_uploader("Envie a planilha", type=["xlsx", "csv"])

    if arquivo:

        if arquivo.name.endswith(".csv"):
            df = pd.read_csv(arquivo)
        else:
            df = pd.read_excel(arquivo)

        st.write("Prévia da planilha")
        st.dataframe(df.head())

        if "salario" not in df.columns:
            st.error("A planilha precisa ter uma coluna chamada 'salario'")
        else:

            resultados = []

            for _, row in df.iterrows():
                calc = calcular_custos_detalhado(
                    row["salario"],
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
                    outros_c,
                    perc_inss,
                    perc_rat,
                    perc_terceiros
                )

                resultados.append({
                    "salario": row["salario"],
                    "custo_mensal": calc["Total Mensal"],
                    "custo_anual": calc["Total Anual"]
                })

            df_saida = pd.DataFrame(resultados)

            st.success("Processamento concluído")
            st.dataframe(df_saida)

            buffer = BytesIO()
            df_saida.to_excel(buffer, index=False)

            st.download_button(
                "📥 Baixar resultado",
                buffer.getvalue(),
                "custos_funcionarios.xlsx"
            )
