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
# ESTILO VISUAL
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
# FUNÇÃO DE CÁLCULO COMPLETA
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

        # ---------------- PROVISÕES ----------------
        p_13 = salario_bruto / 12 if provisionar else 0
        p_ferias = salario_bruto / 12 if provisionar else 0
        terco_const = p_ferias / 3 if provisionar else 0

        # ---------------- BASES ----------------
        base_inss = salario_bruto + p_13 + p_ferias
        base_fgts = salario_bruto + p_13 + p_ferias + terco_const

        # ---------------- ENCARGOS ----------------
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

        # ---------------- VALE TRANSPORTE ----------------
        custo_vt_total = (passagens_dia * valor_passagem) * 22
        desconto_6 = salario_bruto * 0.06
        vt_empresa = max(0, custo_vt_total - desconto_6)

        # ---------------- LANÇAMENTOS ----------------
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

    st.header("⚙️ Parâmetros")

    salario_base_input = st.number_input("Salário Bruto (R$)", 3000.0)
    regime = st.selectbox(
        "Regime",
        ["CLT (Simples Nacional)",
         "CLT (Lucro Presumido/Real)",
         "PJ"]
    )
    provisionar = st.checkbox("Provisionar Férias e 13º", True)

    st.markdown("### Encargos Patronais (%)")
    perc_inss = st.number_input("INSS (%)", 20.0) / 100
    perc_rat = st.number_input("RAT (%)", 2.0) / 100
    perc_terceiros = st.number_input("Sistema S (%)", 5.8) / 100

    st.markdown("### Benefícios")
    v_passagem = st.number_input("Valor Passagem", 5.50)
    n_passagens = st.number_input("Passagens/Dia", 2)
    vr_mensal = st.number_input("Vale Refeição", 550.0)
    va_mensal = st.number_input("Vale Alimentação", 250.0)
    p_saude = st.number_input("Plano Saúde", 0.0)
    p_odonto = st.number_input("Plano Odonto", 0.0)
    s_vida = st.number_input("Seguro Vida", 0.0)
    aux_home = st.number_input("Auxílio Home Office", 0.0)
    epi_equip = st.number_input("EPI/Notebook", 0.0)
    outros_c = st.number_input("Outros Custos", 0.0)

    st.write("---")
    msg_wa = urllib.parse.quote("Olá Rodrigo! Podemos validar os cálculos da ferramenta?")
    st.markdown(f"[📱 WhatsApp](https://wa.me/11977019335?text={msg_wa})")

# ---------------------------------------------------
# TABS
# ---------------------------------------------------
tab_ind, tab_lote = st.tabs(["👤 Cálculo Individual", "📁 Processar Planilha"])

# ---------------------------------------------------
# ABA INDIVIDUAL
# ---------------------------------------------------
with tab_ind:

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
    c1.metric("Custo Mensal", f"R$ {res['Custo Total Mensal']:,.2f}")
    c2.metric("Custo Anual", f"R$ {res['Custo Total Anual']:,.2f}")
    mult = res['Custo Total Mensal']/salario_base_input if salario_base_input > 0 else 0
    c3.metric("Multiplicador", f"{mult:.2f}x")

    df = pd.DataFrame(list(res.items()), columns=["Descrição", "Valor"])
    df = df[(df["Valor"] > 0) & (~df["Descrição"].str.contains("Total"))]
    st.table(df.style.format({"Valor": "R$ {:,.2f}"}))

# ---------------------------------------------------
# ABA PROCESSAR PLANILHA
# ---------------------------------------------------
with tab_lote:

    arquivo = st.file_uploader("Suba planilha (XLSX ou CSV)", ['xlsx','csv'])

    if arquivo:

        df_input = pd.read_excel(arquivo) if arquivo.name.endswith("xlsx") else pd.read_csv(arquivo)
        st.success("Arquivo carregado!")

        col_salario = st.selectbox("Coluna Salário:", df_input.columns)
        col_depto = st.selectbox("Coluna Departamento:", df_input.columns)

        if st.button("🚀 Gerar Relatório"):

            resultados = df_input[col_salario].apply(
                lambda x: calcular_custos_detalhado(
                    x,
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
            )

            df_final = pd.concat([df_input, pd.DataFrame(list(resultados))], axis=1)

            resumo = df_final.groupby(col_depto)['Custo Total Anual'].sum().reset_index()
            total = resumo['Custo Total Anual'].sum()
            resumo.loc[len(resumo)] = ["TOTAL GERAL", total]

            st.dataframe(resumo.style.format({'Custo Total Anual': 'R$ {:,.2f}'}))

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name="Detalhado")
                resumo.to_excel(writer, index=False, sheet_name="Resumo")

                workbook = writer.book
                formato = workbook.add_format({'num_format': 'R$ #,##0.00'})

                writer.sheets["Detalhado"].set_column(3, 30, 18, formato)
                writer.sheets["Resumo"].set_column(1, 1, 22, formato)

            st.download_button(
                "📥 Baixar Excel",
                data=output.getvalue(),
                file_name="relatorio_custos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
