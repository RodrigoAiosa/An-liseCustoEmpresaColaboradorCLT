import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO

# Configuração da Página
st.set_page_config(page_title="Calculadora Expert de Custo de Funcionário", page_icon="📊", layout="wide")

# --- CSS COM EFEITOS DE HOVER E ESTILIZAÇÃO ---
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #4CAF50 !important;
        box-shadow: 0px 0px 25px rgba(76, 175, 80, 0.6);
        transform: translateY(-8px);
        background-color: rgba(76, 175, 80, 0.08);
    }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 800 !important; }
    [data-testid="stTable"] td:nth-child(2) { text-align: right !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def calcular_custos_detalhado(salario_bruto, regime, ferias_13, passagens_dia, valor_passagem, vr, va, saude, odonto, seguro_vida, aux_home, epi_ferramentas, outros):
    custos = {}
    
    if "CLT" in regime:
        p_13 = salario_bruto / 12 if ferias_13 else 0
        p_ferias = (salario_bruto / 12) * 1.33 if ferias_13 else 0
        fgts = salario_bruto * 0.08
        provisao_multa_fgts = fgts * 0.40 
        
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
        custos['Provisão Multa FGTS (40%)'] = provisao_multa_fgts
        custos['INSS Patronal'] = inss_patronal
        custos['RAT/Sistema S/Terceiros'] = rat_sis_s
        custos['Vale Transporte (Custo Empresa)'] = vt_empresa
        custos['Vale Refeição'] = vr
        custos['Vale Alimentação'] = va
        custos['Plano de Saúde'] = saude
        custos['Plano Odontológico'] = odonto
        custos['Seguro de Vida'] = seguro_vida
        custos['Auxílio Home Office'] = aux_home
        custos['Equipamentos/EPI/Uniforme'] = epi_ferramentas
        custos['Outros Custos'] = outros
        
    else: # Modelo PJ
        custos['Valor da Nota Fiscal'] = salario_bruto
        custos['Benefícios Opcionais (VR/VA)'] = vr + va
        custos['Seguros e Saúde'] = saude + odonto + seguro_vida
        custos['Infraestrutura/Outros'] = aux_home + epi_ferramentas + outros
    
    total_m = sum(custos.values())
    custos['Custo Total Mensal'] = total_m
    custos['Custo Total Anual'] = total_m * 12
    return custos

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Parâmetros Detalhados")
    
    with st.expander("📌 Dados Contratuais", expanded=True):
        salario_base_input = st.number_input("Salário Bruto (R$)", value=3000.0, step=100.0)
        regime = st.selectbox("Regime de Contratação", ["CLT (Simples Nacional)", "CLT (Lucro Presumido/Real)", "PJ"])
        incluir_provisoes = st.checkbox("Provisionar Férias e 13º", value=True)

    with st.expander("🚌 Transporte e Alimentação", expanded=False):
        v_passagem = st.number_input("Valor Unitário Passagem (R$)", value=5.50)
        n_passagens = st.number_input("Qtd Passagens/Dia", value=2)
        vr_mensal = st.number_input("Vale Refeição (Mensal)", value=550.0)
        va_mensal = st.number_input("Vale Alimentação (Mensal)", value=250.0)

    with st.expander("🏥 Saúde e Seguros", expanded=False):
        p_saude = st.number_input("Plano de Saúde (Custo Empresa)", value=0.0)
        p_odonto = st.number_input("Plano Odontológico", value=0.0)
        s_vida = st.number_input("Seguro de Vida", value=0.0)

    with st.expander("💻 Outros Custos e Infra", expanded=False):
        aux_home = st.number_input("Auxílio Home Office", value=0.0)
        epi_equip = st.number_input("EPI / Notebook / Uniforme (Mensalizado)", value=0.0)
        outros_c = st.number_input("Outras Taxas / Sindicato", value=0.0)

    st.write("---")
    # Link WhatsApp Personalizado
    msg_wa = urllib.parse.quote("Olá Rodrigo! Ajustei a formatação financeira da planilha de custos e gostaria de agendar uma reunião para validarmos.")
    link_wa = f"https://wa.me/11977019335?text={msg_wa}"
    st.markdown(f"📱 **Dúvidas?** [Fale Comigo no WhatsApp]({link_wa})")

# --- TABS ---
tab_ind, tab_lote = st.tabs(["👤 Cálculo Individual", "📁 Processar Planilha"])

with tab_ind:
    st.subheader(f"Análise de Custo: {regime}")
    res = calcular_custos_detalhado(salario_base_input, regime, incluir_provisoes, n_passagens, v_passagem, vr_mensal, va_mensal, p_saude, p_odonto, s_vida, aux_home, epi_equip, outros_c)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Custo Total Mensal", f"R$ {res['Custo Total Mensal']:,.2f}")
    with c2: st.metric("Custo Total Anual", f"R$ {res['Custo Total Anual']:,.2f}")
    with c3: 
        mult = res['Custo Total Mensal']/salario_base_input if salario_base_input > 0 else 0
        st.metric("Multiplicador Real", f"{mult:.2f}x")

    df_ind = pd.DataFrame(list(res.items()), columns=["Descrição", "Valor"])
    df_ind_filtrado = df_ind[(df_ind['Valor'] > 0) & (~df_ind['Descrição'].str.contains('Total'))]
    st.table(df_ind_filtrado.style.format({"Valor": "R$ {:.2f}"}))

with tab_lote:
    arquivo = st.file_uploader("Suba sua planilha de salários (XLSX ou CSV)", type=['xlsx', 'csv'])

    if arquivo:
        df_input = pd.read_excel(arquivo) if arquivo.name.endswith('xlsx') else pd.read_csv(arquivo)
        st.success("Planilha carregada!")
        
        col1, col2 = st.columns(2)
        with col1:
            coluna_salario = st.selectbox("Coluna de Salário Bruto:", df_input.columns)
        with col2:
            coluna_depto = st.selectbox("Coluna de Departamento/Setor:", df_input.columns)
        
        if st.button("🚀 Calcular e Gerar Relatórios"):
            with st.spinner("Processando..."):
                resultados = df_input[coluna_salario].apply(
                    lambda x: calcular_custos_detalhado(x, regime, incluir_provisoes, n_passagens, v_passagem, vr_mensal, va_mensal, p_saude, p_odonto, s_vida, aux_home, epi_equip, outros_c)
                )
                
                df_detalhado = pd.concat([df_input, pd.DataFrame(list(resultados))], axis=1)
                
                df_resumo_depto = df_detalhado.groupby(coluna_depto)['Custo Total Anual'].sum().reset_index()
                df_resumo_depto = df_resumo_depto.sort_values(by='Custo Total Anual', ascending=False)
                
                total_geral_anual = df_resumo_depto['Custo Total Anual'].sum()
                linha_total = pd.DataFrame({coluna_depto: ['TOTAL GERAL'], 'Custo Total Anual': [total_geral_anual]})
                df_resumo_com_total = pd.concat([df_resumo_depto, linha_total], ignore_index=True)
                
                st.markdown("### Resumo Final")
                st.dataframe(df_resumo_com_total.style.format({'Custo Total Anual': 'R$ {:,.2f}'}))

                output = BytesIO()
                # Uso do xlsxwriter para formatação avançada
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_detalhado.to_excel(writer, index=False, sheet_name='Custos_Detalhados')
                    df_resumo_com_total.to_excel(writer, index=False, sheet_name='Resumo_Por_Departamento')
                    
                    workbook  = writer.book
                    formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00'})
                    
                    # Formatação Aba Custos_Detalhados: Colunas D até U (Índices 3 a 20)
                    worksheet1 = writer.sheets['Custos_Detalhados']
                    worksheet1.set_column(3, 20, 18, formato_moeda)
                    
                    # Formatação Aba Resumo_Por_Departamento: Coluna B (Índice 1)
                    worksheet2 = writer.sheets['Resumo_Por_Departamento']
                    worksheet2.set_column(1, 1, 20, formato_moeda)
                
                st.download_button(
                    label="📥 Baixar Relatório Completo (.xlsx)",
                    data=output.getvalue(),
                    file_name="custos_rh_detalhado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )