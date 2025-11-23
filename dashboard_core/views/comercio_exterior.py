import streamlit as st
import pandas as pd

# ==============================================================================
# IMPORTAÇÕES DE FUNÇÕES E DADOS
# ==============================================================================

from dashboard_core.utils import (
    MESES_DIC,
    checar_ult_ano_completo,
    filtrar_municipio_ult_mes_ano,
    criar_grafico_barras,
    titulo_centralizado,
    style_saldo_variacao,
)

municipio_de_interesse = None
CORES_MUNICIPIOS = {}
anos_de_interesse = []


def set_comercio_exterior_config(municipio, cores_municipios, anos_interesse):
    global municipio_de_interesse, CORES_MUNICIPIOS, anos_de_interesse
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}
    anos_de_interesse = anos_interesse or []


# --- FUNÇÕES DE CALLBACK ---
def set_comex_municipios_open():
    st.session_state.comex_municipios_expander = True


def set_comex_produto_pais_open():
    st.session_state.comex_produto_pais_expander = True


# --- FORMATADORES ---
def formatar_valor_br(x):
    """Formata número float para padrão BR (1.000.000) sem decimais para valores altos."""
    if pd.isna(x):
        return "-"
    return f"{x:,.0f}".replace(",", ".")


def formatar_pct_br(x):
    """Formata número float para percentual BR (+1.234,5%) com 1 casa decimal."""
    if pd.isna(x):
        return "-"
    # Formata como +1,234.5% e depois inverte pontuação
    return f"{x:+,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")


# ==============================================================================
# FUNÇÕES DA PÁGINA DE COMÉRCIO EXTERIOR
# ==============================================================================


def display_comex_kpi_cards(df_ano, df_mes, municipio_interesse):
    titulo_centralizado(f"Exportações de {municipio_de_interesse} (Milhões de US$)", 3)
    with st.container(border=False):
        # Ultimo mês disponível
        ult_ano = df_mes["ano"].max()
        ult_mes = df_mes[df_mes["ano"] == ult_ano]["mes"].max()

        df_kpi_mes = filtrar_municipio_ult_mes_ano(df_mes, municipio_interesse)

        exp_mun_ult_mes = df_kpi_mes["total_exp_mensal"].sum()
        taxa_var_ult_mes = df_kpi_mes["perc_var_mes_ano_anterior"].sum()
        exp_mun_acu_ano = df_kpi_mes["total_exp_acumulado"].sum()
        taxa_var_acu_ano = df_kpi_mes["perc_var_acum_ano_anterior"].sum()

        # Último ano completo
        ano_completo = checar_ult_ano_completo(df_mes)
        df_ano_filtrado = df_ano[
            (df_ano["municipio"] == municipio_interesse)
            & (df_ano["ano"] == ano_completo)
        ]

        exp_mun_ano_completo = df_ano_filtrado["total_exp_anual"].sum()
        tx_var_ano_completo = df_ano_filtrado["perc_var_ano_anterior"].sum()

        col1, col2, col3 = st.columns(3)

        col1.metric(
            label=f"{MESES_DIC[ult_mes]} de {ult_ano}",
            value=f"{exp_mun_ult_mes / 1000000:,.1f}".replace(".", ","),
            delta=f"{taxa_var_ult_mes}%".replace(".", ","),
            help="Taxa de Variação percentual em relação ao mesmo mês do ano anterior",
            border=True,
        )
        col2.metric(
            label=f"Acumulado de Jan a {MESES_DIC[ult_mes][:3]} de {ult_ano}",
            value=f"{exp_mun_acu_ano / 1000000:,.1f}".replace(".", ","),
            delta=f"{taxa_var_acu_ano}%".replace(".", ","),
            help="Taxa de Variação percentual em relação ao mesmo período do ano anterior",
            border=True,
        )

        col3.metric(
            label=f"Exportação em {ano_completo}",
            value=f"{exp_mun_ano_completo / 1000000:,.1f}".replace(".", ","),
            delta=f"{tx_var_ano_completo}%".replace(".", ","),
            help="Taxa de Variação percentual em relação ao ano anterior",
            border=True,
        )


@st.cache_data
def preparar_dados_grafico_comex(df_mensal, df_anual, anos_de_interesse):
    """
    Recebe os DataFrames MENSAL e ANUAL filtrados e retorna os pivots.
    """
    if df_mensal.empty:
        return tuple([pd.DataFrame()] * 8) + (None, None)

    # Pré-processamento MENSAL
    ult_ano = df_mensal["ano"].max()
    ult_mes = df_mensal[df_mensal["ano"] == ult_ano]["mes"].max()

    df_proc_mensal = df_mensal.assign(
        date=lambda x: pd.to_datetime(dict(year=x.ano, month=x.mes, day=1)),
        exp_milhoes=lambda x: x["total_exp_mensal"] / 1_000_000,
        exp_acum_milhoes=lambda x: x["total_exp_acumulado"] / 1_000_000,
    )

    # --- 1. Histórico Mensal (Evolução) ---
    pivot_hist = df_proc_mensal.pivot_table(
        index="date",
        columns="municipio",
        values=["exp_milhoes", "perc_var_mes_ano_anterior"],
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    df_comex_hist = pivot_hist["exp_milhoes"].apply(lambda x: x.round(2))
    df_comex_hist_perc = pivot_hist["perc_var_mes_ano_anterior"].apply(
        lambda x: x.round(2)
    )

    # --- 2. Mês Atual (Comparativo) ---
    df_mes_atual = df_proc_mensal[df_proc_mensal["mes"] == ult_mes]
    pivot_mes = df_mes_atual.pivot_table(
        index="ano",
        columns="municipio",
        values=["exp_milhoes", "perc_var_mes_ano_anterior"],
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    df_comex_mes = pivot_mes["exp_milhoes"]
    df_comex_mes_perc = pivot_mes["perc_var_mes_ano_anterior"]

    # --- 3. Acumulado no Ano ---
    df_acum_correto = df_proc_mensal[df_proc_mensal["mes"] == ult_mes]

    pivot_acum = df_acum_correto.pivot_table(
        index="ano",
        columns="municipio",
        values=["exp_acum_milhoes", "perc_var_acum_ano_anterior"],
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    df_comex_acum = pivot_acum["exp_acum_milhoes"]
    df_comex_acum_perc = pivot_acum["perc_var_acum_ano_anterior"]

    # --- 4. Anual ---
    ano_completo = checar_ult_ano_completo(df_mensal)

    if not df_anual.empty:
        df_ano_proc = df_anual[
            (df_anual["ano"].isin(anos_de_interesse))
            & (df_anual["ano"] <= ano_completo)
        ].assign(exp_milhoes=lambda x: x["total_exp_anual"] / 1_000_000)

        pivot_ano = df_ano_proc.pivot_table(
            index="ano",
            columns="municipio",
            values=["exp_milhoes", "perc_var_ano_anterior"],
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        df_comex_ano = pivot_ano["exp_milhoes"]
        df_comex_ano_perc = pivot_ano["perc_var_ano_anterior"]
    else:
        df_comex_ano = pd.DataFrame()
        df_comex_ano_perc = pd.DataFrame()

    return (
        df_comex_hist,
        df_comex_hist_perc,
        df_comex_mes,
        df_comex_mes_perc,
        df_comex_acum,
        df_comex_acum_perc,
        df_comex_ano,
        df_comex_ano_perc,
        ult_ano,
        ult_mes,
    )


def display_comex_municipios_expander(df_mes, df_ano):
    """Exibe o expander com análise de exportações para múltiplos municípios."""

    if "comex_municipios_expander" not in st.session_state:
        st.session_state.comex_municipios_expander = False

    with st.expander(
        "Comércio Exterior por Município",
        expanded=st.session_state.comex_municipios_expander,
    ):
        df_mes_filtrado = df_mes[(df_mes["ano"].isin(anos_de_interesse))]

        (
            df_comex_hist,
            df_comex_hist_perc,
            df_comex_mes,
            df_comex_mes_perc,
            df_comex_acum,
            df_comex_acum_perc,
            df_comex_ano,
            df_comex_ano_perc,
            ult_ano_comex,
            ult_mes_comex,
        ) = preparar_dados_grafico_comex(df_mes_filtrado, df_ano, anos_de_interesse)

        anos_disponiveis = sorted(
            df_mes_filtrado["ano"].unique().tolist(), reverse=True
        )

        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab_comex = "main_tab_nav_comex_municipios"
        if key_main_tab_comex not in st.session_state:
            st.session_state[key_main_tab_comex] = "Evolução Mensal"

        aba_selecionada_comex = st.pills(
            "Selecione o tipo de análise temporal:",
            options=["Evolução Mensal", "Mês", "Acumulado no Ano", "Anual"],
            selection_mode="single",
            key=key_main_tab_comex,
        )

        if not aba_selecionada_comex:
            aba_selecionada_comex = "Evolução Mensal"

        # --- ABA 1: EVOLUÇÃO MENSAL ---
        if aba_selecionada_comex == "Evolução Mensal":
            col1, col2 = st.columns([0.5, 0.5])
            with col1:
                ANO_SELECIONADO = st.selectbox(
                    "Selecione o ano:",
                    options=anos_disponiveis,
                    index=0,
                    key="hist_ano_comex",
                    on_change=set_comex_municipios_open,
                )
            with col2:
                # Inicialização Segura
                if "metric_mode_comex_hist" not in st.session_state:
                    st.session_state.metric_mode_comex_hist = "Valor (Milhões US$)"

                metric_mode_hist = st.segmented_control(
                    "Métrica:",
                    options=["Valor (Milhões US$)", "Variação (%)"],
                    key="metric_mode_comex_hist",
                    selection_mode="single",
                    on_change=set_comex_municipios_open,
                )
                if not metric_mode_hist:
                    metric_mode_hist = "Valor (Milhões US$)"

            if metric_mode_hist == "Valor (Milhões US$)":
                df_plot = df_comex_hist
                label_y = "(Milhões de US$)"
                titulo = f"Evolução das Exportações dos Municípios em {ANO_SELECIONADO}"
                fmt = ",.1f"
            else:
                df_plot = df_comex_hist_perc
                label_y = "Variação frente mesmo período do ano anterior (%)"
                titulo = f"Variação Mensal das Exportações dos Municípios em {ANO_SELECIONADO}"
                fmt = ",.1f"

            df_plot = df_plot[df_plot.index.year == ANO_SELECIONADO].copy()

            if not df_plot.empty:
                df_plot.index = [
                    f"{MESES_DIC[d.month][:3]}/{str(d.year)[2:]}" for d in df_plot.index
                ]
                titulo_centralizado(titulo, 5)
                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=fmt,
                    hover_label_format=",.2f",
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.warning("Sem dados para o ano selecionado.")

        # --- ABA 2: MÊS (Comparativo Anual) ---
        elif aba_selecionada_comex == "Mês":
            col1_m, _ = st.columns([0.5, 0.5])
            with col1_m:
                # Inicialização Segura
                if "metric_mode_comex_mes" not in st.session_state:
                    st.session_state.metric_mode_comex_mes = "Valor (Milhões US$)"

                metric_mode_mes = st.segmented_control(
                    "Métrica:",
                    options=["Valor (Milhões US$)", "Variação (%)"],
                    key="metric_mode_comex_mes",
                    selection_mode="single",
                    on_change=set_comex_municipios_open,
                )
                if not metric_mode_mes:
                    metric_mode_mes = "Valor (Milhões US$)"

            if metric_mode_mes == "Valor (Milhões US$)":
                df_plot = df_comex_mes
                label_y = "(Milhões de US$)"
                titulo = f"Exportações dos Municípios em {MESES_DIC[ult_mes_comex]}"
            else:
                df_plot = df_comex_mes_perc
                label_y = "Variação frente mesmo período do ano anterior (%)"
                titulo = f"Variação das Exportações dos Municípios em {MESES_DIC[ult_mes_comex]}"

            df_plot.index = (
                MESES_DIC[ult_mes_comex][:3]
                + "/"
                + df_plot.index.astype(str).str.slice(-2)
            )

            titulo_centralizado(titulo, 5)
            fig_mes = criar_grafico_barras(
                df=df_plot,
                titulo="",
                label_y=label_y,
                barmode="group",
                height=400,
                data_label_format=",.1f",
                hover_label_format=",.2f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig_mes, width="stretch")

        # --- ABA 3: ACUMULADO NO ANO ---
        elif aba_selecionada_comex == "Acumulado no Ano":
            col1_a, _ = st.columns([0.5, 0.5])
            with col1_a:
                # Inicialização Segura
                if "metric_mode_comex_acum" not in st.session_state:
                    st.session_state.metric_mode_comex_acum = "Valor (Milhões US$)"

                metric_mode_acum = st.segmented_control(
                    "Métrica:",
                    options=["Valor (Milhões US$)", "Variação (%)"],
                    key="metric_mode_comex_acum",
                    selection_mode="single",
                    on_change=set_comex_municipios_open,
                )
                if not metric_mode_acum:
                    metric_mode_acum = "Valor (Milhões US$)"

            if metric_mode_acum == "Valor (Milhões US$)":
                df_plot = df_comex_acum.copy()
                label_y = "(Milhões de US$)"
                titulo = f"Exportações Acumuladas dos Municípios de Janeiro a {MESES_DIC[ult_mes_comex]}"
            else:
                df_plot = df_comex_acum_perc.copy()
                label_y = "Variação frente mesmo período do ano anterior (%)"
                titulo = f"Variação Acumulada das Exportações dos Municípios até {MESES_DIC[ult_mes_comex]}"

            df_plot.index = (
                "Jan-"
                + MESES_DIC[ult_mes_comex][:3]
                + "/"
                + df_plot.index.astype(str).str.slice(-2)
            )

            titulo_centralizado(titulo, 5)
            fig_acum = criar_grafico_barras(
                df=df_plot,
                titulo="",
                label_y=label_y,
                barmode="group",
                height=400,
                data_label_format=",.1f",
                hover_label_format=",.2f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig_acum, width="stretch")

        # --- ABA 4: ANUAL ---
        elif aba_selecionada_comex == "Anual":
            col1_an, _ = st.columns([0.5, 0.5])
            with col1_an:
                # Inicialização Segura
                if "metric_mode_comex_anual" not in st.session_state:
                    st.session_state.metric_mode_comex_anual = "Valor (Milhões US$)"

                metric_mode_anual = st.segmented_control(
                    "Métrica:",
                    options=["Valor (Milhões US$)", "Variação (%)"],
                    key="metric_mode_comex_anual",
                    selection_mode="single",
                    on_change=set_comex_municipios_open,
                )
                if not metric_mode_anual:
                    metric_mode_anual = "Valor (Milhões US$)"

            if metric_mode_anual == "Valor (Milhões US$)":
                df_plot = df_comex_ano
                label_y = "(Milhões de US$)"
                titulo = "Exportações Anuais dos Municípios"
            else:
                df_plot = df_comex_ano_perc
                label_y = "Variação frente mesmo período do ano anterior (%)"
                titulo = "Variação Anual das Exportações dos Municípios"

            titulo_centralizado(titulo, 5)
            fig_anual = criar_grafico_barras(
                df=df_plot,
                titulo="",
                label_y=label_y,
                barmode="group",
                height=400,
                data_label_format=",.1f",
                hover_label_format=",.2f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig_anual, width="stretch")


@st.cache_data
def preparar_dados_comex_produto_pais_pivot(
    df, tipo_agg, view_mode_tabela, metric_mode_tabela, anos_interesse_global
):
    """
    Prepara e pivota os dados para a tabela dinâmica por País/Produto.
    CORREÇÃO: Soma os valores absolutos antes de calcular a variação percentual
    para evitar médias de porcentagens incorretas.
    Renomeia índices para apresentação (País, Produto).
    """
    if df.empty:
        return pd.DataFrame()

    # 1. Filtrar Dados pelos anos globais de interesse
    df_filtrado = df[df["ano"].isin(anos_interesse_global)].copy()

    if df_filtrado.empty:
        return pd.DataFrame()

    # --- LÓGICA DO MÊS DE REFERÊNCIA ---
    ultimo_ano_dados = df_filtrado["ano"].max()
    ult_mes_referencia = df_filtrado[df_filtrado["ano"] == ultimo_ano_dados][
        "mes"
    ].max()

    # 2. Definir colunas de valor (Atual e Anterior) com base na visualização
    if view_mode_tabela == "Anual":
        # Filtra apenas mês 12
        df_view = df_filtrado[df_filtrado["mes"] == 12].copy()
        col_valor_atual = "valor_acumulado_ano"
        col_valor_ant = "valor_acumulado_ano_anterior"
        prefixo_col = "Ano"
    else:
        # Filtra pelo mês de referência para todos os anos
        df_view = df_filtrado[df_filtrado["mes"] == ult_mes_referencia].copy()

        if view_mode_tabela == "Mês":
            col_valor_atual = "valor_exp_mensal"
            col_valor_ant = "valor_exp_mensal_ano_anterior"
            prefixo_col = f"{MESES_DIC[ult_mes_referencia]}"
        else:  # Acumulado do Ano
            col_valor_atual = "valor_acumulado_ano"
            col_valor_ant = "valor_acumulado_ano_anterior"
            prefixo_col = f"Jan-{MESES_DIC[ult_mes_referencia][:3]}"

    if df_view.empty:
        return pd.DataFrame()

    # 3. Agrupar e Somar Valores Absolutos (Crucial para Variação correta)
    # Definir colunas de agrupamento
    if tipo_agg == "pais":
        cols_group = ["pais"]
    elif tipo_agg == "produto":
        cols_group = ["produto"]
    else:  # pais_produto
        cols_group = ["pais", "produto"]

    # Agrupa por (Categorias + Ano) e soma o valor atual E o valor do ano anterior
    df_grouped = (
        df_view.groupby(cols_group + ["ano"])[[col_valor_atual, col_valor_ant]]
        .sum()
        .reset_index()
    )

    # 4. Pivotar VALORES (Para exibir ou para ordenar)
    pivot_valores = df_grouped.pivot_table(
        index=cols_group,
        columns="ano",
        values=col_valor_atual,
        aggfunc="sum",
        fill_value=0,
    )

    # Ordenação (Sempre pelo maior valor do ano mais recente disponível)
    if not pivot_valores.empty:
        ultimo_ano_col = pivot_valores.columns.max()
        pivot_valores = pivot_valores.sort_values(by=ultimo_ano_col, ascending=False)

    # 5. Calcular o DataFrame Final
    if metric_mode_tabela == "Valor (US$)":
        df_final = pivot_valores
    else:
        # Calcular porcentagem baseada nas somas agrupadas
        df_grouped["variacao_calc"] = (
            (df_grouped[col_valor_atual] / df_grouped[col_valor_ant].replace(0, pd.NA))
            - 1
        ) * 100

        # Pivotar a variação calculada
        pivot_perc = df_grouped.pivot_table(
            index=cols_group,
            columns="ano",
            values="variacao_calc",
            aggfunc="max",  # Como já agrupamos antes, aqui é único
        )

        # Reindexar para manter a mesma ordem da tabela de valores (Maiores exportadores primeiro)
        df_final = pivot_perc.reindex(pivot_valores.index)

    # 6. Renomear Colunas
    if view_mode_tabela == "Anual":
        df_final.columns = [str(ano) for ano in df_final.columns]
    else:
        # Formato: Jan-Nov/24 ou Nov/24
        df_final.columns = [f"{prefixo_col}/{str(ano)[2:]}" for ano in df_final.columns]

    # 7. Renomear Índices (País, Produto com maiúscula)
    new_names = []
    for name in df_final.index.names:
        if name == "pais":
            new_names.append("País")
        elif name == "produto":
            new_names.append("Produto")
        else:
            new_names.append(name)
    df_final.index.names = new_names

    return df_final


@st.cache_data
def preparar_grafico_comex_pais_produto(df_filtrado):
    """
    Gera gráfico de barras empilhadas para a aba de País/Produto
    """
    if df_filtrado.empty:
        return None

    df_grafico = (
        df_filtrado.assign(
            date=lambda x: pd.to_datetime(dict(year=x.ano, month=x.mes, day=1))
        )
        .pivot_table(
            index="date",
            columns="pais",
            values="valor_exp_mensal",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
    )

    if not df_grafico.empty:
        df_grafico.index = [
            f"{MESES_DIC[d.month][:3]}/{str(d.year)[2:]}" for d in df_grafico.index
        ]

    return criar_grafico_barras(
        df=df_grafico,
        titulo="",
        label_y="Valor Exportado (US$)",
        barmode="stack",
        height=400,
        data_label_format=",.0f",
        hover_label_format=",.0f",
        color_map=CORES_MUNICIPIOS,
    )


def display_comex_produto_pais_expander(df, municipio_interesse):
    if "comex_produto_pais_expander" not in st.session_state:
        st.session_state.comex_produto_pais_expander = False

    with st.expander(
        f"Comércio Exterior de {municipio_interesse} por Destino e Produto",
        expanded=st.session_state.comex_produto_pais_expander,
    ):
        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab_produto = "main_tab_nav_comex_produto"
        if key_main_tab_produto not in st.session_state:
            st.session_state[key_main_tab_produto] = "País"

        aba_selecionada_produto = st.pills(
            "Selecione uma análise:",
            options=["País", "Produto", "País - Produto"],
            selection_mode="single",
            key=key_main_tab_produto,
        )

        if not aba_selecionada_produto:
            aba_selecionada_produto = "País"

        # --- ABA PAÍS ---
        if aba_selecionada_produto == "País":
            # Layout: Métrica e Visualização na linha de cima
            col_view_p, col_metric_p = st.columns(2)

            with col_metric_p:
                # Inicialização Segura
                if "metric_mode_pais" not in st.session_state:
                    st.session_state.metric_mode_pais = "Valor (US$)"

                metric_mode_p = st.segmented_control(
                    "Métrica:",
                    options=["Valor (US$)", "Variação (%)"],
                    key="metric_mode_pais",
                    on_change=set_comex_produto_pais_open,
                )
                if not metric_mode_p:
                    metric_mode_p = "Valor (US$)"

            with col_view_p:
                # Inicialização Segura
                if "view_mode_pais" not in st.session_state:
                    st.session_state.view_mode_pais = "Mês"

                view_mode_p = st.segmented_control(
                    "Visualização:",
                    options=["Mês", "Acumulado do Ano", "Anual"],
                    key="view_mode_pais",
                    on_change=set_comex_produto_pais_open,
                )
                if not view_mode_p:
                    view_mode_p = "Mês"

            # Busca na linha de baixo (full width)
            texto_busca_pais = st.text_input(
                "🔍 Pesquisar País:",
                key="busca_pais",
                placeholder="Ex: Estados Unidos, China",
            )

            df_pivot_pais = preparar_dados_comex_produto_pais_pivot(
                df, "pais", view_mode_p, metric_mode_p, anos_de_interesse
            )

            if not df_pivot_pais.empty:
                if texto_busca_pais:
                    df_pivot_pais = df_pivot_pais[
                        df_pivot_pais.index.str.contains(
                            texto_busca_pais, case=False, na=False
                        )
                    ]

                styler = df_pivot_pais.style
                if metric_mode_p == "Valor (US$)":
                    styler = styler.format(formatar_valor_br)
                    # Adiciona gradiente de cor (azul) para os valores
                    styler = styler.background_gradient(cmap="Blues", axis=0)
                else:
                    # CORREÇÃO AQUI: Usando o formatador customizado BR
                    styler = styler.format(formatar_pct_br).map(style_saldo_variacao)

                st.dataframe(styler, width="stretch")
            else:
                st.info("Sem dados para a seleção atual.")

        # --- ABA PRODUTO ---
        elif aba_selecionada_produto == "Produto":
            # Layout: Métrica e Visualização
            col_view_prod, col_metric_prod = st.columns(2)

            with col_metric_prod:
                # Inicialização Segura
                if "metric_mode_prod" not in st.session_state:
                    st.session_state.metric_mode_prod = "Valor (US$)"

                metric_mode_prod = st.segmented_control(
                    "Métrica:",
                    options=["Valor (US$)", "Variação (%)"],
                    key="metric_mode_prod",
                    on_change=set_comex_produto_pais_open,
                )
                if not metric_mode_prod:
                    metric_mode_prod = "Valor (US$)"

            with col_view_prod:
                # Inicialização Segura
                if "view_mode_prod" not in st.session_state:
                    st.session_state.view_mode_prod = "Mês"

                view_mode_prod = st.segmented_control(
                    "Visualização:",
                    options=["Mês", "Acumulado do Ano", "Anual"],
                    key="view_mode_prod",
                    on_change=set_comex_produto_pais_open,
                )
                if not view_mode_prod:
                    view_mode_prod = "Mês"

            # Busca em baixo
            texto_busca_prod = st.text_input(
                "🔍 Pesquisar Produto:",
                key="busca_prod",
                placeholder="Ex: Calçados, Ferramentas",
            )

            df_pivot_prod = preparar_dados_comex_produto_pais_pivot(
                df, "produto", view_mode_prod, metric_mode_prod, anos_de_interesse
            )

            if not df_pivot_prod.empty:
                if texto_busca_prod:
                    df_pivot_prod = df_pivot_prod[
                        df_pivot_prod.index.str.contains(
                            texto_busca_prod, case=False, na=False
                        )
                    ]

                styler = df_pivot_prod.style
                if metric_mode_prod == "Valor (US$)":
                    styler = styler.format(formatar_valor_br)
                    # Adiciona gradiente de cor (azul) para os valores
                    styler = styler.background_gradient(cmap="Blues", axis=0)
                else:
                    # CORREÇÃO AQUI
                    styler = styler.format(formatar_pct_br).map(style_saldo_variacao)

                st.dataframe(styler, width="stretch")
            else:
                st.info("Sem dados para a seleção atual.")

        # --- ABA PAÍS - PRODUTO ---
        elif aba_selecionada_produto == "País - Produto":
            # Layout: Métrica e Visualização
            col_view_pp, col_metric_pp = st.columns(2)

            with col_view_pp:
                # Inicialização Segura
                if "view_mode_pp" not in st.session_state:
                    st.session_state.view_mode_pp = "Mês"

                view_mode_pp = st.segmented_control(
                    "Visualização:",
                    options=["Mês", "Acumulado do Ano", "Anual"],
                    key="view_mode_pp",
                    on_change=set_comex_produto_pais_open,
                )
                if not view_mode_pp:
                    view_mode_pp = "Mês"

            with col_metric_pp:
                # Inicialização Segura
                if "metric_mode_pp" not in st.session_state:
                    st.session_state.metric_mode_pp = "Valor (US$)"

                metric_mode_pp = st.segmented_control(
                    "Métrica:",
                    options=["Valor (US$)", "Variação (%)"],
                    key="metric_mode_pp",
                    on_change=set_comex_produto_pais_open,
                )
                if not metric_mode_pp:
                    metric_mode_pp = "Valor (US$)"

            # Busca em baixo
            texto_busca_pp = st.text_input(
                "🔍 Pesquisar País ou Produto:",
                key="busca_pp",
                placeholder="Ex: Estados Unidos ou Calçados",
            )

            df_pivot_pp = preparar_dados_comex_produto_pais_pivot(
                df, "pais_produto", view_mode_pp, metric_mode_pp, anos_de_interesse
            )

            if not df_pivot_pp.empty:
                if texto_busca_pp:
                    idx_as_str = df_pivot_pp.index.map(
                        lambda x: " ".join(str(v) for v in x)
                    )
                    df_pivot_pp = df_pivot_pp[
                        idx_as_str.str.contains(texto_busca_pp, case=False, na=False)
                    ]

                styler = df_pivot_pp.style
                if metric_mode_pp == "Valor (US$)":
                    styler = styler.format(formatar_valor_br)
                    # Adiciona gradiente de cor (azul) para os valores
                    styler = styler.background_gradient(cmap="Blues", axis=0)
                else:
                    # CORREÇÃO AQUI
                    styler = styler.format(formatar_pct_br).map(style_saldo_variacao)

                st.dataframe(styler, width="stretch")
            else:
                st.info("Sem dados para a seleção atual.")


def show_page_comex(
    df_comex_ano,
    df_comex_mensal,
    df_comex_municipio_raw,
    municipios_selecionados,
    municipio_de_interesse,
):
    """Função principal que renderiza a página de Comércio Exterior."""

    if "comex_municipios_expander" not in st.session_state:
        st.session_state.comex_municipios_expander = False
    if "comex_produto_pais_expander" not in st.session_state:
        st.session_state.comex_produto_pais_expander = False

    titulo_centralizado("Dashboard de Comércio Exterior", 1)

    municipio_foco = (
        municipios_selecionados[0]
        if municipios_selecionados
        else municipio_de_interesse
    )

    df_comex_municipio_filtrado = df_comex_municipio_raw[
        df_comex_municipio_raw["municipio"] == municipio_foco
    ]

    display_comex_kpi_cards(
        df_comex_ano, df_comex_mensal, municipio_interesse=municipio_foco
    )
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

    display_comex_municipios_expander(df_mes=df_comex_mensal, df_ano=df_comex_ano)

    display_comex_produto_pais_expander(
        df=df_comex_municipio_filtrado, municipio_interesse=municipio_foco
    )
