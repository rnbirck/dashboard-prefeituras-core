import streamlit as st
import pandas as pd

from dashboard_core.utils import (
    MESES_DIC,
    titulo_centralizado,
    calcular_yoy,
    filtrar_municipio_ult_mes_ano,
    criar_grafico_barras,
    preparar_dados_graficos_anuais,
)

municipio_de_interesse = None
CORES_MUNICIPIOS = {}
ordem_tamanho_estabelecimentos = []


def set_empresas_config(municipio, cores_municipios, ordem):
    """
    Injeta a configuração específica do município para as views de empresas.
    Chamar no app.py antes de renderizar a página de empresas.

    Parâmetros:
      - municipio: str -> nome do município de interesse
      - cores_municipios: dict -> mapa de cores por município
      - kwargs: dicionário para configurações extras (opcional)
    """
    global municipio_de_interesse, CORES_MUNICIPIOS, ordem_tamanho_estabelecimentos
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}
    ordem_tamanho_estabelecimentos = ordem or []


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
def preparar_dados_grafico_empresas_ativas(df, df_cnae, df_cnae_saldo):
    df_graf_total = pd.DataFrame()
    df_graf_setor = pd.DataFrame()
    df_tab_cnae = pd.DataFrame()
    df_tab_cnae_saldo = pd.DataFrame()

    df_graf_total = (
        df.assign(
            date=lambda x: pd.to_datetime(
                x["ano"].astype(str) + "-" + x["mes"].astype(str).str.zfill(2) + "-01"
            )
        )
        .pivot_table(
            index="date",
            columns="municipio",
            values="empresas_ativas",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
    )

    df_graf_setor = (
        df_cnae.assign(
            date=lambda x: pd.to_datetime(
                x["ano"].astype(str) + "-" + x["mes"].astype(str).str.zfill(2) + "-01"
            )
        )
        .pivot_table(
            index="date",
            columns="grupo_ibge",
            values="empresas_ativas",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
    )

    ult_ano = df_cnae["ano"].max()
    ult_mes = df_cnae[df_cnae["ano"] == ult_ano]["mes"].max()
    date_sort = pd.to_datetime(f"{ult_ano}-{ult_mes:02d}-01")

    df_tab_cnae = (
        df_cnae.assign(
            date=lambda x: pd.to_datetime(
                x["ano"].astype(str) + "-" + x["mes"].astype(str).str.zfill(2) + "-01"
            )
        )
        .pivot_table(
            index="grupo",
            columns="date",
            values="empresas_ativas",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_values(by=date_sort, ascending=False)
    )

    novos_nomes_colunas = [
        f"{MESES_DIC[data.month][:3]}/{str(data.year)[-2:]}"
        for data in df_tab_cnae.columns
    ]

    df_tab_cnae.columns = novos_nomes_colunas
    df_tab_cnae.index.name = "CNAE - Grupo"

    df_tab_cnae_saldo = (
        df_cnae_saldo.assign(
            date=lambda x: pd.to_datetime(
                x["ano"].astype(str) + "-" + x["mes"].astype(str).str.zfill(2) + "-01"
            )
        )
        .pivot_table(
            index="grupo",
            columns="date",
            values="saldo_empresas",
            aggfunc="sum",
            fill_value=0,
        )
        .sort_values(by=date_sort, ascending=False)
    )

    novos_nomes_colunas = [
        f"{MESES_DIC[data.month][:3]}/{str(data.year)[-2:]}"
        for data in df_tab_cnae_saldo.columns
    ]

    df_tab_cnae_saldo.columns = novos_nomes_colunas
    df_tab_cnae_saldo.index.name = "CNAE - Grupo"

    return df_graf_total, df_graf_setor, df_tab_cnae, df_tab_cnae_saldo


def display_empresas_ativas_expander(
    df, df_cnae, df_cnae_saldo, titulo_expander, key_prefix
):
    with st.expander(f"{titulo_expander}", expanded=False):
        df_graf_total, df_graf_cnae, df_tab_cnae, df_tab_cnae_saldo = (
            preparar_dados_grafico_empresas_ativas(
                df=df, df_cnae=df_cnae, df_cnae_saldo=df_cnae_saldo
            )
        )

        anos_disponiveis = sorted(df["ano"].unique().tolist(), reverse=True)
        col1, col2 = st.columns(2)
        with col1:
            if not anos_disponiveis:
                st.warning("Nenhum dado disponível para os filtros selecionados.")
            else:
                ANO_SELECIONADO = st.selectbox(
                    "Selecione o ano para o gráfico:",
                    options=anos_disponiveis,
                    index=0,
                    key=f"selecionar_ano_{key_prefix}",
                )
        tab_total, tab_setor, tab_cnae = st.tabs(
            [f"{titulo_expander} por Município", "Setor", "CNAE"]
        )
        df_graf_total_anos = df_graf_total[df_graf_total.index.year == ANO_SELECIONADO]
        df_graf_total_anos.index = [
            f"{MESES_DIC[date.month][:3]}/{str(date.year)[2:]}"
            for date in df_graf_total_anos.index
        ]

        df_graf_cnae_anos = df_graf_cnae[df_graf_cnae.index.year == ANO_SELECIONADO]
        df_graf_cnae_anos.index = [
            f"{MESES_DIC[date.month][:3]}/{str(date.year)[2:]}"
            for date in df_graf_cnae_anos.index
        ]

        with tab_total:
            titulo_centralizado(
                f"Quantidade de {titulo_expander} em {ANO_SELECIONADO}", 5
            )
            fig_total = criar_grafico_barras(
                df=df_graf_total_anos,
                titulo="",
                label_y="Quantidade de Empresas Ativas",
                barmode="group",
                height=400,
                data_label_format=",.0f",
                hover_label_format=",.0f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig_total, width="stretch")

        with tab_setor:
            titulo_centralizado(
                f"{titulo_expander} por Setor em {municipio_de_interesse} - {ANO_SELECIONADO}",
                5,
            )
            fig_setor = criar_grafico_barras(
                df=df_graf_cnae_anos,
                titulo="",
                label_y="Quantidade de Empresas Ativas",
                barmode="stack",
                height=400,
                data_label_format=",.0f",
                hover_label_format=",.0f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig_setor, width="stretch")

        with tab_cnae:
            view_mode = st.radio(
                "Selecione a Análise:",
                options=["Estoque", "Saldo"],
                horizontal=True,
                label_visibility="collapsed",
                key=f"view_mode_cnae_{key_prefix}",
            )
            if view_mode == "Estoque":
                colunas_do_ano = [
                    col
                    for col in df_tab_cnae.columns
                    if col.endswith(f"/{str(ANO_SELECIONADO)[-2:]}")
                ]
                df_tab_cnae_filtrada = df_tab_cnae[colunas_do_ano]

                titulo_centralizado(
                    f"Estoque de {titulo_expander} por CNAE em {municipio_de_interesse} - {ANO_SELECIONADO}",
                    5,
                )

                tab_cnae = df_tab_cnae_filtrada.style.format(
                    lambda x: f"{x:,.0f}".replace(",", ".")
                ).background_gradient(cmap="GnBu")
                st.dataframe(tab_cnae, width="stretch")

            if view_mode == "Saldo":
                colunas_do_ano = [
                    col
                    for col in df_tab_cnae_saldo.columns
                    if col.endswith(f"/{str(ANO_SELECIONADO)[-2:]}")
                ]
                df_tab_cnae_saldo_filtrada = df_tab_cnae_saldo[colunas_do_ano]

                titulo_centralizado(
                    f"Saldo de {titulo_expander} por CNAE em {municipio_de_interesse} - {ANO_SELECIONADO}",
                    5,
                )

                tab_cnae = df_tab_cnae_saldo_filtrada.style.format(
                    lambda x: f"{x:,.0f}".replace(",", ".")
                ).background_gradient(cmap="coolwarm_r", axis=0)
                st.dataframe(tab_cnae, width="stretch")


def render_estabelecimentos_grafico_tab(
    df, coluna_agregacao, titulo_grafico, color_map=None, reorder_cols=None
):
    """
    Função auxiliar para renderizar uma aba de Estabelecimentos com gráfico.
    """
    titulo_centralizado(titulo_grafico, 5)

    df_grafico = preparar_dados_graficos_anuais(
        df_filtrado=df,
        coluna_agregacao=coluna_agregacao,
        coluna_valores="qntd_estabelecimentos",
    )

    if reorder_cols and not df_grafico.empty:
        df_grafico = df_grafico.reindex(columns=reorder_cols, fill_value=0)

    fig = criar_grafico_barras(
        df=df_grafico,
        titulo="",
        label_y="Nº de Estabelecimentos",
        color_map=color_map,
        data_label_format=",.0f",
        hover_label_format=",.0f",
    )
    st.plotly_chart(fig, width="stretch")


def render_estabelecimentos_tabela_tab(df, index_col, titulo, municipio_interesse):
    """
    Função auxiliar para renderizar uma aba de Estabelecimentos com tabela (CNAE).
    """
    titulo_centralizado(f"{titulo} em {municipio_interesse}", 5)

    ult_ano = df["ano"].max()

    df_agrupado = (
        df.groupby(["ano", index_col])["qntd_estabelecimentos"].sum().reset_index()
    )

    df_pivot = df_agrupado.pivot_table(
        index=index_col,
        columns="ano",
        values="qntd_estabelecimentos",
        aggfunc="sum",
        fill_value=0,
    ).sort_values(by=ult_ano, ascending=False)

    df_pivot.index.name = titulo.split(" por ")[-1]  # Ex: "CNAE - Grupo"

    st.dataframe(
        df_pivot.style.format("{:,.0f}").background_gradient(cmap="GnBu"),
        width="stretch",
    )


def display_estabelecimentos(
    df_estabelecimentos_mun,
    df_estabelecimentos_cnae,
    df_estabelecimentos_tamanho,
    municipio_interesse,
    color_map=None,
):
    """Exibe o expander com a análise de Estabelecimentos."""
    with st.expander("Estabelecimentos", expanded=False):
        tabs = st.tabs(
            ["Município", "Tamanho", "Setor", "CNAE - Grupo", "CNAE - Subclasse"]
        )

        # Aba 0: Comparativo entre Municípios
        with tabs[0]:
            render_estabelecimentos_grafico_tab(
                df=df_estabelecimentos_mun,
                coluna_agregacao="municipio",
                titulo_grafico="Quantidade de Estabelecimentos por Município",
                color_map=color_map,
            )

        # Aba 1: Análise por Tamanho do Estabelecimento
        with tabs[1]:
            render_estabelecimentos_grafico_tab(
                df=df_estabelecimentos_tamanho,
                coluna_agregacao="tamanho_estabelecimento",
                titulo_grafico=f"Quantidade de Estabelecimentos por Número de Funcionários em {municipio_interesse}",
                reorder_cols=ordem_tamanho_estabelecimentos,
            )

        # Aba 2: Análise por Setor Econômico
        with tabs[2]:
            render_estabelecimentos_grafico_tab(
                df=df_estabelecimentos_cnae,
                coluna_agregacao="grupo_ibge",
                titulo_grafico=f"Quantidade de Estabelecimentos por Setor em {municipio_interesse}",
            )

        # Aba 3: Tabela por CNAE - Grupo
        with tabs[3]:
            render_estabelecimentos_tabela_tab(
                df=df_estabelecimentos_cnae,
                index_col="grupo",
                titulo="Quantidade de Estabelecimentos por CNAE - Grupo",
                municipio_interesse=municipio_interesse,
            )

        # Aba 4: Tabela por CNAE - Subclasse
        with tabs[4]:
            render_estabelecimentos_tabela_tab(
                df=df_estabelecimentos_cnae,
                index_col="subclasse",
                titulo="Quantidade de Estabelecimentos por CNAE - Subclasse",
                municipio_interesse=municipio_interesse,
            )


def show_page_empresas_ativas(
    df_cnpj,
    df_cnpj_cnae,
    df_cnpj_cnae_saldo,
    df_mei,
    df_mei_cnae,
    df_mei_cnae_saldo,
    municipio_de_interesse,
    df_estabelecimentos_mun,
    df_estabelecimentos_cnae,
    df_estabelecimentos_tamanho,
):
    titulo_centralizado("Dashboard de Empresas Ativas", 1)

    display_cnpj_kpi_cards(
        df_cnpj=df_cnpj, df_mei=df_mei, municipio_de_interesse=municipio_de_interesse
    )
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)
    display_empresas_ativas_expander(
        df=df_cnpj,
        df_cnae=df_cnpj_cnae,
        df_cnae_saldo=df_cnpj_cnae_saldo,
        titulo_expander="CNPJ Ativos",
        key_prefix="cnpj_ativos",
    )
    display_empresas_ativas_expander(
        df=df_mei,
        df_cnae=df_mei_cnae,
        df_cnae_saldo=df_mei_cnae_saldo,
        titulo_expander="MEI Ativos",
        key_prefix="mei_ativos",
    )
    st.markdown("###### Dados disponibilizados pela RAIS - Atualização Anual")
    display_estabelecimentos(
        df_estabelecimentos_mun=df_estabelecimentos_mun,
        df_estabelecimentos_cnae=df_estabelecimentos_cnae,
        df_estabelecimentos_tamanho=df_estabelecimentos_tamanho,
        municipio_interesse=municipio_de_interesse,
        color_map=CORES_MUNICIPIOS,
    )
