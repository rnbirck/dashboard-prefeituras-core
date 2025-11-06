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
    destacar_percentuais,
    criar_tabela_comex,
    titulo_centralizado,
)

municipio_de_interesse = None
CORES_MUNICIPIOS = {}
anos_de_interesse = []


def set_comercio_exterior_config(municipio, cores_municipios, anos_interesse):
    """
    Configura valores específicos do município que antes eram importados
    do dashboard_core.config. Deve ser chamado pelo app.py antes de
    renderizar a página de comercio_exterior.
    """
    global municipio_de_interesse, CORES_MUNICIPIOS, anos_de_interesse
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}
    anos_de_interesse = anos_interesse or []


# ==============================================================================
# FUNÇÕES DA PÁGINA DE COMÉRCIO EXTERIOR
# ==============================================================================


def display_comex_kpi_cards(df_ano, df_mes, municipio_interesse):
    """Exibe os cards de KPI de Comércio Exterior para um município específico."""

    titulo_centralizado(f"Exportações de {municipio_de_interesse} (Milhões de US$)", 3)
    with st.container(border=False):
        # Ultimo mês disponível
        ult_ano = df_mes["ano"].max()
        ult_mes = df_mes[df_mes["ano"] == ult_ano]["mes"].max()
        exp_mun_ult_mes = filtrar_municipio_ult_mes_ano(df_mes, municipio_interesse)[
            "total_exp_mensal"
        ].sum()

        taxa_var_ult_mes = filtrar_municipio_ult_mes_ano(df_mes, municipio_interesse)[
            "perc_var_mes_ano_anterior"
        ].sum()

        # Acumulado no ano
        exp_mun_acu_ano = filtrar_municipio_ult_mes_ano(df_mes, municipio_interesse)[
            "total_exp_acumulado"
        ].sum()

        taxa_var_acu_ano = filtrar_municipio_ult_mes_ano(df_mes, municipio_interesse)[
            "perc_var_acum_ano_anterior"
        ].sum()

        # Último ano completo
        ano_completo = checar_ult_ano_completo(df_mes)
        exp_mun_ano_completo = df_ano[
            (df_ano["municipio"] == municipio_interesse)
            & (df_ano["ano"] == ano_completo)
        ]["total_exp_anual"].sum()

        tx_var_ano_completo = df_ano[
            (df_ano["municipio"] == municipio_interesse)
            & (df_ano["ano"] == ano_completo)
        ]["perc_var_ano_anterior"].sum()

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
def prepara_dados_graficos_comex(df_filtrado, anos_de_interesse):
    """
    Recebe um DataFrame de comex filtrado e retorna todos os DataFrames pivotados
    e o último ano/mês para os títulos dos gráficos.
    """

    ult_ano_comex, ult_mes_comex = None, None
    df_comex_hist, df_comex_hist_perc, df_comex_acum, df_comex_ano = (
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
        pd.DataFrame(),
    )

    if not df_filtrado.empty:
        ult_ano_comex = df_filtrado["ano"].max()
        ult_mes_comex = df_filtrado[df_filtrado["ano"] == ult_ano_comex]["mes"].max()

        # Histórico Mensal - Valor
        df_comex_hist = (
            df_filtrado.assign(
                date=lambda x: pd.to_datetime(
                    x["ano"].astype(str)
                    + "-"
                    + x["mes"].astype(str).str.zfill(2)
                    + "-01"
                ),
                exp_milhoes=lambda x: x["total_exp_mensal"] / 1_000_000,
            )
            .pivot_table(
                index="date",
                columns="municipio",
                values="exp_milhoes",
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
            .apply(lambda x: x.round(2))
        )
        # Historico Mensal - Percentual
        df_comex_hist_perc = (
            df_filtrado.assign(
                date=lambda x: pd.to_datetime(
                    x["ano"].astype(str)
                    + "-"
                    + x["mes"].astype(str).str.zfill(2)
                    + "-01"
                ),
            )
            .pivot_table(
                index="date",
                columns="municipio",
                values="perc_var_mes_ano_anterior",
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
            .apply(lambda x: x.round(2))
        )

        # Acumulado no Ano
        df_comex_acum = (
            df_filtrado[df_filtrado["mes"] <= ult_mes_comex]
            .assign(exp_milhoes=lambda x: x["total_exp_acumulado"] / 1_000_000)
            .pivot_table(
                index="ano",
                columns="municipio",
                values="exp_milhoes",
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
        )

        # Anual
        ano_completo_comex = checar_ult_ano_completo(df_filtrado)
        df_comex_ano = (
            df_filtrado[df_filtrado["ano"] <= ano_completo_comex]
            .assign(exp_milhoes=lambda x: x["total_exp_mensal"] / 1_000_000)
            .pivot_table(
                index="ano",
                columns="municipio",
                values="exp_milhoes",
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
        )

    return (
        df_comex_hist,
        df_comex_hist_perc,
        df_comex_acum,
        df_comex_ano,
        ult_ano_comex,
        ult_mes_comex,
    )


def display_comex_municipios_expander(df_mes):
    """Exibe o expander com análise de exportações para múltiplos municípios."""
    with st.expander("Comércio Exterior por Município", expanded=False):
        tab_hist, tab_acum, tab_anual = st.tabs(
            ["Histórico Mensal", "Acumulado no Ano", "Anual"],
        )

        df_filtrado = df_mes[(df_mes["ano"].isin(anos_de_interesse))]

        (
            df_comex_hist,
            df_comex_hist_perc,
            df_comex_acum,
            df_comex_ano,
            ult_ano_comex,
            ult_mes_comex,
        ) = prepara_dados_graficos_comex(df_filtrado, anos_de_interesse)

        anos_disponiveis = sorted(df_filtrado["ano"].unique().tolist(), reverse=True)

        with tab_hist:
            col1, col2 = st.columns([0.5, 0.5])
            with col1:
                ANO_SELECIONADO = st.selectbox(
                    "Selecione o ano para o gráfico:",
                    options=anos_disponiveis,
                    index=0,
                    key="hist_ano_comex",
                )

            df_comex_hist_filtrado_ano = df_comex_hist[
                df_comex_hist.index.year == ANO_SELECIONADO
            ]

            if not df_comex_hist_filtrado_ano.empty:
                df_comex_hist_filtrado_ano.index = [
                    f"{MESES_DIC[date.month][:3]}/{str(date.year)[2:]}"
                    for date in df_comex_hist_filtrado_ano.index
                ]

            df_comex_hist_perc_filtrado_ano = df_comex_hist_perc[
                df_comex_hist_perc.index.year == ANO_SELECIONADO
            ]

            if not df_comex_hist_perc_filtrado_ano.empty:
                df_comex_hist_perc_filtrado_ano.index = [
                    f"{MESES_DIC[date.month][:3]}/{str(date.year)[2:]}"
                    for date in df_comex_hist_perc_filtrado_ano.index
                ]

            if not ANO_SELECIONADO:
                st.warning("Por favor, selecione ao menos um ano.")

            fig_hist = criar_grafico_barras(
                df=df_comex_hist_filtrado_ano,
                titulo="",
                label_y="(Milhões de US$)",
                barmode="group",
                height=400,
                data_label_format=",.1f",
                hover_label_format=",.2f",
                color_map=CORES_MUNICIPIOS,
            )

            fig_hist_perc = criar_grafico_barras(
                df=df_comex_hist_perc_filtrado_ano,
                titulo="",
                label_y="Variação em relação ao mesmo mês do ano anterior (%)",
                barmode="group",
                height=400,
                data_label_format=",.1f",
                hover_label_format=",.2f",
                color_map=CORES_MUNICIPIOS,
            )

            with col2:
                view_mode = st.radio(
                    "Selecione o modo de Visualização:",
                    options=["Valor (Milhões de US$)", "Variação Anual (%)"],
                    horizontal=True,
                    key="view_mode_comex_municipios_hist",
                )

            if view_mode == "Valor (Milhões de US$)":
                titulo_centralizado(f"Exportações em {ANO_SELECIONADO}", 5)
                st.plotly_chart(fig_hist, width="stretch")

            elif view_mode == "Variação Anual (%)":
                if fig_hist_perc:
                    titulo_centralizado(
                        f"Variação Percentual Anual das Exportações em {ANO_SELECIONADO}",
                        5,
                    )

                    st.plotly_chart(fig_hist_perc, use_container_width=True)
                else:
                    st.warning("Nenhum dado disponível para o gráfico.")

        with tab_acum:
            df_comex_acum.index = (
                "Jan-"
                + MESES_DIC[ult_mes_comex][:3]
                + "/"
                + df_comex_acum.index.astype(str).str.slice(-2)
            )
            fig_acum = criar_grafico_barras(
                df=df_comex_acum,
                titulo="",
                label_y="(Milhões de US$)",
                barmode="group",
                height=400,
                data_label_format=",.1f",
                hover_label_format=",.2f",
                color_map=CORES_MUNICIPIOS,
            )
            titulo_centralizado(
                f"Exportações de Janeiro a {MESES_DIC[ult_mes_comex]}", 5
            )
            st.plotly_chart(fig_acum, width="stretch")

        with tab_anual:
            fig_anual = criar_grafico_barras(
                df=df_comex_ano,
                titulo="",
                label_y="(Milhões de US$)",
                barmode="group",
                height=400,
                data_label_format=",.1f",
                hover_label_format=",.2f",
                color_map=CORES_MUNICIPIOS,
            )
            titulo_centralizado("Exportações Anuais", 5)
            st.plotly_chart(fig_anual, width="stretch")


@st.cache_data
def preparar_dados_comex_produto_pais(df, anos_selecionados, tipo_agg):
    """
    Função cacheada e genérica para preparar os dados para as abas de Comex.
    'tipo_agg' pode ser 'pais', 'produto', ou 'pais_produto'.
    """
    if not anos_selecionados:
        return pd.DataFrame()

    df_filtrado = df[df["ano"].isin(anos_selecionados)]

    if tipo_agg == "pais":
        return criar_tabela_comex(df_filtrado, ["pais"], ["País"], anos_selecionados)

    if tipo_agg == "produto":
        return criar_tabela_comex(
            df_filtrado, ["produto"], ["Produto"], anos_selecionados
        )

    if tipo_agg == "pais_produto":
        return criar_tabela_comex(
            df_filtrado, ["pais", "produto"], ["País", "Produto"], anos_selecionados
        )

    return pd.DataFrame()


@st.cache_data
def preparar_grafico_comex(df_filtrado_exibicao):
    """
    Recebe o DataFrame já filtrado pela UI e retorna a figura do gráfico cacheada.
    """
    if df_filtrado_exibicao.empty:
        return None

    df_grafico = (
        df_filtrado_exibicao.assign(
            date=lambda x: pd.to_datetime(
                x["Ano"].astype(str) + "-" + x["Mês"].astype(str).str.zfill(2) + "-01"
            )
        )
        .pivot_table(
            index="date",
            columns=["País"],
            values="Valor Exportado no Mês (US$)",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
    )
    if not df_grafico.empty:
        df_grafico.index = [
            f"{MESES_DIC[date.month][:3]}/{str(date.year)[2:]}"
            for date in df_grafico.index
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
    """Exibe o expander com análise de exportações por Produto e País do Municipio Selecionado."""
    with st.expander(
        f"Comércio Exterior de {municipio_interesse} por Destino e Produto",
        expanded=False,
    ):
        anos_disponiveis = sorted(df["ano"].unique().tolist(), reverse=True)
        ANOS_SELECIONADOS = st.multiselect(
            "Selecione o(s) ano(s) para a tabela:",
            options=anos_disponiveis,
            default=anos_de_interesse[-1],
            key="anos_comex_pais_multiselect",
        )

        if not ANOS_SELECIONADOS:
            st.warning("Por favor, selecione ao menos um ano.")

        tab_pais, tab_produto, tab_pais_produto = st.tabs(
            ["País", "Produto", "País - Produto"],
        )

        format_dict = {
            "Valor Exportado no Mês (US$)": lambda x: f"{x:,.0f}".replace(",", "."),
            "Valor Acumulado no Ano (US$)": lambda x: f"{x:,.0f}".replace(",", "."),
            "Variação Mês (vs Ano Ant.) (%)": lambda x: f"{x:.1f}%".replace(".", ","),
            "Variação Acum. (vs Ano Ant.) (%)": lambda x: f"{x:.1f}%".replace(".", ","),
        }

        with tab_pais:
            df_comex_pais = preparar_dados_comex_produto_pais(
                df=df,
                anos_selecionados=ANOS_SELECIONADOS,
                tipo_agg="pais",
            )

            paises_options = sorted(df_comex_pais["País"].unique().tolist())

            paises_selecionados_filtro = st.multiselect(
                label="Filtrar a tabela por país (opcional):",
                options=paises_options,
                key="filtro_tabela_comex_pais",
            )

            df_comex_pais_exibir = (
                df_comex_pais[df_comex_pais["País"].isin(paises_selecionados_filtro)]
                if paises_selecionados_filtro
                else df_comex_pais
            )

            st.dataframe(
                df_comex_pais_exibir.style.map(
                    destacar_percentuais,
                    subset=[
                        "Variação Mês (vs Ano Ant.) (%)",
                        "Variação Acum. (vs Ano Ant.) (%)",
                    ],
                ).format(format_dict),
                hide_index=True,
                width="stretch",
            )

        with tab_produto:
            df_comex_produto = preparar_dados_comex_produto_pais(
                df=df, anos_selecionados=ANOS_SELECIONADOS, tipo_agg="produto"
            )

            produtos_options = sorted(df_comex_produto["Produto"].unique().tolist())

            produtos_selecionados_filtro = st.multiselect(
                label="Filtrar a tabela por produto (opcional):",
                options=produtos_options,
                key="filtro_tabela_comex_produto",
            )
            df_comex_produto_exibir = (
                df_comex_produto[
                    df_comex_produto["Produto"].isin(produtos_selecionados_filtro)
                ]
                if produtos_selecionados_filtro
                else df_comex_produto
            )

            st.dataframe(
                df_comex_produto_exibir.style.map(
                    destacar_percentuais,
                    subset=[
                        "Variação Mês (vs Ano Ant.) (%)",
                        "Variação Acum. (vs Ano Ant.) (%)",
                    ],
                ).format(format_dict),
                hide_index=True,
                width="stretch",
            )

        with tab_pais_produto:
            df_comex_pais_produto = preparar_dados_comex_produto_pais(
                df=df, anos_selecionados=ANOS_SELECIONADOS, tipo_agg="pais_produto"
            )

            paises_options = sorted(df_comex_pais_produto["País"].unique().tolist())
            paises_default = (
                df_comex_pais_produto.groupby(["País"], as_index=False)[
                    "Valor Exportado no Mês (US$)"
                ]
                .sum()
                .sort_values(by="Valor Exportado no Mês (US$)", ascending=False)
                .head(3)["País"]
                .tolist()
            )
            paises_selecionados = st.multiselect(
                "Filtrar por País(es):",
                options=paises_options,
                default=paises_default,
                key="filtro_pp_pais",
            )

            if paises_selecionados:
                df_filtrado_temp = df_comex_pais_produto[
                    df_comex_pais_produto["País"].isin(paises_selecionados)
                ]
                produtos_options = sorted(df_filtrado_temp["Produto"].unique().tolist())
            else:
                produtos_options = sorted(
                    df_comex_pais_produto["Produto"].unique().tolist()
                )

            produtos_selecionados = st.multiselect(
                "Filtrar por Produto:",
                options=produtos_options,
                default=produtos_options,
                key="filtro_pp_produto",
            )

            df_pais_produto_exibir = df_comex_pais_produto.copy()
            if paises_selecionados:
                df_pais_produto_exibir = df_pais_produto_exibir[
                    df_pais_produto_exibir["País"].isin(paises_selecionados)
                ]
            if produtos_selecionados:
                df_pais_produto_exibir = df_pais_produto_exibir[
                    df_pais_produto_exibir["Produto"].isin(produtos_selecionados)
                ]

            styled_df = df_pais_produto_exibir.style.map(
                destacar_percentuais,
                subset=[
                    "Variação Mês (vs Ano Ant.) (%)",
                    "Variação Acum. (vs Ano Ant.) (%)",
                ],
            ).format(format_dict)

            fig_pp = preparar_grafico_comex(df_pais_produto_exibir)

            view_mode = st.radio(
                "Selecione o modo de Visualização:",
                options=["Tabela", "Gráfico"],
                horizontal=True,
                label_visibility="collapsed",
                key="view_mode_comex_pp",
            )

            if view_mode == "Tabela":
                st.dataframe(styled_df, hide_index=True, width="stretch")

            elif view_mode == "Gráfico":
                if fig_pp:
                    st.plotly_chart(fig_pp, use_container_width=True)
                else:
                    st.warning("Nenhum dado disponível para o gráfico.")


def show_page_comex(
    df_comex_ano,
    df_comex_mensal,
    df_comex_municipio_raw,
    municipios_selecionados,
    municipio_de_interesse,
):
    """Função principal que renderiza a página de Comércio Exterior."""
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

    display_comex_municipios_expander(
        df_mes=df_comex_mensal,
    )

    display_comex_produto_pais_expander(
        df=df_comex_municipio_filtrado, municipio_interesse=municipio_foco
    )
