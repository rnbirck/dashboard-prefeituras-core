import streamlit as st
import pandas as pd

# ==============================================================================
# IMPORTAÇÕES DE FUNÇÕES E DADOS
# ==============================================================================

from dashboard_core.utils import (
    MESES_DIC,
    checar_ult_ano_completo,
    criar_grafico_barras,
    titulo_centralizado,
    style_saldo_variacao,
)

# --- VARIÁVEIS GLOBAIS DO MÓDULO ---
CORES_MUNICIPIOS = {}
anos_de_interesse = []


def set_seguranca_config(cores_municipios, anos_interesse):
    """
    Configura valores específicos do município e anos de interesse.
    Deve ser chamado pelo app.py antes de renderizar a página.
    """
    global CORES_MUNICIPIOS, anos_de_interesse
    CORES_MUNICIPIOS = cores_municipios or {}
    anos_de_interesse = anos_interesse or []


# --- FUNÇÕES AUXILIARES ---
def formatar_valor_br(x):
    """Formata número float para padrão BR."""
    if pd.isna(x):
        return "-"
    if isinstance(x, int) or x.is_integer():
        return f"{x:,.0f}".replace(",", ".")
    return f"{x:,.2f}".replace(".", ",")


# --- FUNÇÕES DE CALLBACK ---


def set_expander_open(key):
    """Define o estado de um expander específico como True (aberto)."""
    st.session_state[key] = True


def geral_callback():
    set_expander_open("geral_expander_state")


def mulher_callback():
    set_expander_open("mulher_expander_state")


def drogas_callback():
    set_expander_open("drogas_expander_state")


def furtos_callback():
    set_expander_open("furtos_expander_state")


# ==============================================================================
# FUNÇÕES DA PÁGINA DE SEGURANÇA
# ==============================================================================


@st.cache_data
def preparar_dados_graficos_seguranca(
    df_filtrado, coluna_selecionada, anos_visualizacao, is_taxa=False
):
    """
    Prepara os DataFrames pivotados para as abas da página de segurança.
    Retorna também os DataFrames de Variação (%) para Acumulado e Anual.
    """
    df_hist = pd.DataFrame()
    df_acum, df_acum_var = pd.DataFrame(), pd.DataFrame()
    df_anual, df_anual_var = pd.DataFrame(), pd.DataFrame()
    ult_ano, ult_mes = None, None

    coluna_valor = f"taxa_{coluna_selecionada}" if is_taxa else coluna_selecionada

    if not df_filtrado.empty and coluna_valor in df_filtrado.columns:
        # Pega o último ano DENTRO dos anos de visualização desejados
        df_range_visualizacao = df_filtrado[df_filtrado["ano"].isin(anos_visualizacao)]
        if df_range_visualizacao.empty:
            ult_ano = df_filtrado["ano"].max()
        else:
            ult_ano = df_range_visualizacao["ano"].max()

        ult_mes = df_filtrado[df_filtrado["ano"] == ult_ano]["mes"].max()

        # 1. Evolução Mensal
        df_hist_full = (
            df_filtrado.assign(
                date=lambda x: pd.to_datetime(
                    x["ano"].astype(str)
                    + "-"
                    + x["mes"].astype(str).str.zfill(2)
                    + "-01"
                )
            )
            .pivot_table(
                index="date",
                columns="municipio",
                values=coluna_valor,
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
        )
        df_hist = df_hist_full[df_hist_full.index.year.isin(anos_visualizacao)]

        # 2. Acumulado no Ano
        df_acum_temp = df_filtrado[df_filtrado["mes"] <= ult_mes]

        df_acum_full = df_acum_temp.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_valor,
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        # Cálculo da Variação (usando o ano buffer)
        df_acum_var_full = df_acum_full.pct_change() * 100

        # Filtra anos
        df_acum = df_acum_full[df_acum_full.index.isin(anos_visualizacao)]
        df_acum_var = df_acum_var_full[df_acum_var_full.index.isin(anos_visualizacao)]

        # 3. Anual (Anos Completos)
        ano_completo = checar_ult_ano_completo(df_filtrado)
        df_anual_temp = df_filtrado[df_filtrado["ano"] <= ano_completo]

        df_anual_calc = df_anual_temp.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_valor,
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        df_anual_var_full = df_anual_calc.pct_change() * 100

        # Filtra e ordena
        df_anual = df_anual_calc[
            df_anual_calc.index.isin(anos_visualizacao)
        ].sort_index(ascending=False)
        df_anual_var = df_anual_var_full[
            df_anual_var_full.index.isin(anos_visualizacao)
        ].sort_index(ascending=False)

    return df_hist, df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes


@st.cache_data
def preparar_dados_furtos_por_tipo(
    df_furtos,
    anos_visualizacao,
    ult_ano_referencia=None,
    ult_mes_referencia=None,
):
    """
    Prepara os DataFrames para análise de furtos por tipo.
    Retorna dados para Acumulado no Ano e Anual com valores absolutos e variação.
    """
    df_acum = pd.DataFrame()
    df_acum_var = pd.DataFrame()
    df_anual = pd.DataFrame()
    df_anual_var = pd.DataFrame()
    ult_ano, ult_mes = None, None

    if df_furtos.empty:
        return df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes

    # Usa referência externa quando disponível (série mensal geral de furtos).
    if ult_ano_referencia is not None and ult_mes_referencia is not None:
        ult_ano = int(ult_ano_referencia)
        ult_mes = int(ult_mes_referencia)
    else:
        # Fallback: determina o mês no último ano com base em dado efetivo.
        # Em algumas bases, meses futuros podem existir com valor zero.
        ult_ano = df_furtos["ano"].max()
        df_ult_ano = df_furtos[df_furtos["ano"] == ult_ano].copy()

        if not df_ult_ano.empty:
            df_ult_ano["mes"] = pd.to_numeric(df_ult_ano["mes"], errors="coerce")
            df_ult_ano["n_furtos"] = pd.to_numeric(
                df_ult_ano["n_furtos"], errors="coerce"
            )

            soma_por_mes = df_ult_ano.groupby("mes", dropna=True)["n_furtos"].sum()
            meses_com_dado = soma_por_mes[soma_por_mes > 0].index.tolist()

            if meses_com_dado:
                ult_mes = int(max(meses_com_dado))
            else:
                ult_mes = int(df_ult_ano["mes"].max())

    # 1. Acumulado no Ano (até o último mês disponível)
    df_acum_temp = df_furtos[df_furtos["mes"] <= ult_mes]

    df_acum_full = df_acum_temp.pivot_table(
        index="ano",
        columns="tipo_furtos",
        values="n_furtos",
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    # Variação YoY para Acumulado
    df_acum_var_full = df_acum_full.pct_change() * 100

    # Filtrar anos
    df_acum = df_acum_full[df_acum_full.index.isin(anos_visualizacao)]
    df_acum_var = df_acum_var_full[df_acum_var_full.index.isin(anos_visualizacao)]

    # 2. Anual (Anos Completos - bimestre 12)
    ano_completo = checar_ult_ano_completo(df_furtos)
    df_anual_temp = df_furtos[df_furtos["ano"] <= ano_completo]

    df_anual_full = df_anual_temp.pivot_table(
        index="ano",
        columns="tipo_furtos",
        values="n_furtos",
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    # Variação YoY para Anual
    df_anual_var_full = df_anual_full.pct_change() * 100

    # Filtrar anos
    df_anual = df_anual_full[df_anual_full.index.isin(anos_visualizacao)]
    df_anual_var = df_anual_var_full[df_anual_var_full.index.isin(anos_visualizacao)]

    return df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes


def display_secao_seguranca(
    df_seguranca,
    df_seguranca_taxa,
    titulo_expander,
    dicionario_indicadores,
    key_prefix,
    expander_state_key,
    callback_func,
    label_taxa_desc="Taxa por 10 mil hab.",
    anos_visuais=None,
):
    """
    Exibe uma seção de indicadores de segurança com controles dentro das abas.
    """
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    # Usa a variável global se não for passado argumento
    if anos_visuais is None:
        anos_visuais = anos_de_interesse

    with st.expander(titulo_expander, expanded=st.session_state[expander_state_key]):
        # --- 1. SELETOR DE INDICADOR ---
        indicador_selecionado = st.selectbox(
            "Selecione um indicador:",
            options=list(dicionario_indicadores.keys()),
            key=f"{key_prefix}_selectbox",
            on_change=callback_func,
        )
        coluna_selecionada = dicionario_indicadores[indicador_selecionado]

        # --- 2. PREPARAÇÃO DOS DADOS ---
        # Dados Absolutos
        (
            hist_abs,
            acum_abs,
            acum_var_abs,
            anual_abs,
            anual_var_abs,
            ult_ano,
            ult_mes,
        ) = preparar_dados_graficos_seguranca(
            df_seguranca, coluna_selecionada, anos_visuais, is_taxa=False
        )

        indicadores_taxa_frota = {"furto_veiculo", "roubo_veiculo"}
        usa_taxa_frota = coluna_selecionada in indicadores_taxa_frota
        label_taxa_exibicao = (
            "Taxa por 10 mil veículos" if usa_taxa_frota else label_taxa_desc
        )

        # Dados Taxa
        (hist_taxa, acum_taxa, _, anual_taxa, _, _, _) = (
            preparar_dados_graficos_seguranca(
                df_seguranca_taxa, coluna_selecionada, anos_visuais, is_taxa=True
            )
        )

        # Filtra anos disponíveis baseado nos dados reais do DataFrame
        anos_com_dados = (
            sorted(
                df_seguranca[coluna_selecionada]
                .notna()
                .loc[lambda x: x]
                .index.to_series()
                .apply(lambda idx: df_seguranca.loc[idx, "ano"])
                .unique()
                .tolist(),
                reverse=True,
            )
            if not df_seguranca.empty and coluna_selecionada in df_seguranca.columns
            else []
        )

        # Intersecção entre anos de visualização e anos com dados
        anos_disponiveis = (
            sorted([ano for ano in anos_visuais if ano in anos_com_dados], reverse=True)
            if anos_com_dados
            else sorted(list(anos_visuais), reverse=True)
        )

        # --- 3. NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = f"main_tab_nav_{key_prefix}"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Evolução Mensal"

        aba_selecionada = st.pills(
            "Selecione o tipo de análise temporal:",
            options=["Evolução Mensal", "Acumulado no Ano", "Anual"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Evolução Mensal"

        # --- ABA 1: Evolução ---
        if aba_selecionada == "Evolução Mensal":
            col_opt, col_ano = st.columns([0.5, 0.5])
            with col_opt:
                # CORREÇÃO: Inicialização explícita da chave
                key_hist = f"hist_mode_{key_prefix}"
                if key_hist not in st.session_state:
                    st.session_state[key_hist] = "Nº Ocorrências"

                modo_hist = st.segmented_control(
                    "Visualizar:",
                    options=["Nº Ocorrências", label_taxa_exibicao],
                    key=key_hist,
                    selection_mode="single",
                    on_change=callback_func,
                )

                # Fallback: se desmarcar (None), força o padrão
                if not modo_hist:
                    modo_hist = "Nº Ocorrências"

            with col_ano:
                ano_hist = st.selectbox(
                    "Ano:",
                    options=anos_disponiveis,
                    index=0,
                    key=f"hist_ano_{key_prefix}",
                    on_change=callback_func,
                    label_visibility="visible",
                )

            if modo_hist == "Nº Ocorrências":
                df_plot = hist_abs
                lbl_y = "Ocorrências"
                fmt = ",.0f"
                hover = ",.0f"
                titulo_grafico = (
                    f"Número de Ocorrências - {indicador_selecionado} - {ano_hist}"
                )
            else:
                df_plot = hist_taxa
                lbl_y = label_taxa_exibicao
                fmt = ",.1f"
                hover = ",.2f"
                titulo_grafico = (
                    f"{label_taxa_exibicao} - {indicador_selecionado} - {ano_hist}"
                )

            titulo_centralizado(titulo_grafico, 5)

            if not df_plot.empty:
                df_plot_ano = df_plot[df_plot.index.year == ano_hist]
                if not df_plot_ano.empty:
                    df_plot_ano.index = [
                        f"{MESES_DIC[d.month][:3]}/{str(d.year)[2:]}"
                        for d in df_plot_ano.index
                    ]
                    fig = criar_grafico_barras(
                        df=df_plot_ano,
                        titulo="",
                        label_y=lbl_y,
                        barmode="group",
                        height=400,
                        data_label_format=fmt,
                        color_map=CORES_MUNICIPIOS,
                        hover_label_format=hover,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"Sem dados mensais para {ano_hist}.")
            else:
                st.warning("Sem dados disponíveis.")

        # --- ABA 2: ACUMULADO ---
        if ult_mes and aba_selecionada == "Acumulado no Ano":
            # CORREÇÃO: Inicialização explícita da chave
            key_acum = f"acum_mode_{key_prefix}"
            if key_acum not in st.session_state:
                st.session_state[key_acum] = "Nº Ocorrências"

            modo_acum = st.segmented_control(
                "Visualizar:",
                options=["Nº Ocorrências", label_taxa_exibicao, "Variação (%)"],
                key=key_acum,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_acum:
                modo_acum = "Nº Ocorrências"

            periodo_txt = f"Jan a {MESES_DIC[ult_mes]}"

            if modo_acum == "Variação (%)":
                titulo_centralizado(
                    f"Variação Acumulada - {indicador_selecionado} - {periodo_txt}",
                    5,
                )
                df_var_plot = acum_var_abs.copy().sort_index(ascending=False)
                df_var_plot.index = df_var_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y="Variação (%)",
                    barmode="group",
                    height=400,
                    data_label_format="+,.1f",
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format="+,.2f",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                if modo_acum == "Nº Ocorrências":
                    df_plot = acum_abs.copy()
                    lbl_y = "Ocorrências"
                    fmt = ",.0f"
                    hover = ",.0f"
                    titulo_grafico = f"Número de Ocorrências - {indicador_selecionado} - {periodo_txt}"
                else:
                    df_plot = acum_taxa.copy()
                    lbl_y = label_taxa_exibicao
                    fmt = ",.1f"
                    hover = ",.2f"
                    titulo_grafico = f"{label_taxa_exibicao} - {indicador_selecionado} - {periodo_txt}"

                titulo_centralizado(titulo_grafico, 5)

                df_plot.index = (
                    "Jan-"
                    + MESES_DIC[ult_mes][:3]
                    + "/"
                    + df_plot.index.astype(str).str.slice(-2)
                )
                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=lbl_y,
                    barmode="group",
                    height=400,
                    data_label_format=fmt,
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format=hover,
                )
                st.plotly_chart(fig, use_container_width=True)

        # --- ABA 3: ANUAL ---
        if aba_selecionada == "Anual":
            # CORREÇÃO: Inicialização explícita da chave
            key_anual = f"anual_mode_{key_prefix}"
            if key_anual not in st.session_state:
                st.session_state[key_anual] = "Nº Ocorrências"

            modo_anual = st.segmented_control(
                "Visualizar:",
                options=["Nº Ocorrências", label_taxa_exibicao, "Variação (%)"],
                key=key_anual,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_anual:
                modo_anual = "Nº Ocorrências"

            if modo_anual == "Variação (%)":
                titulo_centralizado(f"Variação Anual - {indicador_selecionado}", 5)
                df_var_plot = anual_var_abs.copy()
                df_var_plot.index = df_var_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y="Variação (%)",
                    barmode="group",
                    height=400,
                    data_label_format="+,.1f",
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format="+,.2f",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                if modo_anual == "Nº Ocorrências":
                    df_plot = anual_abs
                    lbl_y = "Ocorrências"
                    fmt = ",.0f"
                    hover = ",.0f"
                    titulo_grafico = (
                        f"Número de Ocorrências - {indicador_selecionado} - Anual"
                    )
                else:
                    df_plot = anual_taxa
                    lbl_y = label_taxa_exibicao
                    fmt = ",.1f"
                    hover = ",.2f"
                    titulo_grafico = (
                        f"{label_taxa_exibicao} - {indicador_selecionado} - Anual"
                    )

                titulo_centralizado(titulo_grafico, 5)

                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=lbl_y,
                    barmode="group",
                    height=400,
                    data_label_format=fmt,
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format=hover,
                )
                st.plotly_chart(fig, use_container_width=True)


def display_furtos_por_tipo(
    df_furtos,
    expander_state_key,
    callback_func,
    ult_ano_referencia=None,
    ult_mes_referencia=None,
):
    """
    Exibe análise de furtos por tipo em formato de tabela.
    Mostra o tipo de furto nas linhas e anos nas colunas com valores absolutos ou variação.
    """
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander("Furtos por Tipo", expanded=st.session_state[expander_state_key]):
        if df_furtos.empty:
            st.warning("Não há dados de furtos por tipo disponíveis.")
            return

        # Preparar dados
        (
            df_acum,
            df_acum_var,
            df_anual,
            df_anual_var,
            ult_ano,
            ult_mes,
        ) = preparar_dados_furtos_por_tipo(
            df_furtos,
            anos_de_interesse,
            ult_ano_referencia=ult_ano_referencia,
            ult_mes_referencia=ult_mes_referencia,
        )

        # Navegação entre abas
        key_main_tab = "main_tab_nav_furtos"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Acumulado no Ano"

        aba_selecionada = st.pills(
            "Selecione o tipo de análise temporal:",
            options=["Acumulado no Ano", "Anual"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Acumulado no Ano"

        # --- ABA 1: ACUMULADO NO ANO ---
        if aba_selecionada == "Acumulado no Ano":
            # Segmented control para métrica
            key_acum = "acum_mode_furtos"

            modo_acum = st.segmented_control(
                "Visualizar:",
                options=["Número de Furtos", "Variação (%)"],
                key=key_acum,
                selection_mode="single",
                on_change=callback_func,
                default="Número de Furtos",
            )

            if not modo_acum:
                modo_acum = "Número de Furtos"

            # Preparar tabela de valores (sempre necessária para ordenação)
            if not df_acum.empty:
                # Determinar o último ano dos dados (antes do transpose)
                ultimo_ano_dados = df_acum.index.max()  # Pega o último ano numérico

                # Ordenar por tipo de furto baseado no último ano (usando df original)
                df_ordenado = df_acum.loc[ultimo_ano_dados].sort_values(ascending=False)
                ordem_index = df_ordenado.index  # Ordem dos tipos de furto

                # Transpor e reindexar pela ordem correta
                df_tabela_valores = df_acum.T.reindex(ordem_index)
                df_tabela_valores.index.name = "Tipo de Furto"

                # Formatar as colunas
                df_tabela_valores.columns = [
                    f"Jan-{MESES_DIC[ult_mes][:3]}/{str(ano)[-2:]}"
                    for ano in df_tabela_valores.columns
                ]

            if modo_acum == "Variação (%)":
                titulo_grafico = f"Furtos por Tipo - Acumulado até {MESES_DIC.get(ult_mes, ult_mes)} - Variação (%)"
                titulo_centralizado(titulo_grafico, 5)

                if not df_acum_var.empty:
                    # Transpor para ter tipos de furto nas linhas e anos nas colunas
                    df_tabela = df_acum_var.T
                    df_tabela.index.name = "Tipo de Furto"

                    # Formatar índice das colunas para incluir período
                    df_tabela.columns = [
                        f"Jan-{MESES_DIC[ult_mes][:3]}/{str(ano)[-2:]}"
                        for ano in df_tabela.columns
                    ]

                    # Reindexar pela ordem dos valores (não da variação)
                    df_tabela = df_tabela.reindex(ordem_index)

                    # Remover colunas que são totalmente NaN (primeiro ano sem dados anteriores)
                    df_tabela = df_tabela.dropna(axis=1, how="all")

                    # Estilizar tabela
                    styler = df_tabela.style.format("{:+.1f}%").map(
                        style_saldo_variacao
                    )
                    st.dataframe(styler, width="stretch")
                else:
                    st.info("Não há dados de variação disponíveis.")

            else:  # Número de Furtos
                titulo_grafico = (
                    f"Furtos por Tipo - Acumulado até {MESES_DIC.get(ult_mes, ult_mes)}"
                )
                titulo_centralizado(titulo_grafico, 5)

                if not df_acum.empty:
                    # Usar a tabela já preparada e ordenada
                    df_tabela = df_tabela_valores

                    # Estilizar tabela
                    styler = df_tabela.style.format(
                        formatar_valor_br
                    ).background_gradient(cmap="Blues", axis=0)
                    st.dataframe(styler, width="stretch")
                else:
                    st.info("Sem dados disponíveis.")

        # --- ABA 2: ANUAL ---
        elif aba_selecionada == "Anual":
            if not df_anual.empty:
                # Segmented control para métrica
                key_anual = "anual_mode_furtos"

                modo_anual = st.segmented_control(
                    "Visualizar:",
                    options=["Número de Furtos", "Variação (%)"],
                    key=key_anual,
                    selection_mode="single",
                    on_change=callback_func,
                    default="Número de Furtos",
                )

                if not modo_anual:
                    modo_anual = "Número de Furtos"

                # Preparar tabela de valores (sempre necessária para ordenação)
                # Determinar o último ano dos dados (antes do transpose)
                ultimo_ano_dados = df_anual.index.max()  # Pega o último ano numérico

                # Ordenar por tipo de furto baseado no último ano (usando df original)
                df_ordenado = df_anual.loc[ultimo_ano_dados].sort_values(
                    ascending=False
                )
                ordem_index = df_ordenado.index  # Ordem dos tipos de furto

                # Transpor e reindexar pela ordem correta
                df_tabela_valores = df_anual.T.reindex(ordem_index)
                df_tabela_valores.index.name = "Tipo de Furto"

                # Formatar as colunas
                df_tabela_valores.columns = [
                    str(ano) for ano in df_tabela_valores.columns
                ]

                if modo_anual == "Variação (%)":
                    titulo_grafico = "Furtos por Tipo - Evolução Anual - Variação (%)"
                    titulo_centralizado(titulo_grafico, 5)

                    if not df_anual_var.empty:
                        # Transpor para ter tipos de furto nas linhas e anos nas colunas
                        df_tabela = df_anual_var.T
                        df_tabela.index.name = "Tipo de Furto"

                        # Formatar índice das colunas (apenas ano)
                        df_tabela.columns = [str(ano) for ano in df_tabela.columns]

                        # Reindexar pela ordem dos valores (não da variação)
                        df_tabela = df_tabela.reindex(ordem_index)

                        # Remover colunas que são totalmente NaN (primeiro ano sem dados anteriores)
                        df_tabela = df_tabela.dropna(axis=1, how="all")

                        # Estilizar tabela
                        styler = df_tabela.style.format("{:+.1f}%").map(
                            style_saldo_variacao
                        )
                        st.dataframe(styler, width="stretch")
                    else:
                        st.info("Não há dados de variação disponíveis.")

                else:  # Número de Furtos
                    titulo_grafico = "Furtos por Tipo - Evolução Anual"
                    titulo_centralizado(titulo_grafico, 5)

                    if not df_anual.empty:
                        # Usar a tabela já preparada e ordenada
                        df_tabela = df_tabela_valores

                        # Estilizar tabela
                        styler = df_tabela.style.format(
                            formatar_valor_br
                        ).background_gradient(cmap="Blues", axis=0)
                        st.dataframe(styler, width="stretch")
                    else:
                        st.info("Sem dados disponíveis.")
            else:
                st.warning("Não há dados anuais completos disponíveis.")


def show_page_seguranca(df_seguranca, df_seguranca_taxa, df_seguranca_furtos):
    # Inicialização dos estados dos expanders
    if "geral_expander_state" not in st.session_state:
        st.session_state.geral_expander_state = False
    if "mulher_expander_state" not in st.session_state:
        st.session_state.mulher_expander_state = False
    if "drogas_expander_state" not in st.session_state:
        st.session_state.drogas_expander_state = False
    if "furtos_expander_state" not in st.session_state:
        st.session_state.furtos_expander_state = False

    titulo_centralizado("Dashboard de Segurança", 1)
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

    # Dicionários de Indicadores
    INDICADORES_GERAIS = {
        "Homicídio Doloso": "homicidio_doloso",
        "Furtos": "furtos",
        "Roubos": "roubos",
        "Furto de Veículo": "furto_veiculo",
        "Roubo de Veículo": "roubo_veiculo",
        "Estelionato": "estelionato",
    }

    INDICADORES_VIOLENCIA_MULHER = {
        "Feminicídio Consumado": "feminicidio_consumado",
        "Feminicídio Tentado": "feminicidio_tentado",
        "Ameaça": "ameaca",
        "Estupro": "estupro",
        "Lesão Corporal": "lesao_corporal",
    }

    INDICADORES_DROGAS_ARMAS = {
        "Delitos com Armas e Munições": "delitos_armas_municoes",
        "Posse de Entorpecentes": "entorpecentes_posse",
        "Tráfico de Entorpecentes": "entorpecentes_trafico",
    }

    # Renderização das Seções
    display_secao_seguranca(
        df_seguranca,
        df_seguranca_taxa,
        "Indicadores Gerais",
        INDICADORES_GERAIS,
        "geral",
        "geral_expander_state",
        geral_callback,
    )
    display_secao_seguranca(
        df_seguranca,
        df_seguranca_taxa,
        "Violência Contra a Mulher",
        INDICADORES_VIOLENCIA_MULHER,
        "mulher",
        "mulher_expander_state",
        mulher_callback,
        label_taxa_desc="Taxa por 10 mil mulheres",
    )
    display_secao_seguranca(
        df_seguranca,
        df_seguranca_taxa,
        "Crimes Relacionados à Drogas e Armas",
        INDICADORES_DROGAS_ARMAS,
        "drogas",
        "drogas_expander_state",
        drogas_callback,
    )
    ult_ano_ref_furtos, ult_mes_ref_furtos = None, None
    if (
        df_seguranca is not None
        and not df_seguranca.empty
        and {"ano", "mes", "furtos"}.issubset(df_seguranca.columns)
    ):
        df_ref = df_seguranca[["ano", "mes", "furtos"]].copy()
        df_ref["ano"] = pd.to_numeric(df_ref["ano"], errors="coerce")
        df_ref["mes"] = pd.to_numeric(df_ref["mes"], errors="coerce")
        df_ref["furtos"] = pd.to_numeric(df_ref["furtos"], errors="coerce")

        # Evita que meses placeholder com zero puxem o período para dezembro.
        df_ref = df_ref[df_ref["furtos"] > 0]

        if not df_ref.empty:
            ult_ano_ref_furtos = int(df_ref["ano"].max())
            ult_mes_ref_furtos = int(
                df_ref[df_ref["ano"] == ult_ano_ref_furtos]["mes"].max()
            )

    display_furtos_por_tipo(
        df_seguranca_furtos,
        "furtos_expander_state",
        furtos_callback,
        ult_ano_referencia=ult_ano_ref_furtos,
        ult_mes_referencia=ult_mes_ref_furtos,
    )
