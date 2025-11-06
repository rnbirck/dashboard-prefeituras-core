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
)

CORES_MUNICIPIOS = {}


def set_seguranca_config(cores_municipios):
    """
    Configura valores específicos do município que antes eram importados
    do dashboard_core.config. Deve ser chamado pelo app.py antes de
    renderizar a página de seguranca.
    """
    global CORES_MUNICIPIOS
    CORES_MUNICIPIOS = cores_municipios or {}


# ==============================================================================
# FUNÇÕES DA PÁGINA DE SEGURANÇA
# ==============================================================================


@st.cache_data
def preparar_dados_graficos_seguranca(df_filtrado, coluna_selecionada, is_taxa=False):
    """
    Prepara os DataFrames pivotados para as abas da página de segurança.

    """
    df_hist, df_acum, df_anual = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ult_ano, ult_mes = None, None

    # Define o nome da coluna de valor com base no tipo de dado (absoluto ou taxa)
    coluna_valor = f"taxa_{coluna_selecionada}" if is_taxa else coluna_selecionada

    if not df_filtrado.empty and coluna_valor in df_filtrado.columns:
        ult_ano = df_filtrado["ano"].max()
        ult_mes = df_filtrado[df_filtrado["ano"] == ult_ano]["mes"].max()

        # Histórico Mensal
        df_hist = (
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

        # Acumulado no Ano
        df_acum_temp = df_filtrado[df_filtrado["mes"] <= ult_mes]
        df_acum = df_acum_temp.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_valor,
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        # Anual
        ano_completo = checar_ult_ano_completo(df_filtrado)
        df_anual_temp = df_filtrado[df_filtrado["ano"] <= ano_completo]
        df_anual = df_anual_temp.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_valor,
            aggfunc="sum",
            fill_value=0,
        ).sort_index(ascending=False)

    return df_hist, df_acum, df_anual, ult_ano, ult_mes


def display_secao_seguranca(
    df_seguranca,
    df_seguranca_taxa,
    titulo_expander,
    dicionario_indicadores,
    key_prefix,
    label_taxa="Taxa por 10 mil hab.",
):
    """Função genérica para exibir uma seção de indicadores de segurança com opção de taxa."""
    with st.expander(titulo_expander, expanded=False):
        # --- WIDGETS DE FILTRO ---
        col1, col2 = st.columns([0.6, 0.4])

        with col1:
            indicador_selecionado = st.selectbox(
                "Selecione um indicador:",
                options=list(dicionario_indicadores.keys()),
                key=f"{key_prefix}_selectbox",
            )
        coluna_selecionada = dicionario_indicadores[indicador_selecionado]

        # --- BOTÕES PARA ALTERNAR VISUALIZAÇÃO ---
        with col2:
            view_mode = st.radio(
                "Visualizar por:",
                options=["Número de Ocorrências", label_taxa],
                horizontal=True,
                key=f"view_mode_{key_prefix}",
            )

        # --- PREPARAÇÃO DOS DADOS COM BASE NA ESCOLHA DO USUÁRIO ---
        is_taxa = view_mode == label_taxa
        df_ativo = df_seguranca_taxa if is_taxa else df_seguranca
        label_y_grafico = label_taxa if is_taxa else "Ocorrências"
        data_label_format = ",.1f" if is_taxa else ",.0f"
        hover_label_format = ",.2f" if is_taxa else ",.0f"

        df_hist, df_acum, df_anual, ult_ano, ult_mes = (
            preparar_dados_graficos_seguranca(df_ativo, coluna_selecionada, is_taxa)
        )

        anos_disponiveis = sorted(df_ativo["ano"].unique().tolist(), reverse=True)

        # --- RENDERIZAÇÃO DAS ABAS ---
        tab_hist, tab_acum, tab_anual = st.tabs(
            ["Histórico Mensal", "Acumulado no Ano", "Anual"]
        )

        with tab_hist:
            if not anos_disponiveis:
                st.warning("Nenhum dado disponível para os filtros selecionados.")
            else:
                ANO_SELECIONADO = st.selectbox(
                    "Selecione o ano para o gráfico:",
                    options=anos_disponiveis,
                    index=0,
                    key=f"{key_prefix}_hist_ano",
                )
                titulo_centralizado(
                    f"{indicador_selecionado} - Histórico Mensal em {ANO_SELECIONADO}",
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
                    label_y=label_y_grafico,
                    barmode="group",
                    height=400,
                    data_label_format=data_label_format,
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format=hover_label_format,
                )
                st.plotly_chart(fig, use_container_width=True)

        if ult_mes:
            with tab_acum:
                df_acum.index = (
                    "Jan-"
                    + MESES_DIC[ult_mes][:3]
                    + "/"
                    + df_acum.index.astype(str).str.slice(-2)
                )
                titulo_centralizado(
                    f"{indicador_selecionado} - Acumulado de Janeiro a {MESES_DIC[ult_mes]}",
                    5,
                )

                fig = criar_grafico_barras(
                    df=df_acum,
                    titulo="",
                    label_y=label_y_grafico,
                    barmode="group",
                    height=400,
                    data_label_format=data_label_format,
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format=hover_label_format,
                )
                st.plotly_chart(fig, use_container_width=True)

        with tab_anual:
            titulo_centralizado(f"Total Anual - {indicador_selecionado}", 5)
            fig = criar_grafico_barras(
                df=df_anual,
                titulo="",
                label_y=label_y_grafico,
                barmode="group",
                height=400,
                data_label_format=data_label_format,
                color_map=CORES_MUNICIPIOS,
                hover_label_format=hover_label_format,
            )
            st.plotly_chart(fig, use_container_width=True)


def show_page_seguranca(df_seguranca, df_seguranca_taxa):
    titulo_centralizado("Dashboard de Segurança", 1)
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)
    # Dicionário de Indicadores Gerais
    INDICADORES_GERAIS = {
        "Homicídio Doloso": "homicidio_doloso",
        "Furtos": "furtos",
        "Roubos": "roubos",
        "Furto de Veículo": "furto_veiculo",
        "Roubo de Veículo": "roubo_veiculo",
        "Estelionato": "estelionato",
    }

    # Dicionário de Violência Contra a Mulher
    INDICADORES_VIOLENCIA_MULHER = {
        "Feminicídio Consumado": "feminicidio_consumado",
        "Feminicídio Tentado": "feminicidio_tentado",
        "Ameaça": "ameaca",
        "Estupro": "estupro",
        "Lesão Corporal": "lesao_corporal",
    }

    # Dicionário de Drogas e Armas
    INDICADORES_DROGAS_ARMAS = {
        "Delitos com Armas e Munições": "delitos_armas_municoes",
        "Posse de Entorpecentes": "entorpecentes_posse",
        "Tráfico de Entorpecentes": "entorpecentes_trafico",
    }

    # Chama a função de display para cada seção
    display_secao_seguranca(
        df_seguranca,
        df_seguranca_taxa,
        "Indicadores Gerais",
        INDICADORES_GERAIS,
        "geral",
    )
    display_secao_seguranca(
        df_seguranca,
        df_seguranca_taxa,
        "Violência Contra a Mulher",
        INDICADORES_VIOLENCIA_MULHER,
        "mulher",
        label_taxa="Taxa por 10 mil mulheres",
    )
    display_secao_seguranca(
        df_seguranca,
        df_seguranca_taxa,
        "Crimes Relacionados à Drogas e Armas",
        INDICADORES_DROGAS_ARMAS,
        "drogas",
    )
