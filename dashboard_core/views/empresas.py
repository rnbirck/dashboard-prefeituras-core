import streamlit as st
import pandas as pd

from dashboard_core.utils import (
    MESES_DIC,
    titulo_centralizado,
    calcular_yoy,
    filtrar_municipio_ult_mes_ano,
    criar_grafico_barras,
    preparar_dados_graficos_anuais,
    style_saldo_variacao,
)

municipio_de_interesse = None
CORES_MUNICIPIOS = {}
ordem_tamanho_estabelecimentos = []


def set_empresas_config(municipio, cores_municipios, ordem):
    """
    Injeta a configuração específica do município para as views de empresas.
    Chamar no app.py antes de renderizar a página de empresas.
    """
    global municipio_de_interesse, CORES_MUNICIPIOS, ordem_tamanho_estabelecimentos
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}
    ordem_tamanho_estabelecimentos = ordem or []


# --- FUNÇÕES DE CALLBACK ---


def set_expander_open(key):
    """Define o estado de um expander específico como True (aberto)."""
    st.session_state[key] = True


def cnpj_callback():
    """Callback para manter o expander CNPJ Ativos aberto."""
    set_expander_open("cnpj_ativos_expander_state")


def mei_callback():
    """Callback para manter o expander MEI Ativos aberto."""
    set_expander_open("mei_ativos_expander_state")


def estabelecimentos_callback():
    """Callback para manter o expander Estabelecimentos aberto."""
    set_expander_open("estabelecimentos_expander_state")


# ==============================================================================
# FUNÇÕES DA PÁGINA DE EMPRESAS ATIVAS
# ==============================================================================


def display_cnpj_kpi_cards(df_cnpj, df_mei, municipio_de_interesse):
    """Exibe os cards de KPI de Empresas Ativas para um município específico."""
    titulo_centralizado(f"Número de Empresas Ativas em {municipio_de_interesse}", 3)
    ult_ano = df_cnpj["ano"].max()
    ult_mes = df_cnpj[df_cnpj["ano"] == ult_ano]["mes"].max()

    cnpj_ativos_ult_mes = filtrar_municipio_ult_mes_ano(
        df_cnpj, municipio_de_interesse
    )["empresas_ativas"].sum()
    cnpj_ativos_yoy = calcular_yoy(
        df=df_cnpj,
        municipio=municipio_de_interesse,
        ultimo_ano=ult_ano,
        ultimo_mes=ult_mes,
        coluna="empresas_ativas",
        round=1,
    )
    mei_ativos_ult_mes = filtrar_municipio_ult_mes_ano(df_mei, municipio_de_interesse)[
        "empresas_ativas"
    ].sum()
    mei_ativos_yoy = calcular_yoy(
        df=df_mei,
        municipio=municipio_de_interesse,
        ultimo_ano=ult_ano,
        ultimo_mes=ult_mes,
        coluna="empresas_ativas",
        round=1,
    )
    col1, col2 = st.columns(2)

    col1.metric(
        label=f"CNPJ Ativos em {MESES_DIC[ult_mes]} de {ult_ano}",
        value=f"{cnpj_ativos_ult_mes:,.0f}".replace(",", "."),
        delta=f"{cnpj_ativos_yoy}%".replace(".", ","),
        help="Taxa de Variação percentual em relação ao mesmo mês do ano anterior",
        border=True,
    )
    col2.metric(
        label=f"MEI Ativos em {MESES_DIC[ult_mes]} de {ult_ano}",
        value=f"{mei_ativos_ult_mes:,.0f}".replace(",", "."),
        delta=f"{mei_ativos_yoy}%".replace(".", ","),
        help="Taxa de Variação percentual em relação ao mesmo mês do ano anterior",
        border=True,
    )


@st.cache_data
def preparar_dados_grafico_empresas_ativas(df, df_setor, df_cnae, df_cnae_saldo):
    """
    Prepara os dados base para os gráficos e tabelas.
    Retorna DataFrames com coluna 'date' para facilitar filtragens dinâmicas.
    Agora utiliza df_setor para as visões de Setor Econômico.
    """

    def processar_df_base(dataframe, index_col, value_col):
        # Verifica se a coluna existe
        if value_col not in dataframe.columns:
            return pd.DataFrame()

        return (
            dataframe.assign(
                date=lambda x: pd.to_datetime(
                    x["ano"].astype(str)
                    + "-"
                    + x["mes"].astype(str).str.zfill(2)
                    + "-01"
                )
            )
            .pivot_table(
                index="date",
                columns=index_col,
                values=value_col,
                aggfunc="sum",
                observed=False,
                fill_value=0,
            )
            .sort_index()
        )

    def adicionar_coluna_data(dataframe):
        if dataframe.empty:
            return dataframe.copy()

        return dataframe.assign(
            date=lambda x: pd.to_datetime(
                x["ano"].astype(str) + "-" + x["mes"].astype(str).str.zfill(2) + "-01"
            )
        )

    def calcular_saldo_yoy_cnae(dataframe):
        if dataframe.empty:
            return dataframe.copy()

        df_proc = dataframe.copy().sort_values(
            by=["municipio", "grupo", "grupo_ibge", "mes", "ano"]
        )
        df_proc["empresas_ativas_ano_anterior"] = df_proc.groupby(
            ["municipio", "grupo", "grupo_ibge", "mes"], dropna=False
        )["empresas_ativas"].shift(1)
        df_proc["saldo_empresas_yoy"] = (
            df_proc["empresas_ativas"] - df_proc["empresas_ativas_ano_anterior"]
        )
        df_proc.loc[
            df_proc["empresas_ativas_ano_anterior"].isna(), "saldo_empresas_yoy"
        ] = pd.NA
        return df_proc

    # 1. Dados Totais por Município (Date x Municipio)
    df_graf_total = processar_df_base(df, "municipio", "empresas_ativas")

    df_graf_total_yoy = processar_df_base(df, "municipio", "empresas_ativas_yoy")

    # 2. Dados por Setor (Date x Grupo IBGE)
    df_graf_setor = processar_df_base(df_setor, "grupo_ibge", "empresas_ativas")

    # 2.1 Dados YoY Setor -
    df_graf_setor_yoy = processar_df_base(df_setor, "grupo_ibge", "empresas_ativas_yoy")

    # 3. Dados CNAE Estoque (Date x Grupo)
    df_cnae_processed = adicionar_coluna_data(df_cnae)
    df_cnae_saldo_yoy_processed = adicionar_coluna_data(
        calcular_saldo_yoy_cnae(df_cnae)
    )

    # Últimos dados para defaults
    ult_ano = df["ano"].max()
    ult_mes = df[df["ano"] == ult_ano]["mes"].max()

    return (
        df_graf_total,
        df_graf_total_yoy,
        df_graf_setor,
        df_graf_setor_yoy,
        df_cnae_processed,
        df_cnae_saldo_yoy_processed,
        ult_ano,
        ult_mes,
    )


def display_empresas_ativas_expander(
    df,
    df_setor,
    df_cnae,
    df_cnae_saldo,
    titulo_expander,
    key_prefix,
    expander_state_key,
    callback_func,
):
    """Renderiza a seção de CNPJ ou MEI Ativos."""

    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(
        f"{titulo_expander}", expanded=st.session_state[expander_state_key]
    ):
        (
            df_graf_total,
            df_graf_total_yoy,
            df_graf_setor,
            df_graf_setor_yoy,
            df_cnae_processed,
            df_cnae_saldo_yoy_processed,
            ult_ano,
            ult_mes,
        ) = preparar_dados_grafico_empresas_ativas(
            df=df, df_setor=df_setor, df_cnae=df_cnae, df_cnae_saldo=df_cnae_saldo
        )

        anos_disponiveis = sorted(df["ano"].unique().tolist(), reverse=True)

        # Navegação entre as análises
        aba_selecionada = st.pills(
            "Selecione o tipo de análise:",
            [f"{titulo_expander} por Município", "Setor", "CNAE"],
            selection_mode="single",
            default=f"{titulo_expander} por Município",
            key=f"main_tab_nav_{key_prefix}",
        )
        if not aba_selecionada:
            aba_selecionada = f"{titulo_expander} por Município"

        # --- ABA 1: MUNICÍPIO ---
        if aba_selecionada == f"{titulo_expander} por Município":
            col1, col2 = st.columns([0.5, 0.5])
            with col1:
                view_mode_total = (
                    st.segmented_control(
                        "Visualização:",
                        options=["Evolução", "Mês", "Anual"],
                        selection_mode="single",
                        default="Evolução",
                        key=f"view_mode_total_{key_prefix}",
                        on_change=callback_func,
                    )
                    or "Evolução"
                )

            with col2:
                if view_mode_total == "Evolução":
                    ano_sel = st.selectbox(
                        "Selecione o ano:",
                        options=anos_disponiveis,
                        index=0,
                        key=f"ano_total_{key_prefix}",
                        on_change=callback_func,
                    )
                    metric_mode_total = "Total"
                else:
                    # Seletor de Métrica para Mês e Anual
                    metric_mode_total = (
                        st.segmented_control(
                            "Métrica:",
                            options=["Total", "Variação (%)"],
                            selection_mode="single",
                            default="Total",
                            key=f"metric_mode_total_{key_prefix}",
                            on_change=callback_func,
                        )
                        or "Total"
                    )

            # Seleção do DataFrame base e Formatação
            if metric_mode_total == "Variação (%)":
                df_base = df_graf_total_yoy
                label_y = "Variação (%)"
                fmt = ",.1f"
            else:
                df_base = df_graf_total
                label_y = "Empresas Ativas"
                fmt = ",.0f"

            df_plot = pd.DataFrame()
            titulo_grafico = ""

            if view_mode_total == "Evolução":
                df_plot = df_base[df_base.index.year == ano_sel].copy()
                df_plot.index = [
                    f"{MESES_DIC[d.month][:3]}/{str(d.year)[-2:]}"
                    for d in df_plot.index
                ]
                titulo_grafico = f"Evolução Mensal em {ano_sel}"

            elif view_mode_total == "Mês":
                df_plot = df_base[df_base.index.month == ult_mes].copy()
                df_plot.index = [
                    f"{MESES_DIC[d.month][:3]}/{str(d.year)[-2:]}"
                    for d in df_plot.index
                ]
                if metric_mode_total == "Variação (%)":
                    titulo_grafico = (
                        f"Variação em {MESES_DIC[ult_mes]} (vs Ano Anterior)"
                    )
                else:
                    titulo_grafico = f"{titulo_expander} em {MESES_DIC[ult_mes]}"

            elif view_mode_total == "Anual":
                df_plot = df_base[df_base.index.month == 12].copy()
                df_plot.index = df_plot.index.year.astype(str)
                if metric_mode_total == "Variação (%)":
                    titulo_grafico = "Variação Anual"
                else:
                    titulo_grafico = f"{titulo_expander} por Ano"

            titulo_centralizado(titulo_grafico, 5)
            if not df_plot.empty:
                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=fmt,
                    hover_label_format=fmt,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.warning("Sem dados para a seleção.")

        # --- ABA 2: SETOR ---
        elif aba_selecionada == "Setor":
            col1_s, col2_s = st.columns([0.5, 0.5])
            with col1_s:
                view_mode_setor = (
                    st.segmented_control(
                        "Visualização:",
                        options=["Evolução", "Mês", "Anual"],
                        selection_mode="single",
                        default="Evolução",
                        key=f"view_mode_setor_{key_prefix}",
                        on_change=callback_func,
                    )
                    or "Evolução"
                )

            with col2_s:
                if view_mode_setor == "Evolução":
                    ano_sel_setor = st.selectbox(
                        "Selecione o ano:",
                        options=anos_disponiveis,
                        index=0,
                        key=f"ano_setor_{key_prefix}",
                        on_change=callback_func,
                    )
                    metric_mode_setor = "Total"
                else:
                    metric_mode_setor = (
                        st.segmented_control(
                            "Métrica:",
                            options=["Total", "Variação (%)"],
                            selection_mode="single",
                            default="Total",
                            key=f"metric_mode_setor_{key_prefix}",
                            on_change=callback_func,
                        )
                        or "Total"
                    )

            # Seleção do DataFrame base SETOR
            if metric_mode_setor == "Variação (%)":
                df_base_setor = df_graf_setor_yoy
                label_y_setor = "Variação (%)"
                fmt_setor = ",.1f"
            else:
                df_base_setor = df_graf_setor
                label_y_setor = "Empresas Ativas"
                fmt_setor = ",.0f"

            df_plot_setor = pd.DataFrame()
            titulo_grafico_setor = ""

            if view_mode_setor == "Evolução":
                df_plot_setor = df_base_setor[
                    df_base_setor.index.year == ano_sel_setor
                ].copy()
                df_plot_setor.index = [
                    f"{MESES_DIC[d.month][:3]}/{str(d.year)[-2:]}"
                    for d in df_plot_setor.index
                ]
                titulo_grafico_setor = f"Evolução por Setor em {ano_sel_setor}"

            elif view_mode_setor == "Mês":
                df_plot_setor = df_base_setor[
                    df_base_setor.index.month == ult_mes
                ].copy()
                df_plot_setor.index = [
                    f"{MESES_DIC[d.month][:3]}/{str(d.year)[-2:]}"
                    for d in df_plot_setor.index
                ]
                if metric_mode_setor == "Variação (%)":
                    titulo_grafico_setor = f"Variação em {MESES_DIC[ult_mes]} por Setor"
                else:
                    titulo_grafico_setor = (
                        f"{titulo_expander} em {MESES_DIC[ult_mes]} por Setor"
                    )

            elif view_mode_setor == "Anual":
                df_plot_setor = df_base_setor[df_base_setor.index.month == 12].copy()
                df_plot_setor.index = df_plot_setor.index.year.astype(str)
                if metric_mode_setor == "Variação (%)":
                    titulo_grafico_setor = "Variação Anual por Setor"
                else:
                    titulo_grafico_setor = f"{titulo_expander} por Ano por Setor"

            titulo_centralizado(titulo_grafico_setor, 5)
            if not df_plot_setor.empty:
                # Se for variação barras lado a lado para facilitar comparação
                barmode = "group" if metric_mode_setor == "Variação (%)" else "stack"

                fig_setor = criar_grafico_barras(
                    df=df_plot_setor,
                    titulo="",
                    label_y=label_y_setor,
                    barmode=barmode,
                    height=400,
                    data_label_format=fmt_setor,
                    hover_label_format=fmt_setor,
                    color_map=CORES_MUNICIPIOS
                    if "municipio" in df_plot_setor.columns
                    else None,
                )
                st.plotly_chart(fig_setor, width="stretch")
            else:
                st.warning("Sem dados para a seleção.")

        # --- ABA 3: CNAE (TABELA) ---
        elif aba_selecionada == "CNAE":
            col1_c, col2_c = st.columns([0.5, 0.5])

            with col2_c:
                metric_mode_cnae = (
                    st.segmented_control(
                        "Métrica:",
                        options=["Estoque", "Saldo"],
                        selection_mode="single",
                        default="Estoque",
                        key=f"metric_cnae_{key_prefix}",
                        on_change=callback_func,
                    )
                    or "Estoque"
                )

            with col1_c:
                view_mode_cnae = (
                    st.segmented_control(
                        "Visualização:",
                        options=["Mês", "Anual"],
                        selection_mode="single",
                        default="Mês",
                        key=f"view_mode_cnae_{key_prefix}",
                        on_change=callback_func,
                    )
                    or "Mês"
                )

            # 1. CALCULAR A ORDEM (BASEADA SEMPRE NO ESTOQUE)
            if view_mode_cnae == "Mês":

                def filter_condition(x):
                    return x["date"].dt.month == ult_mes

                titulo_sufixo = f"em {MESES_DIC[ult_mes]}"

                def col_fmt(d):
                    return f"{MESES_DIC[d.month][:3]}/{str(d.year)[-2:]}"

            else:  # Anual

                def filter_condition(x):
                    return x["date"].dt.month == 12

                titulo_sufixo = "por Ano"

                def col_fmt(d):
                    return str(d.year)

            # Tabela Referência (Estoque) para ordenar
            df_estoque_ref = df_cnae_processed[filter_condition(df_cnae_processed)]

            ordenacao_fixa = []
            if not df_estoque_ref.empty:
                pivot_ref = df_estoque_ref.pivot_table(
                    index="grupo",
                    columns="date",
                    values="empresas_ativas",
                    aggfunc="sum",
                    observed=False,
                    fill_value=0,
                )
                last_col = pivot_ref.columns[-1]
                ordenacao_fixa = pivot_ref.sort_values(
                    by=last_col, ascending=False
                ).index

            # 2. PREPARAR DADOS DE EXIBIÇÃO
            if metric_mode_cnae == "Estoque":
                df_base = df_cnae_processed[filter_condition(df_cnae_processed)]
                val_col = "empresas_ativas"
                cmap = "GnBu"  # Azul para estoque
                titulo_tabela = f"Estoque {titulo_sufixo} por CNAE"
            else:
                df_base = df_cnae_saldo_yoy_processed[
                    filter_condition(df_cnae_saldo_yoy_processed)
                ]
                val_col = "saldo_empresas_yoy"
                titulo_tabela = f"Saldo {titulo_sufixo} por CNAE"

            if not df_base.empty:
                if metric_mode_cnae == "Saldo":
                    df_pivot_final = df_base.pivot_table(
                        index="grupo",
                        columns="date",
                        values=val_col,
                        aggfunc="first",
                        observed=False,
                    )
                else:
                    df_pivot_final = df_base.pivot_table(
                        index="grupo",
                        columns="date",
                        values=val_col,
                        aggfunc="sum",
                        observed=False,
                        fill_value=0,
                    )

                # Aplica a ordenação fixa
                if len(ordenacao_fixa) > 0:
                    indices_validos = [
                        i for i in ordenacao_fixa if i in df_pivot_final.index
                    ]
                    restante = [
                        i for i in df_pivot_final.index if i not in indices_validos
                    ]
                    df_pivot_final = df_pivot_final.reindex(indices_validos + restante)

                # Formata nomes das colunas
                df_pivot_final.columns = [col_fmt(c) for c in df_pivot_final.columns]

                titulo_centralizado(titulo_tabela, 5)

                # 3. ESTILIZAÇÃO
                if metric_mode_cnae == "Saldo":
                    # Formatação inteira para saldo absoluto versus o mesmo mês do ano anterior
                    styler = df_pivot_final.style.format(
                        lambda x: "-" if pd.isna(x) else f"{x:+,.0f}".replace(",", ".")
                    ).map(style_saldo_variacao)
                else:
                    # Formatação padrão para Estoque
                    styler = df_pivot_final.style.format(
                        lambda x: f"{x:,.0f}".replace(",", ".")
                    ).background_gradient(cmap=cmap, axis=0)

                st.dataframe(styler, width="stretch")
            else:
                st.warning("Sem dados disponíveis para esta visualização.")


def render_estabelecimentos_grafico_tab(
    df,
    coluna_agregacao,
    titulo_grafico,
    metric_mode="Quantidade",
    color_map=None,
    reorder_cols=None,
    callback=None,
):
    """
    Função auxiliar para renderizar uma aba de Estabelecimentos com gráfico.
    """
    # Definição de colunas e formatos baseado na métrica
    if metric_mode == "Variação (%)":
        coluna_valores = "qntd_estabelecimentos_yoy"
        label_y = "Variação (%)"
        fmt = ",.1f"
        titulo_final = f"Variação Anual de Estabelecimentos {titulo_grafico}"
    else:
        coluna_valores = "qntd_estabelecimentos"
        label_y = "Nº de Estabelecimentos"
        fmt = ",.0f"
        titulo_final = f"Número de Estabelecimentos {titulo_grafico}"

    titulo_centralizado(titulo_final, 5)

    # Prepara dados (agora escolhendo a coluna correta)
    df_grafico = preparar_dados_graficos_anuais(
        df_filtrado=df,
        coluna_agregacao=coluna_agregacao,
        coluna_valores=coluna_valores,
    )

    if reorder_cols and not df_grafico.empty:
        df_grafico = df_grafico.reindex(columns=reorder_cols, fill_value=0)

    # Ajuste do modo de barras
    barmode = "group" if metric_mode == "Variação (%)" else "group"

    fig = criar_grafico_barras(
        df=df_grafico,
        titulo="",
        label_y=label_y,
        color_map=color_map,
        barmode=barmode,
        data_label_format=fmt,
        hover_label_format=fmt,
    )
    st.plotly_chart(fig, width="stretch")


def render_estabelecimentos_tabela_tab(
    df, index_col, titulo, municipio_interesse, metric_mode="Quantidade"
):
    """
    Função auxiliar para renderizar uma aba de Estabelecimentos com tabela (CNAE).
    Ordenação fixa pela QUANTIDADE (maior para menor), independente da métrica visualizada.
    """
    # 1. Configurações de Exibição baseadas na Métrica
    if metric_mode == "Variação (%)":
        val_col = "qntd_estabelecimentos_yoy"
        titulo_final = f"Variação Anual de Estabelecimentos {titulo}"
        fmt = "{:,.1f}"
        agg = "sum"
    else:
        val_col = "qntd_estabelecimentos"
        titulo_final = f"Número de Estabelecimentos {titulo} "
        fmt = "{:,.0f}"
        agg = "sum"

    titulo_centralizado(f"{titulo_final} em {municipio_interesse}", 5)

    ult_ano = df["ano"].max()

    # 2. Lógica de Ordenação (Quantidade no último ano)
    df_ordenacao = (
        df[df["ano"] == ult_ano]
        .groupby(index_col)["qntd_estabelecimentos"]
        .sum()
        .sort_values(ascending=False)
    )
    # Lista ordenada de índices (nomes dos Grupos ou Subclasses)
    ordem_indices = df_ordenacao.index.tolist()

    # 3. Criação da Tabela Pivot (com os valores da métrica escolhida)
    df_pivot = df.pivot_table(
        index=index_col,
        columns="ano",
        values=val_col,
        aggfunc=agg,
        observed=False,
        fill_value=0,
    )

    # 4. Aplicação da Ordenação na Tabela Pivot
    indices_existentes = [idx for idx in ordem_indices if idx in df_pivot.index]
    indices_faltantes = [idx for idx in df_pivot.index if idx not in indices_existentes]

    # Reindexa a tabela para forçar a ordem calculada no passo 2
    df_pivot = df_pivot.reindex(indices_existentes + indices_faltantes)

    df_pivot.index.name = titulo.split(" por ")[-1]

    # 5. Estilização
    if metric_mode == "Variação (%)":
        # Formatação com % e separador decimal ,
        styler = df_pivot.style.format(
            lambda x: (
                f"{x:+,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")
            )
        ).map(style_saldo_variacao)
    else:
        styler = df_pivot.style.format(fmt).background_gradient(cmap="GnBu")

    st.dataframe(styler, width="stretch")


def display_estabelecimentos(
    df_estabelecimentos_mun,
    df_estabelecimentos_tamanho,
    df_estabelecimentos_setor,
    df_estabelecimentos_grupo,
    df_estabelecimentos_subclasse,
    municipio_interesse,
    color_map=None,
    expander_state_key=None,
    callback_func=None,
):
    """Exibe o expander com a análise de Estabelecimentos."""

    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander("Estabelecimentos", expanded=st.session_state[expander_state_key]):
        aba_selecionada = st.pills(
            "Selecione uma análise:",
            ["Município", "Tamanho", "Setor", "CNAE - Grupo", "CNAE - Subclasse"],
            selection_mode="single",
            default="Município",
            key="main_tab_nav_estabelecimentos",
        )
        if not aba_selecionada:
            aba_selecionada = "Município"

        metric_mode = (
            st.segmented_control(
                "Métrica:",
                options=["Quantidade", "Variação (%)"],
                default="Quantidade",
                key="metric_mode_estabelecimentos",
                selection_mode="single",
                on_change=callback_func,
            )
            or "Quantidade"
        )

        # Aba 0: Comparativo entre Municípios
        if aba_selecionada == "Município":
            render_estabelecimentos_grafico_tab(
                df=df_estabelecimentos_mun,
                coluna_agregacao="municipio",
                titulo_grafico="por Município",
                metric_mode=metric_mode,
                color_map=color_map,
            )

        # Aba 1: Análise por Tamanho do Estabelecimento
        elif aba_selecionada == "Tamanho":
            render_estabelecimentos_grafico_tab(
                df=df_estabelecimentos_tamanho,
                coluna_agregacao="tamanho_estabelecimento",
                titulo_grafico=f"por Porte em {municipio_interesse}",
                metric_mode=metric_mode,
                reorder_cols=ordem_tamanho_estabelecimentos,
            )

        # Aba 2: Análise por Setor Econômico
        elif aba_selecionada == "Setor":
            render_estabelecimentos_grafico_tab(
                df=df_estabelecimentos_setor,
                coluna_agregacao="grupo_ibge",
                titulo_grafico=f"por Setor em {municipio_interesse}",
                metric_mode=metric_mode,
            )

        # Aba 3: Tabela por CNAE - Grupo
        elif aba_selecionada == "CNAE - Grupo":
            render_estabelecimentos_tabela_tab(
                df=df_estabelecimentos_grupo,
                index_col="grupo",
                titulo="CNAE - Grupo",
                municipio_interesse=municipio_interesse,
                metric_mode=metric_mode,
            )

        # Aba 4: Tabela por CNAE - Subclasse
        elif aba_selecionada == "CNAE - Subclasse":
            render_estabelecimentos_tabela_tab(
                df=df_estabelecimentos_subclasse,
                index_col="subclasse",
                titulo="CNAE - Subclasse",
                municipio_interesse=municipio_interesse,
                metric_mode=metric_mode,
            )


def show_page_empresas_ativas(
    df_cnpj,
    df_cnpj_cnae,
    df_cnpj_cnae_saldo,
    df_cnpj_setor,
    df_mei,
    df_mei_cnae,
    df_mei_cnae_saldo,
    df_mei_setor,
    municipio_de_interesse,
    df_estabelecimentos_mun,
    df_estabelecimentos_tamanho,
    # Novos DataFrames separados
    df_estabelecimentos_setor,
    df_estabelecimentos_grupo,
    df_estabelecimentos_subclasse,
):
    # 1. INICIALIZAÇÃO DOS ESTADOS DOS EXPANDERS (Fechados por padrão)
    if "cnpj_ativos_expander_state" not in st.session_state:
        st.session_state.cnpj_ativos_expander_state = False
    if "mei_ativos_expander_state" not in st.session_state:
        st.session_state.mei_ativos_expander_state = False
    if "estabelecimentos_expander_state" not in st.session_state:
        st.session_state.estabelecimentos_expander_state = False

    titulo_centralizado("Dashboard de Empresas Ativas", 1)

    display_cnpj_kpi_cards(
        df_cnpj=df_cnpj, df_mei=df_mei, municipio_de_interesse=municipio_de_interesse
    )
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

    # 2. CHAMADA AOS EXPANDERS COM ESTADO E CALLBACK

    # CNPJ Ativos
    display_empresas_ativas_expander(
        df=df_cnpj,
        df_setor=df_cnpj_setor,
        df_cnae=df_cnpj_cnae,
        df_cnae_saldo=df_cnpj_cnae_saldo,
        titulo_expander="CNPJ Ativos",
        key_prefix="cnpj_ativos",
        expander_state_key="cnpj_ativos_expander_state",
        callback_func=cnpj_callback,
    )

    # MEI Ativos
    display_empresas_ativas_expander(
        df=df_mei,
        df_setor=df_mei_setor,
        df_cnae=df_mei_cnae,
        df_cnae_saldo=df_mei_cnae_saldo,
        titulo_expander="MEI Ativos",
        key_prefix="mei_ativos",
        expander_state_key="mei_ativos_expander_state",
        callback_func=mei_callback,
    )

    st.markdown("###### Dados disponibilizados pela RAIS - Atualização Anual")

    # Estabelecimentos
    display_estabelecimentos(
        df_estabelecimentos_mun=df_estabelecimentos_mun,
        df_estabelecimentos_tamanho=df_estabelecimentos_tamanho,
        df_estabelecimentos_setor=df_estabelecimentos_setor,
        df_estabelecimentos_grupo=df_estabelecimentos_grupo,
        df_estabelecimentos_subclasse=df_estabelecimentos_subclasse,
        municipio_interesse=municipio_de_interesse,
        color_map=CORES_MUNICIPIOS,
        expander_state_key="estabelecimentos_expander_state",
        callback_func=estabelecimentos_callback,
    )
