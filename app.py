import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go

# ---------------- CONFIGURAÇÃO ----------------
st.set_page_config(
    page_title="Calculadora Expert de Custo de Funcionário",
    page_icon="📊",
    layout="wide"
)

# ---------------- CONSTANTES ----------------
TETO_INSS_2025 = 8157.41
SALARIO_MINIMO_2025 = 1518.00

# Presets de benefícios por área
PRESETS_BENEFICIOS = {
    "Personalizado": {},
    "Tech/TI": {
        "vr": 800,
        "va": 400,
        "saude": 450,
        "odonto": 80,
        "home": 200
    },
    "Comercial": {
        "vr": 600,
        "va": 300,
        "saude": 350,
        "odonto": 60,
        "home": 0
    },
    "Operacional": {
        "vr": 550,
        "va": 250,
        "saude": 300,
        "odonto": 50,
        "home": 0
    },
    "Administrativo": {
        "vr": 650,
        "va": 350,
        "saude": 400,
        "odonto": 70,
        "home": 100
    }
}

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
.css-1d391kg {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- FUNÇÕES AUXILIARES ----------------

def calcular_inss_funcionario(salario):
    """Calcula INSS progressivo do funcionário"""
    faixas = [
        (1412.00, 0.075),
        (2666.68, 0.09),
        (4000.03, 0.12),
        (TETO_INSS_2025, 0.14)
    ]
    
    inss = 0
    salario_restante = salario
    
    for i, (limite, aliquota) in enumerate(faixas):
        base_anterior = faixas[i-1][0] if i > 0 else 0
        base_calculo = min(salario_restante, limite - base_anterior)
        
        if base_calculo > 0:
            inss += base_calculo * aliquota
            salario_restante -= base_calculo
    
    return min(inss, TETO_INSS_2025 * 0.14)

def calcular_irrf(salario, dependentes=0):
    """Calcula IRRF"""
    inss = calcular_inss_funcionario(salario)
    base = salario - inss - (dependentes * 189.59)
    
    if base <= 2259.20:
        return 0
    elif base <= 2826.65:
        return base * 0.075 - 169.44
    elif base <= 3751.05:
        return base * 0.15 - 381.44
    elif base <= 4664.68:
        return base * 0.225 - 662.77
    else:
        return base * 0.275 - 896.00

# ---------------- FUNÇÃO DE CÁLCULO ----------------
def calcular_custos(salario, regime, incluir, n_pass, v_pass, vr, va, saude, odonto, seguro, home, epi, outros, rat_perc=2.0, terceiros_perc=5.8, dependentes=0):
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
        desc_real = min(vt_total, desc_max)
        vt = max(0, vt_total - desc_real)

        # INSS e Encargos
        inss = 0
        rat = 0
        terceiros = 0
        
        if regime == "CLT (Lucro Presumido/Real)":
            base_inss = min(salario, TETO_INSS_2025)
            inss = base_inss * 0.20
            rat = base_inss * (rat_perc / 100)
            terceiros = base_inss * (terceiros_perc / 100)

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
        
        # Calcular salário líquido
        inss_func = calcular_inss_funcionario(salario)
        irrf_func = calcular_irrf(salario, dependentes)
        salario_liquido = salario - inss_func - irrf_func - desc_real
        
        custos["_salario_liquido"] = salario_liquido
        custos["_inss_funcionario"] = inss_func
        custos["_irrf_funcionario"] = irrf_func

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
            "_salario_liquido": salario * 0.85,  # Estimativa
        }

    total = sum([v for k, v in custos.items() if not k.startswith("_")])
    
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
    
    # Tema
    tema = st.radio("🎨 Tema", ["Claro", "Escuro"], horizontal=True)
    
    if tema == "Escuro":
        st.markdown("""
        <style>
            .stApp {
                background-color: #0e1117;
            }
            div[data-testid="stMetric"] {
                background-color: rgba(255,255,255,0.1);
            }
        </style>
        """, unsafe_allow_html=True)

    with st.expander("📌 Dados Contratuais", expanded=True):
        salario = st.number_input("Salário Bruto (R$)", value=3000.0, min_value=0.0, step=100.0)
        regime = st.selectbox("Regime",
                              ["CLT (Simples Nacional)",
                               "CLT (Lucro Presumido/Real)",
                               "PJ"])
        incluir = st.checkbox("Provisionar Férias e 13º", True)
        dependentes = st.number_input("Número de Dependentes (IR)", value=0, min_value=0, max_value=10)

    # Preset de benefícios
    with st.expander("🎁 Preset de Benefícios"):
        preset_selecionado = st.selectbox("Área/Função", list(PRESETS_BENEFICIOS.keys()))
        
        if preset_selecionado != "Personalizado":
            st.info(f"✅ Valores do preset '{preset_selecionado}' aplicados")

    rat_perc = 2.0
    terceiros_perc = 5.8
    
    if regime == "CLT (Lucro Presumido/Real)":
        with st.expander("🏭 Encargos Específicos"):
            rat_perc = st.number_input("RAT - Risco Ambiental (%)", value=2.0, min_value=1.0, max_value=3.0, step=0.5)
            terceiros_perc = st.number_input("Terceiros/Sistema S (%)", value=5.8, min_value=0.0, max_value=10.0, step=0.1)
            st.info(f"💡 Teto INSS 2025: R$ {TETO_INSS_2025:,.2f}")

    with st.expander("🚌 Transporte e Alimentação"):
        if preset_selecionado != "Personalizado":
            preset = PRESETS_BENEFICIOS[preset_selecionado]
            vr = st.number_input("Vale Refeição (R$)", value=float(preset.get("vr", 550)), min_value=0.0)
            va = st.number_input("Vale Alimentação (R$)", value=float(preset.get("va", 250)), min_value=0.0)
        else:
            vr = st.number_input("Vale Refeição (R$)", value=550.0, min_value=0.0)
            va = st.number_input("Vale Alimentação (R$)", value=250.0, min_value=0.0)
        
        v_pass = st.number_input("Valor Passagem (R$)", value=5.50, min_value=0.0)
        n_pass = st.number_input("Passagens/Dia", value=2, min_value=0)

    with st.expander("🏥 Saúde e Seguros"):
        if preset_selecionado != "Personalizado":
            preset = PRESETS_BENEFICIOS[preset_selecionado]
            saude = st.number_input("Plano Saúde (R$)", value=float(preset.get("saude", 0)), min_value=0.0)
            odonto = st.number_input("Plano Odonto (R$)", value=float(preset.get("odonto", 0)), min_value=0.0)
        else:
            saude = st.number_input("Plano Saúde (R$)", value=0.0, min_value=0.0)
            odonto = st.number_input("Plano Odonto (R$)", value=0.0, min_value=0.0)
        
        seguro = st.number_input("Seguro Vida (R$)", value=0.0, min_value=0.0)

    with st.expander("💻 Outros Custos e Infra"):
        if preset_selecionado != "Personalizado":
            preset = PRESETS_BENEFICIOS[preset_selecionado]
            home = st.number_input("Auxílio Home Office (R$)", value=float(preset.get("home", 0)), min_value=0.0)
        else:
            home = st.number_input("Auxílio Home Office (R$)", value=0.0, min_value=0.0)
        
        epi = st.number_input("EPI/Equipamentos (R$)", value=0.0, min_value=0.0)
        outros = st.number_input("Outros Custos (R$)", value=0.0, min_value=0.0)

    st.write("---")
    
    msg = urllib.parse.quote("Olá Rodrigo! Gostaria de validar a calculadora.")
    st.markdown(f"[💬 WhatsApp](https://wa.me/11977019335?text={msg})")

# ---------------- VALIDAÇÕES E ALERTAS ----------------
if salario > 0 and salario < SALARIO_MINIMO_2025:
    st.warning(f"⚠️ Atenção: Salário abaixo do mínimo nacional (R$ {SALARIO_MINIMO_2025:,.2f})")

if regime == "CLT (Lucro Presumido/Real)" and salario > TETO_INSS_2025:
    st.info(f"ℹ️ Salário acima do teto. INSS patronal calculado sobre R$ {TETO_INSS_2025:,.2f}")

custo_vt_mensal = (n_pass * v_pass) * 22
if custo_vt_mensal > salario * 0.06 and salario > 0:
    economia = custo_vt_mensal - (salario * 0.06)
    st.success(f"💰 Empresa economiza R$ {economia:.2f}/mês com limite de desconto de 6% no VT")

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs(["👤 Cálculo Individual", "⚖️ Comparador de Regimes", "💹 Break-even", "📁 Processar Planilha"])

# ---------------- CÁLCULO INDIVIDUAL ----------------
with tab1:

    st.subheader(f"Análise de Custo: {regime}")

    res = calcular_custos(
        salario, regime, incluir,
        n_pass, v_pass, vr, va,
        saude, odonto, seguro,
        home, epi, outros,
        rat_perc, terceiros_perc, dependentes
    )

    # Métricas principais
    c1, c2, c3, c4 = st.columns(4)

    c1.metric("💼 Salário Bruto", f"R$ {salario:,.2f}")
    c2.metric("💵 Salário Líquido", f"R$ {res['_salario_liquido']:,.2f}")
    c3.metric("💰 Custo Total Mensal", f"R$ {res['Custo Total Mensal']:,.2f}")
    
    mult = res['Custo Total Mensal'] / salario if salario else 0
    c4.metric("📊 Multiplicador", f"{mult:.2f}x")

    st.write("")
    
    # Gráfico de Pizza
    col1, col2 = st.columns([2, 1])
    
    with col1:
        df_grafico = pd.DataFrame(res.items(), columns=["Descrição", "Valor"])
        df_grafico = df_grafico[
            (df_grafico["Valor"] > 0) & 
            (~df_grafico["Descrição"].str.contains("Total")) &
            (~df_grafico["Descrição"].str.startswith("_")) &
            (df_grafico["Descrição"] != "Salário Base")
        ]
        
        if not df_grafico.empty:
            fig = px.pie(
                df_grafico,
                values='Valor',
                names='Descrição',
                title='📊 Distribuição dos Custos',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📋 Resumo Fiscal")
        
        if "CLT" in regime:
            st.metric("INSS Funcionário", f"R$ {res.get('_inss_funcionario', 0):,.2f}")
            st.metric("IRRF", f"R$ {res.get('_irrf_funcionario', 0):,.2f}")
            
            desconto_vt = min(custo_vt_mensal, salario * 0.06)
            st.metric("Desconto VT", f"R$ {desconto_vt:,.2f}")
            
            total_descontos = res.get('_inss_funcionario', 0) + res.get('_irrf_funcionario', 0) + desconto_vt
            st.metric("Total Descontos", f"R$ {total_descontos:,.2f}", delta=f"-{(total_descontos/salario*100):.1f}%")

    # Tabela detalhada
    st.subheader("📑 Detalhamento de Custos")
    df = pd.DataFrame(res.items(), columns=["Descrição", "Valor"])
    df = df[(df["Valor"] > 0) & (~df["Descrição"].str.contains("Total")) & (~df["Descrição"].startswith("_"))]
    
    df["Percentual"] = df["Valor"].apply(lambda x: f"{(x/res['Custo Total Mensal']*100):.1f}%" if res['Custo Total Mensal'] > 0 else "0%")
    df["Valor"] = df["Valor"].apply(lambda x: f"R$ {x:,.2f}")
    
    st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------- COMPARADOR DE REGIMES ----------------
with tab2:
    st.subheader("⚖️ Comparação entre Regimes")
    
    col1, col2, col3 = st.columns(3)
    
    regimes_comparar = [
        "CLT (Simples Nacional)",
        "CLT (Lucro Presumido/Real)",
        "PJ"
    ]
    
    resultados_comp = {}
    
    for idx, reg in enumerate(regimes_comparar):
        resultados_comp[reg] = calcular_custos(
            salario, reg, incluir,
            n_pass, v_pass, vr, va,
            saude, odonto, seguro,
            home, epi, outros,
            rat_perc, terceiros_perc, dependentes
        )
    
    with col1:
        st.markdown("### 🟢 CLT Simples")
        r1 = resultados_comp["CLT (Simples Nacional)"]
        st.metric("Custo Mensal", f"R$ {r1['Custo Total Mensal']:,.2f}")
        st.metric("Custo Anual", f"R$ {r1['Custo Total Anual']:,.2f}")
        st.metric("Multiplicador", f"{(r1['Custo Total Mensal']/salario):.2f}x")
        st.metric("Salário Líquido", f"R$ {r1['_salario_liquido']:,.2f}")
    
    with col2:
        st.markdown("### 🟡 CLT LP/Real")
        r2 = resultados_comp["CLT (Lucro Presumido/Real)"]
        st.metric("Custo Mensal", f"R$ {r2['Custo Total Mensal']:,.2f}")
        st.metric("Custo Anual", f"R$ {r2['Custo Total Anual']:,.2f}")
        st.metric("Multiplicador", f"{(r2['Custo Total Mensal']/salario):.2f}x")
        st.metric("Salário Líquido", f"R$ {r2['_salario_liquido']:,.2f}")
    
    with col3:
        st.markdown("### 🔵 PJ")
        r3 = resultados_comp["PJ"]
        st.metric("Custo Mensal", f"R$ {r3['Custo Total Mensal']:,.2f}")
        st.metric("Custo Anual", f"R$ {r3['Custo Total Anual']:,.2f}")
        st.metric("Multiplicador", f"{(r3['Custo Total Mensal']/salario):.2f}x")
        st.metric("Valor Líquido (est.)", f"R$ {r3['_salario_liquido']:,.2f}")
    
    # Gráfico comparativo
    st.subheader("📊 Comparativo Visual")
    
    df_comp = pd.DataFrame({
        'Regime': regimes_comparar,
        'Custo Mensal': [r1['Custo Total Mensal'], r2['Custo Total Mensal'], r3['Custo Total Mensal']],
        'Custo Anual': [r1['Custo Total Anual'], r2['Custo Total Anual'], r3['Custo Total Anual']]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Custo Mensal',
        x=df_comp['Regime'],
        y=df_comp['Custo Mensal'],
        text=df_comp['Custo Mensal'].apply(lambda x: f'R$ {x:,.2f}'),
        textposition='outside'
    ))
    
    fig.update_layout(
        title='Comparação de Custos Mensais',
        yaxis_title='Valor (R$)',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Análise de economia
    custos = [r1['Custo Total Mensal'], r2['Custo Total Mensal'], r3['Custo Total Mensal']]
    menor_custo = min(custos)
    regime_economico = regimes_comparar[custos.index(menor_custo)]
    
    st.success(f"💡 **Regime mais econômico:** {regime_economico} com custo mensal de R$ {menor_custo:,.2f}")
    
    if regime_economico != regimes_comparar[0]:
        economia_anual = (custos[0] - menor_custo) * 12
        st.info(f"💰 Economia anual potencial: R$ {economia_anual:,.2f} em relação ao CLT Simples")

# ---------------- BREAK-EVEN ----------------
with tab3:
    st.subheader("💹 Análise de Ponto de Equilíbrio")
    
    col1, col2 = st.columns(2)
    
    with col1:
        receita_hora = st.number_input("Receita gerada por hora (R$)", value=0.0, min_value=0.0, step=10.0)
        horas_mes = st.number_input("Horas trabalhadas/mês", value=160.0, min_value=0.0, step=10.0)
    
    with col2:
        margem_desejada = st.slider("Margem de lucro desejada (%)", 0, 100, 30)
    
    if receita_hora > 0 and horas_mes > 0:
        receita_total = receita_hora * horas_mes
        custo_total = res['Custo Total Mensal']
        lucro_bruto = receita_total - custo_total
        margem_real = (lucro_bruto / receita_total * 100) if receita_total > 0 else 0
        
        # Métricas
        c1, c2, c3, c4 = st.columns(4)
        
        c1.metric("💰 Receita Mensal", f"R$ {receita_total:,.2f}")
        c2.metric("💸 Custo Total", f"R$ {custo_total:,.2f}")
        c3.metric("📈 Lucro Bruto", f"R$ {lucro_bruto:,.2f}", 
                  delta=f"{margem_real:.1f}%")
        
        receita_necessaria = custo_total / (1 - margem_desejada/100)
        c4.metric("🎯 Receita p/ Margem", f"R$ {receita_necessaria:,.2f}")
        
        # Gráfico de barras empilhadas
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Custo',
            x=['Atual', f'Meta ({margem_desejada}%)'],
            y=[custo_total, custo_total],
            marker_color='#FF6B6B'
        ))
        
        fig.add_trace(go.Bar(
            name='Lucro',
            x=['Atual', f'Meta ({margem_desejada}%)'],
            y=[lucro_bruto, receita_necessaria - custo_total],
            marker_color='#4CAF50'
        ))
        
        fig.update_layout(
            barmode='stack',
            title='Análise de Receita vs Custo',
            yaxis_title='Valor (R$)',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendações
        if margem_real < margem_desejada:
            diferenca = receita_necessaria - receita_total
            st.warning(f"⚠️ Para atingir {margem_desejada}% de margem, é necessário aumentar a receita em R$ {diferenca:,.2f}/mês")
            
            horas_necessarias = receita_necessaria / receita_hora
            st.info(f"💡 Isso equivale a trabalhar {horas_necessarias:.0f} horas/mês (ou R$ {(receita_necessaria/horas_mes):.2f}/hora em {horas_mes:.0f}h)")
        else:
            st.success(f"✅ Margem atual ({margem_real:.1f}%) está acima da meta de {margem_desejada}%!")
    else:
        st.info("👆 Preencha os campos acima para calcular o ponto de equilíbrio")

# ---------------- PROCESSAR PLANILHA ----------------
with tab4:

    arquivo = st.file_uploader("📤 Envie sua planilha com dados dos funcionários", type=["xlsx", "csv"])

    if arquivo:
        df_input = pd.read_excel(arquivo) if arquivo.name.endswith("xlsx") else pd.read_csv(arquivo)
        st.success(f"✅ Planilha carregada com {len(df_input)} registros")
        
        st.dataframe(df_input.head(), use_container_width=True)

        col1, col2 = st.columns(2)
        
        with col1:
            coluna_salario = st.selectbox("📊 Coluna de salário", df_input.columns)
        
        with col2:
            coluna_grupo = st.selectbox("📁 Coluna para agrupar relatório", df_input.columns)

        if st.button("🚀 Calcular Custos", type="primary"):
            with st.spinner("Processando..."):
                resultados = df_input[coluna_salario].apply(
                    lambda x: calcular_custos(
                        x, regime, incluir,
                        n_pass, v_pass, vr, va,
                        saude, odonto, seguro,
                        home, epi, outros,
                        rat_perc, terceiros_perc, dependentes
                    )
                )

                df_final = pd.concat([df_input, pd.DataFrame(list(resultados))], axis=1)
                
                # Remover colunas internas
                colunas_remover = [col for col in df_final.columns if col.startswith('_')]
                df_final = df_final.drop(columns=colunas_remover)
                
                st.success("✅ Cálculos concluídos!")
                st.dataframe(df_final, use_container_width=True)

                # -------- RELATÓRIO CONSOLIDADO --------
                relatorio = (
                    df_final
                    .groupby(coluna_grupo)
                    .agg({
                        'Custo Total Mensal': 'sum',
                        'Custo Total Anual': 'sum',
                        coluna_salario: 'count'
                    })
                    .rename(columns={coluna_salario: 'Quantidade'})
                    .reset_index()
                    .sort_values("Custo Total Anual", ascending=False)
                )

                st.subheader("📊 Relatório Consolidado por " + coluna_grupo)
                
                # Métricas totais
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Funcionários", f"{len(df_final)}")
                c2.metric("Custo Total Mensal", f"R$ {relatorio['Custo Total Mensal'].sum():,.2f}")
                c3.metric("Custo Total Anual", f"R$ {relatorio['Custo Total Anual'].sum():,.2f}")
                
                st.dataframe(relatorio, use_container_width=True, hide_index=True)
                
                # Gráfico do relatório
                fig = px.bar(
                    relatorio,
                    x=coluna_grupo,
                    y='Custo Total Anual',
                    title=f'Custo Anual por {coluna_grupo}',
                    text='Custo Total Anual',
                    color='Custo Total Anual',
                    color_continuous_scale='Viridis'
                )
                fig.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

                # -------- EXPORTAÇÃO EXCEL COM 2 ABAS --------
                output = BytesIO()

                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_final.to_excel(writer, sheet_name="Detalhamento", index=False)
                    relatorio.to_excel(writer, sheet_name="Consolidado", index=False)

                st.download_button(
                    "📥 Baixar Relatório Excel Completo",
                    output.getvalue(),
                    "relatorio_custos_funcionarios.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

