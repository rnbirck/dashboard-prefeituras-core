import pandas as pd
import streamlit as st

from dashboard_core.utils import (
    MESES_DIC,
    criar_grafico_barras,
    checar_ult_ano_completo,
    titulo_centralizado,
    style_saldo_variacao,  # Adicionado para estilizar a tabela
)

CORES_MUNICIPIOS = {}
ANOS_DE_INTERESSE = []
municipio_de_interesse = None  # Variável global para o município foco


def set_saude_config(municipio, cores_municipios, anos_de_interesse):
    """
    Configura valores específicos do município que antes eram importados
    do dashboard_core.config. Deve ser chamado pelo app.py antes de
    renderizar a página de saude.
    """
    global CORES_MUNICIPIOS, ANOS_DE_INTERESSE, municipio_de_interesse
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}
    ANOS_DE_INTERESSE = anos_de_interesse or []


# --- FUNÇÕES AUXILIARES DE FORMATAÇÃO ---
def formatar_valor_br(x):
    """Formata número float para padrão BR (1.000.000) sem decimais."""
    if pd.isna(x):
        return "-"
    return f"{x:,.0f}".replace(",", ".")


def formatar_pct_br(x):
    """Formata número float para percentual BR (+1,2%) com 1 casa decimal."""
    if pd.isna(x):
        return "-"
    return f"{x:+,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")


# --- FUNÇÕES DE CALLBACK ---


def set_expander_open(key):
    """Define o estado de um expander específico como True (aberto)."""
    st.session_state[key] = True


# Callbacks para Indicadores Mensais
def obitos_callback():
    set_expander_open("obitos_expander_state")


def nascimentos_callback():
    set_expander_open("nascimentos_expander_state")


def gestantes_callback():
    set_expander_open("gestantes_expander_state")


def atencao_basica_mensal_callback():
    set_expander_open("atencao_basica_mensal_expander_state")


def acidente_trabalho_callback():
    set_expander_open("acidente_trabalho_expander_state")


# Callbacks para Indicadores Anuais
def despesas_callback():
    set_expander_open("despesas_expander_state")


def vacinas_callback():
    set_expander_open("vacinas_expander_state")


def medicos_callback():
    set_expander_open("medicos_expander_state")


def leitos_callback():
    set_expander_open("leitos_expander_state")


def obitos_causa_basica_callback():
    set_expander_open("obitos_causa_basica_expander_state")


def preparar_dados_graficos_saude_mensal(
    df_filtrado, coluna_selecionada, metodo_agg="sum", anos_visualizacao=None
):
    """
    Prepara os DataFrames para os gráficos, usando o método de agregação correto.
    'sum' para números absolutos, 'mean' para taxas/proporções.
    Retorna também DataFrames de variação.
    """
    df_hist = pd.DataFrame()
    df_acum, df_acum_var = pd.DataFrame(), pd.DataFrame()
    df_anual, df_anual_var = pd.DataFrame(), pd.DataFrame()
    ult_ano, ult_mes = None, None

    if not df_filtrado.empty:
        # Filtra apenas registros onde a coluna selecionada tem dados válidos (não nulo)
        df_com_dados = df_filtrado[df_filtrado[coluna_selecionada].notna()].copy()

        if df_com_dados.empty:
            return (
                df_hist,
                df_acum,
                df_acum_var,
                df_anual,
                df_anual_var,
                ult_ano,
                ult_mes,
            )

        # Se anos_visualizacao for fornecido, usa para determinar o último ano
        if anos_visualizacao:
            df_range_visualizacao = df_com_dados[
                df_com_dados["ano"].isin(anos_visualizacao)
            ]
            if df_range_visualizacao.empty:
                ult_ano = df_com_dados["ano"].max()
            else:
                ult_ano = df_range_visualizacao["ano"].max()
        else:
            ult_ano = df_com_dados["ano"].max()

        ult_mes = df_com_dados[df_com_dados["ano"] == ult_ano]["mes"].max()

        # Evolução Mensal
        df_hist_full = (
            df_com_dados.assign(
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
                values=coluna_selecionada,
                aggfunc="sum",
            )
            .dropna(how="all")  # Remove datas onde todos os municípios têm NaN
            .sort_index()
        )

        # Filtra Evolução por anos de interesse
        if anos_visualizacao:
            df_hist = df_hist_full[df_hist_full.index.year.isin(anos_visualizacao)]
        else:
            df_hist = df_hist_full

        # Lógica de Agregação para Acumulado e Anual
        agg_func = "mean" if metodo_agg == "mean" else "sum"
        is_taxa = metodo_agg == "mean"  # Se for mean, é taxa/proporção

        # Acumulado no Ano
        df_acum_temp = df_com_dados[df_com_dados["mes"] <= ult_mes]
        df_acum_full = (
            df_acum_temp.pivot_table(
                index="ano",
                columns="municipio",
                values=coluna_selecionada,
                aggfunc=agg_func,
            )
            .dropna(how="all")
            .sort_index()
        )  # Remove anos sem dados

        # Calcula variação (diferença para taxas, percentual para valores absolutos)
        if is_taxa:
            df_acum_var_full = df_acum_full.diff()
        else:
            df_acum_var_full = df_acum_full.pct_change() * 100

        # Aplica filtro de anos apenas aos valores absolutos
        if anos_visualizacao:
            df_acum = df_acum_full[df_acum_full.index.isin(anos_visualizacao)]
        else:
            df_acum = df_acum_full
        df_acum_var = df_acum_var_full  # Variação mantém todos os anos

        # Anual
        ano_completo = checar_ult_ano_completo(df_com_dados)
        df_anual_temp = df_com_dados[df_com_dados["ano"] <= ano_completo]
        df_anual_full = (
            df_anual_temp.pivot_table(
                index="ano",
                columns="municipio",
                values=coluna_selecionada,
                aggfunc=agg_func,
            )
            .dropna(how="all")
            .sort_index()
        )  # Remove anos sem dados

        # Calcula variação
        if is_taxa:
            df_anual_var_full = df_anual_full.diff()
        else:
            df_anual_var_full = df_anual_full.pct_change() * 100

        # Aplica filtro de anos apenas aos valores absolutos
        if anos_visualizacao:
            df_anual = df_anual_full[
                df_anual_full.index.isin(anos_visualizacao)
            ].sort_index(ascending=False)
        else:
            df_anual = df_anual_full.sort_index(ascending=False)
        df_anual_var = df_anual_var_full  # Variação mantém todos os anos

    return df_hist, df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes


# --- PREPARAÇÃO DE DADOS PARA TABELA DE ÓBITOS ---
@st.cache_data
def preparar_dados_obitos_tipo_tabela(df, municipio, anos_interesse=None):
    """
    Prepara a tabela dinâmica de óbitos por tipo para o município selecionado.
    Retorna DF de Valores e DF de Variação Percentual.
    """
    if df.empty or not municipio:
        return pd.DataFrame(), pd.DataFrame()

    df_filt = df[df["municipio"] == municipio].copy()

    if df_filt.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Verifica se as colunas necessárias existem
    colunas_necessarias = [
        "causa_basica",
        "descricao_subcategoria",
        "ano",
        "num_obitos",
    ]
    if not all(col in df_filt.columns for col in colunas_necessarias):
        return pd.DataFrame(), pd.DataFrame()

    # Cria coluna combinada Causa + Descrição para facilitar leitura
    df_filt["causa_completa"] = (
        df_filt["causa_basica"] + " - " + df_filt["descricao_subcategoria"]
    )
    pivot_val = df_filt.pivot_table(
        index="causa_completa",
        columns="ano",
        values="num_obitos",
        aggfunc="sum",
        fill_value=0,
    )

    # Ordena pelo último ano disponível com dados
    if not pivot_val.empty:
        ult_ano = pivot_val.columns.max()
        pivot_val = pivot_val.sort_values(by=ult_ano, ascending=False)

    # Calcula Variação Percentual (Ano X vs Ano X-1)
    # pct_change faz (atual - anterior) / anterior
    pivot_pct = pivot_val.pct_change(axis=1) * 100

    # Filtra pelos anos de interesse
    if anos_interesse:
        colunas_interesse = [c for c in pivot_val.columns if c in anos_interesse]
        pivot_val = pivot_val[colunas_interesse]
        pivot_pct = pivot_pct[colunas_interesse]

    # Renomeia o índice para "Causa Básica"
    pivot_val.index.name = "Causa Básica"
    pivot_pct.index.name = "Causa Básica"

    return pivot_val, pivot_pct


def preparar_dados_graficos_saude_anual(
    df_filtrado, coluna_selecionada, is_percentual=False, anos_visualizacao=None
):
    """
    Prepara os DataFrames para os gráficos anuais.
    Retorna também DataFrame de variação.
    """
    df_anual_full = (
        df_filtrado.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_selecionada,
            aggfunc="sum",
        )
        .dropna(how="all")
        .sort_index()
    )  # Remove anos sem dados

    # Calcula variação
    if is_percentual:
        df_anual_var = df_anual_full.diff()
    else:
        df_anual_var = df_anual_full.pct_change() * 100

    # Aplica filtro de anos apenas aos valores absolutos
    if anos_visualizacao:
        df_anual = df_anual_full[
            df_anual_full.index.isin(anos_visualizacao)
        ].sort_index(ascending=False)
    else:
        df_anual = df_anual_full.sort_index(ascending=False)

    return df_anual, df_anual_var


def display_obitos_causa_basica_expander(
    df_obitos_tipo,
    expander_state_key,
    callback_func,
):
    """Função dedicada para exibir o detalhamento de óbitos por causa básica."""
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(
        "Detalhamento de Óbitos por Causa Básica",
        expanded=st.session_state[expander_state_key],
    ):
        if df_obitos_tipo is None or df_obitos_tipo.empty:
            st.warning("Dados detalhados de óbitos não disponíveis.")
            return

        titulo_centralizado(f"Detalhamento de Óbitos - {municipio_de_interesse}", 5)

        # Preparação dos dados da tabela
        df_val, df_pct = preparar_dados_obitos_tipo_tabela(
            df_obitos_tipo, municipio_de_interesse, anos_interesse=ANOS_DE_INTERESSE
        )

        if df_val.empty:
            st.info(
                f"Não há registros detalhados de óbitos para {municipio_de_interesse}."
            )
            return

        # Controles da Tabela
        col_busca, col_metric = st.columns([0.6, 0.4])
        with col_busca:
            texto_busca = st.text_input(
                "🔍 Pesquisar Causa:",
                placeholder="Ex: Neoplasia, Hipertensão",
                key="obitos_causa_basica_busca",
            )
        with col_metric:
            modo_metrica = st.segmented_control(
                "Métrica:",
                options=["Nᵒ Óbitos", "Variação (%)"],
                selection_mode="single",
                default="Nᵒ Óbitos",
                key="obitos_causa_basica_metrica",
            )
            if not modo_metrica:
                modo_metrica = "Nᵒ Óbitos"

        # Filtragem por busca
        if texto_busca:
            mask = df_val.index.str.contains(texto_busca, case=False, na=False)
            df_val = df_val[mask]
            df_pct = df_pct[mask]

        # Seleção do DataFrame para exibição
        if modo_metrica == "Nᵒ Óbitos":
            df_show = df_val
            formatter = formatar_valor_br
            cmap = "Blues"
            style_func = None
        else:
            df_show = df_pct
            formatter = formatar_pct_br
            cmap = None
            style_func = style_saldo_variacao

        # Renderização da Tabela
        if not df_show.empty:
            # Converte colunas (anos) para string para exibição limpa
            df_show.columns = [str(c) for c in df_show.columns]

            styler = df_show.style.format(formatter)

            if cmap:
                styler = styler.background_gradient(cmap=cmap, axis=0)
            if style_func:
                styler = styler.map(style_func)

            st.dataframe(styler, height=400, use_container_width=True)
        else:
            st.warning("Nenhum registro encontrado para a busca.")


def display_saude_expander(
    df_filtrado,
    titulo_expander,
    dicionario_indicadores,
    key_prefix,
    expander_state_key,
    callback_func,
):
    """Função genérica para exibir uma seção de indicadores de saúde."""
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(titulo_expander, expanded=st.session_state[expander_state_key]):
        indicador_selecionado = st.selectbox(
            "Selecione um indicador para visualizar:",
            options=list(dicionario_indicadores.keys()),
            key=f"{key_prefix}_selectbox",
            on_change=callback_func,
        )

        # --- LÓGICA PADRÃO PARA GRÁFICOS ---
        coluna_selecionada, agg_method, label_y, data_format = dicionario_indicadores[
            indicador_selecionado
        ]

        # Verifica se é taxa/proporção para definir tipo de variação
        is_taxa = agg_method == "mean"
        label_var = "Variação (p.p.)" if is_taxa else "Variação (%)"
        fmt_var = "+,.2f" if is_taxa else "+,.1f"

        hover_format = (
            f",.{int(data_format.split('.')[-1][0]) + 1}f"
            if "." in data_format
            else ",.0f"
        )

        df_hist, df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes = (
            preparar_dados_graficos_saude_mensal(
                df_filtrado,
                coluna_selecionada,
                agg_method,
                anos_visualizacao=ANOS_DE_INTERESSE,
            )
        )

        anos_disponiveis = sorted(df_filtrado["ano"].unique().tolist(), reverse=True)

        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
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

        # --- ABA 1: Evolução MENSAL ---
        if aba_selecionada == "Evolução Mensal":
            if not anos_disponiveis:
                st.warning("Nenhum dado disponível para os filtros selecionados.")
            else:
                ANO_SELECIONADO = st.selectbox(
                    "Selecione o ano para o gráfico:",
                    options=anos_disponiveis,
                    index=0,
                    key=f"{key_prefix}_hist_ano",
                    on_change=callback_func,
                )
                titulo_centralizado(
                    f"{indicador_selecionado} - Evolução Mensal em {ANO_SELECIONADO}",
                    5,
                )

                df_hist_ano = df_hist[df_hist.index.year == ANO_SELECIONADO]
                if not df_hist_ano.empty:
                    df_hist_ano.index = [
                        f"{MESES_DIC[date.month][:3]}/{str(date.year)[2:]}"
                        for date in df_hist_ano.index
                    ]

                    fig = criar_grafico_barras(
                        df=df_hist_ano,
                        titulo="",
                        label_y=label_y,
                        barmode="group",
                        height=400,
                        data_label_format=data_format,
                        hover_label_format=hover_format,
                        color_map=CORES_MUNICIPIOS,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"Sem dados mensais para {ANO_SELECIONADO}.")

        # --- ABA 2: ACUMULADO NO ANO ---
        elif aba_selecionada == "Acumulado no Ano":
            if ult_mes:
                # Seletor de modo
                key_acum = f"acum_mode_{key_prefix}"
                if key_acum not in st.session_state:
                    st.session_state[key_acum] = label_y

                modo_acum = st.segmented_control(
                    "Visualizar:",
                    options=[label_y, label_var],
                    key=key_acum,
                    selection_mode="single",
                    on_change=callback_func,
                )

                if not modo_acum:
                    modo_acum = label_y

                periodo_txt = f"Jan a {MESES_DIC[ult_mes][:3]}"

                if modo_acum == label_var:
                    titulo_centralizado(
                        f"{indicador_selecionado} - {label_var} - {periodo_txt}", 5
                    )
                    df_var_plot = df_acum_var.copy().sort_index(ascending=True)

                    # Remove anos com variação nula
                    df_var_plot = df_var_plot.dropna(how="all")

                    df_var_plot.index = (
                        "Jan-"
                        + MESES_DIC[ult_mes][:3]
                        + "/"
                        + df_var_plot.index.astype(str).str.slice(-2)
                    )

                    fig = criar_grafico_barras(
                        df=df_var_plot,
                        titulo="",
                        label_y=label_var,
                        barmode="group",
                        height=400,
                        data_label_format=fmt_var,
                        hover_label_format=fmt_var,
                        color_map=CORES_MUNICIPIOS,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    df_plot = df_acum.copy()
                    df_plot.index = (
                        "Jan-"
                        + MESES_DIC[ult_mes][:3]
                        + "/"
                        + df_plot.index.astype(str).str.slice(-2)
                    )
                    titulo_centralizado(
                        f"{indicador_selecionado} - {periodo_txt}",
                        5,
                    )
                    fig = criar_grafico_barras(
                        df=df_plot,
                        titulo="",
                        label_y=label_y,
                        barmode="group",
                        height=400,
                        data_label_format=data_format,
                        hover_label_format=hover_format,
                        color_map=CORES_MUNICIPIOS,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Dados acumulados não disponíveis.")

        # --- ABA 3: ANUAL ---
        elif aba_selecionada == "Anual":
            # Seletor de modo
            key_anual = f"anual_mode_{key_prefix}"
            if key_anual not in st.session_state:
                st.session_state[key_anual] = label_y

            modo_anual = st.segmented_control(
                "Visualizar:",
                options=[label_y, label_var],
                key=key_anual,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_anual:
                modo_anual = label_y

            if modo_anual == label_var:
                titulo_centralizado(f"{indicador_selecionado} - {label_var} Anual", 5)
                df_var_plot = df_anual_var.copy()

                # Remove anos com variação nula
                df_var_plot = df_var_plot.dropna(how="all")

                df_var_plot = df_var_plot.sort_index(ascending=True)
                df_var_plot.index = df_var_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y=label_var,
                    barmode="group",
                    height=400,
                    data_label_format=fmt_var,
                    hover_label_format=fmt_var,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                titulo_centralizado(f"{indicador_selecionado} - Análise Anual", 5)
                fig = criar_grafico_barras(
                    df=df_anual,
                    titulo="",
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=data_format,
                    hover_label_format=hover_format,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)


def display_saude_anual_expander(
    df_filtrado,
    titulo_expander,
    dicionario_indicadores,
    key_prefix,
    expander_state_key,
    callback_func,
):
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(titulo_expander, expanded=st.session_state[expander_state_key]):
        indicador_selecionado = st.selectbox(
            "Selecione um indicador para visualizar:",
            options=list(dicionario_indicadores.keys()),
            key=f"{key_prefix}_selectbox",
            on_change=callback_func,
        )

        coluna_selecionada, label_y, data_format = dicionario_indicadores[
            indicador_selecionado
        ]

        # Verifica se é percentual/cobertura para definir tipo de variação
        is_percentual = (
            "(%)" in indicador_selecionado
            or "Cobertura" in indicador_selecionado
            or "Percentual" in indicador_selecionado
        )
        label_var = "Variação (p.p.)" if is_percentual else "Variação (%)"
        fmt_var = "+,.2f" if is_percentual else "+,.1f"

        hover_format = (
            f",.{int(data_format.split('.')[-1][0]) + 1}f"
            if "." in data_format
            else ",.0f"
        )

        df_anual, df_anual_var = preparar_dados_graficos_saude_anual(
            df_filtrado=df_filtrado,
            coluna_selecionada=coluna_selecionada,
            is_percentual=is_percentual,
            anos_visualizacao=ANOS_DE_INTERESSE,
        )

        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = f"main_tab_nav_{key_prefix}"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = label_y

        aba_selecionada = st.pills(
            "Selecione a visualização:",
            options=[label_y, label_var],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = label_y

        if aba_selecionada == label_var:
            titulo_centralizado(f"{indicador_selecionado} - {label_var}", 5)
            df_var_plot = df_anual_var.copy()

            # Remove anos com variação nula
            df_var_plot = df_var_plot.dropna(how="all")

            df_var_plot = df_var_plot.sort_index(ascending=True)
            df_var_plot.index = df_var_plot.index.astype(str)

            fig = criar_grafico_barras(
                df=df_var_plot,
                titulo="",
                label_y=label_var,
                barmode="group",
                height=400,
                data_label_format=fmt_var,
                hover_label_format=fmt_var,
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            titulo_centralizado(f"{indicador_selecionado}", 5)
            fig = criar_grafico_barras(
                df=df_anual,
                titulo="",
                label_y=label_y,
                barmode="group",
                height=400,
                data_label_format=data_format,
                hover_label_format=hover_format,
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig, use_container_width=True)


# ==============================================================================
# FUNÇÃO PRINCIPAL DA PÁGINA
# ==============================================================================


def show_page_saude(
    df_saude_mensal,
    df_saude_vacinas,
    df_saude_despesas,
    df_saude_leitos,
    df_saude_medicos,
    df_obitos_tipo=None,
):
    # 1. Inicialização dos estados dos expanders
    if "obitos_expander_state" not in st.session_state:
        st.session_state.obitos_expander_state = False
    if "nascimentos_expander_state" not in st.session_state:
        st.session_state.nascimentos_expander_state = False
    if "gestantes_expander_state" not in st.session_state:
        st.session_state.gestantes_expander_state = False
    if "atencao_basica_mensal_expander_state" not in st.session_state:
        st.session_state.atencao_basica_mensal_expander_state = False
    if "acidente_trabalho_expander_state" not in st.session_state:
        st.session_state.acidente_trabalho_expander_state = False
    if "despesas_expander_state" not in st.session_state:
        st.session_state.despesas_expander_state = False
    if "vacinas_expander_state" not in st.session_state:
        st.session_state.vacinas_expander_state = False
    if "medicos_expander_state" not in st.session_state:
        st.session_state.medicos_expander_state = False
    if "leitos_expander_state" not in st.session_state:
        st.session_state.leitos_expander_state = False
    if "obitos_causa_basica_expander_state" not in st.session_state:
        st.session_state.obitos_causa_basica_expander_state = False

    titulo_centralizado("Dashboard de Saúde", 1)
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

    INDICADORES_OBITOS = {
        "Óbitos com Causas Definidas": (
            "obitos_causa_definida",
            "sum",
            "Nº de Óbitos",
            ",.0f",
        ),
        "Óbitos com Causas Não Definidas": (
            "obitos_causa_nao_definida",
            "sum",
            "Nº de Óbitos",
            ",.0f",
        ),
        "Proporção de Óbitos com Causas Definidas (%)": (
            "prop_obitos_causas_definidas",
            "mean",
            "Proporção (%)",
            ".1f",
        ),
        "Proporção de Óbitos com Causas Não Definidas (%)": (
            "prop_obitos_causa_nao_definida",
            "mean",
            "Proporção (%)",
            ".1f",
        ),
    }

    INDICADORES_NASCIMENTOS = {
        "Nascidos Vivos": ("nascimentos", "sum", "Nº de Nascidos", ",.0f"),
        "Nascidos por Mil Habitantes": (
            "nascimentos/1000_hab",
            "sum",
            "Nascidos por mil hab.",
            ".2f",
        ),
        "Mortalidade Infantil": (
            "taxa_obitos_infantis",
            "mean",
            "Taxa de Mort. Infantil por mil nasc.",
            ".1f",
        ),
        "Proporção de Nascidos Vivos com Baixo Peso ao Nascer (%)": (
            "prop_nasc_baixo_peso",
            "mean",
            "Prop. de Nascidos Vivos (%)",
            ".1f",
        ),
        "Proporção de Nascidos Vivos com Sete ou Mais Consultas de Pré-Natal (%)": (
            "prop_consultas_pre_natal",
            "mean",
            "Prop. de Nascidos Vivos (%)",
            ".1f",
        ),
    }

    INDICADORES_GESTANTES = {
        "Proporção de Gravidez na Adolescência entre as Faixas Etárias 10 a 19 anos (%)": (
            "prop_nasc_adolesc",
            "mean",
            "Prop. de Gravidez (%)",
            ".1f",
        ),
        "Coeficiente de Mortalidade Neonatal (por mil nascidos vivos)": (
            "coef_neonatal",
            "mean",
            "Coeficiente por mil nascidos vivos",
            ".1f",
        ),
    }
    INDICADORES_ATENCAO_BASICA_MENSAL = {
        "Internações Totais": (
            "internacoes_totais",
            "sum",
            "Núm. de Internações",
            ",.0f",
        ),
        "Internações por Condições Sensíveis à Atenção Básica - ICSAB": (
            "internacoes_icsab",
            "sum",
            "Núm. de Internações",
            ",.0f",
        ),
        "Proporção das Internações por Condições Sensíveis à Atenção Básica - ICSAB (%)": (
            "prop_icsab",
            "mean",
            "Prop. de Internações (%)",
            ".1f",
        ),
    }
    INDICADORES_ACIDENTE_DE_TRABALHO = {
        "Notificações Totais": (
            "notificacoes_acidentes_trab",
            "sum",
            "Núm. de Notificações",
            ",.0f",
        ),
        "Taxa de Acidentes e Doenças Relacionadas ao Trabalho por 10 mil Habitantes": (
            "taxa_acidentes_trab",
            "mean",
            "Taxa por 10 mil Hab.",
            ".2f",
        ),
    }

    INDICADORES_DESPESAS = {
        "Despesa Total com Saúde em milhões (R$) - Valores Reais": (
            "despesa_saude_deflacionada",
            "Despesa",
            ",.0f",
        ),
        "Despesa Per Capita com Saúde - Valores Reais": (
            "despesa_per_capita_deflacionada",
            "Despesa per capita",
            ",.0f",
        ),
        "Percentual das Despesas em Saúde sobre a Arrecadação Municipal (%)": (
            "percental_gastos_saude",
            "Percentual",
            ",.2f",
        ),
    }

    INDICADORES_VACINAS = {
        "Número de Doses Aplicadas": (
            "doses_total",
            "Núm. de Doses",
            ",.0f",
        ),
        "Cobertura vacinal da Pentavalente (DTP+HB+Hib) (Penta) (%)": (
            "cobertura_penta",
            "Cobertura (%)",
            ",.1f",
        ),
        "Cobertura vacinal contra Meningococo (%)": (
            "cobertura_meningococo",
            "Cobertura (%)",
            ",.1f",
        ),
        "Cobertura vacinal contra Poliomielite (%)": (
            "cobertura_poliomielite",
            "Cobertura (%)",
            ",.1f",
        ),
        "Cobertura vacinal da 1ª dose da Tríplice Viral (SCR) (%)": (
            "cobertura_triplice_viral_d1",
            "Cobertura (%)",
            ",.1f",
        ),
    }

    INDICADORES_MEDICOS = {
        "Número de Médicos que atendem pelo SUS": (
            "qtd_medicos_sus",
            "Núm. de Médicos",
            ",.0f",
        ),
        "Número de Médicos que atendem pelo SUS por mil habitantes": (
            "qtd_medicos_sus_mil_hab",
            "Núm. de Médicos por mil hab.",
            ",.2f",
        ),
    }

    INDICADORES_LEITOS = {
        "Número de Leitos de Internação e Complementares disponíveis pelo SUS": (
            "qtd_leitos_sus",
            "Núm. de Leitos",
            ",.0f",
        ),
        "Número de Leitos disponíveis pelo SUS por mil habitantes": (
            "qtd_leitos_sus_mil_hab",
            "Núm. de Leitos por mil hab.",
            ",.2f",
        ),
    }

    # --- CHAMADAS PARA OS EXPANDERS ---

    st.markdown("###### Indicadores Mensais de Saúde")

    display_saude_expander(
        df_filtrado=df_saude_mensal,
        titulo_expander="Indicadores de Óbitos",
        dicionario_indicadores=INDICADORES_OBITOS,
        key_prefix="obitos",
        expander_state_key="obitos_expander_state",
        callback_func=obitos_callback,
    )

    display_saude_expander(
        df_filtrado=df_saude_mensal,
        titulo_expander="Indicadores de Nascimentos",
        dicionario_indicadores=INDICADORES_NASCIMENTOS,
        key_prefix="nascimentos",
        expander_state_key="nascimentos_expander_state",
        callback_func=nascimentos_callback,
    )

    display_saude_expander(
        df_filtrado=df_saude_mensal,
        titulo_expander="Indicadores de Gestantes",
        dicionario_indicadores=INDICADORES_GESTANTES,
        key_prefix="gestantes",
        expander_state_key="gestantes_expander_state",
        callback_func=gestantes_callback,
    )

    display_saude_expander(
        df_filtrado=df_saude_mensal,
        titulo_expander="Atenção Básica",
        dicionario_indicadores=INDICADORES_ATENCAO_BASICA_MENSAL,
        key_prefix="atencao_basica_mensal",
        expander_state_key="atencao_basica_mensal_expander_state",
        callback_func=atencao_basica_mensal_callback,
    )

    display_saude_expander(
        df_filtrado=df_saude_mensal,
        titulo_expander="Acidentes e Doenças Relacionadas ao Trabalho",
        dicionario_indicadores=INDICADORES_ACIDENTE_DE_TRABALHO,
        key_prefix="acidente_trabalho",
        expander_state_key="acidente_trabalho_expander_state",
        callback_func=acidente_trabalho_callback,
    )

    st.markdown("###### Indicadores Anuais de Saúde")

    display_obitos_causa_basica_expander(
        df_obitos_tipo=df_obitos_tipo,
        expander_state_key="obitos_causa_basica_expander_state",
        callback_func=obitos_causa_basica_callback,
    )

    display_saude_anual_expander(
        df_filtrado=df_saude_despesas,
        titulo_expander="Despesas com Saúde",
        dicionario_indicadores=INDICADORES_DESPESAS,
        key_prefix="despesas",
        expander_state_key="despesas_expander_state",
        callback_func=despesas_callback,
    )

    display_saude_anual_expander(
        df_filtrado=df_saude_vacinas,
        titulo_expander="Imunização",
        dicionario_indicadores=INDICADORES_VACINAS,
        key_prefix="vacinas",
        expander_state_key="vacinas_expander_state",
        callback_func=vacinas_callback,
    )

    display_saude_anual_expander(
        df_filtrado=df_saude_medicos,
        titulo_expander="Médicos no SUS",
        dicionario_indicadores=INDICADORES_MEDICOS,
        key_prefix="medicos",
        expander_state_key="medicos_expander_state",
        callback_func=medicos_callback,
    )

    display_saude_anual_expander(
        df_filtrado=df_saude_leitos,
        titulo_expander="Leitos de Internação e Complementares no SUS",
        dicionario_indicadores=INDICADORES_LEITOS,
        key_prefix="leitos",
        expander_state_key="leitos_expander_state",
        callback_func=leitos_callback,
    )
