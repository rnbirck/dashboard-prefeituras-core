# %%
import pandas as pd
import streamlit as st
import plotly.express as px
from dashboard_core.config import CORES_MUNICIPIOS
from dashboard_core.utils import (
    criar_grafico_linhas,
    criar_grafico_barras,
    titulo_centralizado,
)


@st.cache_data
def preparar_dados_graficos_pib(df_filtrado, coluna_agregacao, coluna_selecionada):
    """Prepara os dados para o gráfico de PIB, garantindo que todos os municípios e anos estejam presentes."""
    if df_filtrado.empty:
        return pd.DataFrame()

    anos = sorted(df_filtrado["ano"].unique())

    if "tx_cresc" in coluna_selecionada:
        anos_validos = df_filtrado.dropna(subset=[coluna_selecionada])["ano"].unique()
        anos = sorted(list(set(anos) & set(anos_validos)))
        if not anos:
            return pd.DataFrame()
        df_filtrado = df_filtrado[df_filtrado["ano"].isin(anos)]

    municipios_selecionados = df_filtrado["municipio"].unique()

    df_grid = pd.MultiIndex.from_product(
        [anos, municipios_selecionados], names=["ano", "municipio"]
    ).to_frame(index=False)

    df_completo = pd.merge(df_grid, df_filtrado, on=["ano", "municipio"], how="left")

    if coluna_selecionada in df_completo.columns:
        df_completo[coluna_selecionada] = df_completo[coluna_selecionada].fillna(0)
    else:
        df_completo[coluna_selecionada] = 0

    df_graf = df_completo.pivot_table(
        index="ano",
        columns=coluna_agregacao,
        values=coluna_selecionada,
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    df_graf.index = df_graf.index.astype(str)

    return df_graf


def display_pib_total_expander(
    df_filtrado, titulo_expander, dicionario_indicadores, key_prefix
):
    """
    Expander modificado para incluir um st.radio para métricas
    (Valor vs Taxa de Crescimento) quando disponível.
    """
    with st.expander(titulo_expander, expanded=False):
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            indicador_selecionado = st.selectbox(
                "Selecione um indicador para visualizar:",
                options=list(dicionario_indicadores.keys()),
                key=f"{key_prefix}_selectbox",
            )

        # Pega o dicionário de métricas para o indicador selecionado
        metricas_disponiveis = dicionario_indicadores[indicador_selecionado]

        metrica_selecionada = "default"
        # Se houver mais de uma métrica (ex: Valor e Taxa), mostra o radio
        with col2:
            if "default" not in metricas_disponiveis:
                metrica_selecionada = st.radio(
                    "Selecione a métrica:",
                    options=list(metricas_disponiveis.keys()),
                    key=f"{key_prefix}_metric_radio",
                    horizontal=True,
                )

        (coluna_selecionada, label_y, data_format, reversed_y, chart_type) = (
            metricas_disponiveis[metrica_selecionada]
        )

        hover_format = (
            f",.{int(data_format.split('.')[-1][0]) + 0}f"
            if "." in data_format
            else ",.0f"
        )

        titulo_grafico = indicador_selecionado
        if metrica_selecionada != "default":
            titulo_grafico = f"{indicador_selecionado} - {metrica_selecionada}"

        titulo_centralizado(titulo_grafico, 5)

        df_grafico = preparar_dados_graficos_pib(
            df_filtrado=df_filtrado,
            coluna_agregacao="municipio",
            coluna_selecionada=coluna_selecionada,
        )

        # --- LÓGICA DE SELEÇÃO DO GRÁFICO ---
        if chart_type == "linha":
            fig = criar_grafico_linhas(
                df=df_grafico,
                titulo="",
                label_y=label_y,
                height=400,
                data_label_format=data_format,
                hover_label_format=hover_format,
                color_map=CORES_MUNICIPIOS,
                reverse_y=reversed_y,
            )
        else:  # "barra"
            fig = criar_grafico_barras(
                df=df_grafico,
                titulo="",
                label_y=label_y,
                height=400,
                data_label_format=data_format,
                hover_label_format=hover_format,
                color_map=CORES_MUNICIPIOS,
            )

        st.plotly_chart(fig, use_container_width=True)


def display_pib_vab_expander(df_filtrado, titulo_expander, vab_map, key_prefix):
    """
    Função modificada para incluir o gráfico de barras empilhadas (Estrutura VAB)
    como a primeira opção.
    """
    with st.expander(titulo_expander, expanded=False):
        opcoes_visualizacao = ["Estrutura VAB por Setor"] + list(vab_map.keys())

        col1, col2 = st.columns([0.5, 0.5])

        with col1:
            visualizacao_selecionada = st.selectbox(
                "Selecione a visualização:",
                options=opcoes_visualizacao,
                key=f"{key_prefix}_setor_selectbox",
            )

        # --- LÓGICA 1: GRÁFICO DE ESTRUTURA (STACKED BAR) ---
        if visualizacao_selecionada == "Estrutura VAB por Setor":
            with col2:
                # Seletor de ano
                anos_disponiveis = sorted(df_filtrado["ano"].unique(), reverse=True)
                ano_selecionado = st.selectbox(
                    "Selecione o ano:",
                    anos_disponiveis,
                    key=f"{key_prefix}_ano_stacked",
                )

            titulo_centralizado(f"Estrutura do VAB por Setor ({ano_selecionado})", 5)

            # Filtra dados para o ano
            df_ano = df_filtrado[df_filtrado["ano"] == ano_selecionado].copy()

            vab_cols_map = {
                "valor_adicionado_bruto_agropecuaria_milhoes": "Agropecuária",
                "valor_adicionado_bruto_industria_milhoes": "Indústria",
                "valor_adicionado_bruto_servicos_milhoes": "Serviços",
                "valor_adicionado_bruto_adm_milhoes": "Administração Pública",
            }

            df_plot = df_ano[["municipio"] + list(vab_cols_map.keys())].copy()

            # Calcula total para ordenação
            df_plot["Total"] = df_plot[list(vab_cols_map.keys())].sum(axis=1)
            df_plot = df_plot.sort_values("Total", ascending=True)
            df_melted = df_plot.melt(
                id_vars="municipio",
                value_vars=list(vab_cols_map.keys()),
                var_name="Setor",
                value_name="Valor (Milhões R$)",
            )

            df_melted["Setor"] = df_melted["Setor"].map(vab_cols_map)

            fig = px.bar(
                df_melted,
                y="municipio",
                x="Valor (Milhões R$)",
                color="Setor",
                barmode="stack",
                orientation="h",
                height=400,
                labels={"municipio": ""},
                title="",
                color_discrete_map={
                    "Administração Pública": "#F5693E",
                    "Serviços": "#AB5CFA",
                    "Indústria": "#319AEA",
                    "Agropecuária": "#74F44D",
                },
            )
            fig.update_layout(
                legend_title_text="",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- LÓGICA 2: GRÁFICOS DE SÉRIE TEMPORAL ---
        else:
            metricas_setor = vab_map[visualizacao_selecionada]

            with col2:
                metrica_selecionada = st.radio(
                    "Selecione a métrica:",
                    options=list(metricas_setor.keys()),
                    key=f"{key_prefix}_metrica_radio",
                    horizontal=True,
                )

            (coluna_selecionada, label_y, data_format, reversed_y, chart_type) = (
                metricas_setor[metrica_selecionada]
            )

            hover_format = (
                f",.{int(data_format.split('.')[-1][0]) + 0}f"
                if "." in data_format
                else ",.0f"
            )

            titulo_centralizado(
                f"VAB - {visualizacao_selecionada} ({metrica_selecionada})",
                5,
            )

            df_grafico = preparar_dados_graficos_pib(
                df_filtrado=df_filtrado,
                coluna_agregacao="municipio",
                coluna_selecionada=coluna_selecionada,
            )

            if df_grafico.empty:
                st.warning(
                    "Não há dados disponíveis para os filtros selecionados (ex: primeiro ano não possui taxa de crescimento)."
                )
                return

            if chart_type == "linha":
                fig = criar_grafico_linhas(
                    df=df_grafico,
                    titulo="",
                    label_y=label_y,
                    height=400,
                    data_label_format=data_format,
                    hover_label_format=hover_format,
                    color_map=CORES_MUNICIPIOS,
                    reverse_y=reversed_y,
                )
            else:  # "barra"
                fig = criar_grafico_barras(
                    df=df_grafico,
                    titulo="",
                    label_y=label_y,
                    height=400,
                    data_label_format=data_format,
                    hover_label_format=hover_format,
                    color_map=CORES_MUNICIPIOS,
                )

            st.plotly_chart(fig, use_container_width=True)


def show_page_pib(df_pib):
    titulo_centralizado("Dashboard do PIB Municipal", 1)
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

    INDICADORES_PIB_TOTAL = {
        "PIB (Milhões R$)": {
            "Valor": ("pib_milhoes", "PIB (Milhões R$)", ",.0f", False, "linha"),
            "Taxa de Crescimento (%)": (
                "tx_cresc_pib_mil",
                "Crescimento (%)",
                ",.1f",
                False,
                "barra",
            ),
        },
        "PIB per Capita (R$)": {
            "Valor": ("pib_per_capita", "PIB per Capita (R$)", ",.0f", False, "linha"),
            "Taxa de Crescimento (%)": (
                "tx_cresc_pib_per_capita",
                "Crescimento (%)",
                ",.1f",
                False,
                "barra",
            ),
        },
        "Participação no PIB do RS (%)": {
            "default": ("percentual_pib_rs", "Participação (%)", ",.2f", False, "linha")
        },
        "Posição no Ranking do PIB do RS": {
            "default": ("posicao_pib_geral", "Posição", ",.0f", True, "linha")
        },
    }

    VAB_MAP = {
        "Agropecuária": {
            "Valor (Milhões R$)": (
                "valor_adicionado_bruto_agropecuaria_milhoes",
                "VAB (Milhões R$)",
                ",.0f",
                False,
                "linha",
            ),
            "Taxa de Crescimento (%)": (
                "tx_cresc_agro_mil",
                "Crescimento (%)",
                ",.1f",
                False,
                "barra",
            ),
            "Posição no Ranking": (
                "posicao_pib_agropecuaria",
                "Posição",
                ",.0f",
                True,
                "linha",
            ),
        },
        "Indústria": {
            "Valor (Milhões R$)": (
                "valor_adicionado_bruto_industria_milhoes",
                "VAB (Milhões R$)",
                ",.0f",
                False,
                "linha",
            ),
            "Taxa de Crescimento (%)": (
                "tx_cresc_industria_mil",
                "Crescimento (%)",
                ",.1f",
                False,
                "barra",
            ),
            "Posição no Ranking": (
                "posicao_pib_industria",
                "Posição",
                ",.0f",
                True,
                "linha",
            ),
        },
        "Serviços": {
            "Valor (Milhões R$)": (
                "valor_adicionado_bruto_servicos_milhoes",
                "VAB (Milhões R$)",
                ",.0f",
                False,
                "linha",
            ),
            "Taxa de Crescimento (%)": (
                "tx_cresc_servicos_mil",
                "Crescimento (%)",
                ",.1f",
                False,
                "barra",
            ),
            "Posição no Ranking": (
                "posicao_pib_servico",
                "Posição",
                ",.0f",
                True,
                "linha",
            ),
        },
        "Administração Pública": {
            "Valor (Milhões R$)": (
                "valor_adicionado_bruto_adm_milhoes",
                "VAB (Milhões R$)",
                ",.0f",
                False,
                "linha",
            ),
            "Taxa de Crescimento (%)": (
                "tx_cresc_adm_mil",
                "Crescimento (%)",
                ",.1f",
                False,
                "barra",
            ),
            "Posição no Ranking": (
                "posicao_pib_adm_publica",
                "Posição",
                ",.0f",
                True,
                "linha",
            ),
        },
    }
    display_pib_total_expander(
        df_filtrado=df_pib,
        titulo_expander="Indicadores do PIB Municipal",
        dicionario_indicadores=INDICADORES_PIB_TOTAL,
        key_prefix="pib_total",
    )

    display_pib_vab_expander(
        df_filtrado=df_pib,
        titulo_expander="Valor Adicionado Bruto (VAB) por Setor",
        vab_map=VAB_MAP,
        key_prefix="pib_VAB",
    )
