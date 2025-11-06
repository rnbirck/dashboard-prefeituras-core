import pandas as pd
import streamlit as st
import plotly.express as px
from dashboard_core.utils import (
    criar_grafico_barras,
    titulo_centralizado,
)

municipio_de_interesse = None
CORES_MUNICIPIOS = {}


def set_demografia_config(municipio, cores_municipios):
    """
    Configura valores específicos do município que antes eram importados
    do dashboard_core.config. Deve ser chamado pelo app.py antes de
    renderizar a página de demografia.
    """
    global municipio_de_interesse, CORES_MUNICIPIOS
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}


@st.cache_data
def preparar_dados_graficos_populacao_densidade(df_filtrado, coluna_selecionada):
    df_anual = df_filtrado.pivot_table(
        index="ano",
        columns="municipio",
        values=coluna_selecionada,
        aggfunc="sum",
        fill_value=0,
    ).sort_index(ascending=False)

    return df_anual


@st.cache_data
def preparar_dados_grafico_sexo_proporcao(df_filtrado_sexo, ano_selecionado):
    """Prepara os dados para o gráfico de proporção por sexo para um ano específico."""
    if df_filtrado_sexo.empty:
        return pd.DataFrame()

    df_ano = df_filtrado_sexo[df_filtrado_sexo["ano"] == ano_selecionado].copy()
    if df_ano.empty:
        return pd.DataFrame()

    df_sexo_agg = (
        df_ano.groupby(["municipio", "sexo"])["pop_estimada"].sum().reset_index()
    )

    df_total_pop = (
        df_sexo_agg.groupby("municipio")["pop_estimada"]
        .sum()
        .reset_index()
        .rename(columns={"pop_estimada": "pop_total"})
    )

    df_merged = pd.merge(df_sexo_agg, df_total_pop, on="municipio")
    df_merged["Proporção (%)"] = (
        df_merged["pop_estimada"] / df_merged["pop_total"]
    ) * 100

    df_pivot = df_merged.pivot_table(
        index="municipio", columns="sexo", values="Proporção (%)", fill_value=0
    )

    if "Feminino" in df_pivot.columns:
        df_pivot = df_pivot.sort_values(by="Feminino", ascending=False)

    return df_pivot


@st.cache_data
def preparar_dados_grafico_piramide_etaria(
    df_filtrado_sexo, municipio_de_interesse, ano_selecionado
):
    """Prepara os dados para o gráfico de pirâmide etária."""
    if df_filtrado_sexo.empty:
        return pd.DataFrame()

    # Filtra para o município e ano selecionados
    df_ano = df_filtrado_sexo[
        (df_filtrado_sexo["municipio"] == municipio_de_interesse)
        & (df_filtrado_sexo["ano"] == ano_selecionado)
    ].copy()

    if df_ano.empty:
        return pd.DataFrame()

    # Calcula a população total para esse ano/município
    pop_total = df_ano["pop_estimada"].sum()
    if pop_total == 0:
        return pd.DataFrame()

    # Agrupa por faixa etária E sexo
    df_grouped = (
        df_ano.groupby(["faixa_etaria", "sexo"])["pop_estimada"].sum().reset_index()
    )

    # Calcula a proporção de cada grupo
    df_grouped["proporcao"] = (df_grouped["pop_estimada"] / pop_total) * 100

    # Multiplica por -1 para o gráfico (lado esquerdo)
    df_grouped.loc[df_grouped["sexo"] == "Masculino", "proporcao"] *= -1

    return df_grouped


def display_populacao_densidade_expander(df_filtrado, df_filtrado_sexo):
    tab_populacao, tab_sexo, tab_densidade = st.tabs(
        ["População Estimada", "Sexo", "Densidade Demográfica"]
    )

    with tab_populacao:
        titulo_centralizado("População Estimada", 5)

        df_populacao_estimada = preparar_dados_graficos_populacao_densidade(
            df_filtrado=df_filtrado, coluna_selecionada="pop_estimada"
        )
        fig = criar_grafico_barras(
            df=df_populacao_estimada,
            titulo="",
            label_y="População Estimada",
            barmode="group",
            height=400,
            data_label_format=",.0f",
            hover_label_format=",.0f",
            color_map=CORES_MUNICIPIOS,
        )
        st.plotly_chart(fig, width="stretch")

    with tab_sexo:
        CORES_SEXO = {"Masculino": "#4C82F7", "Feminino": "#FF6BE1"}

        anos_disponiveis = sorted(
            df_filtrado_sexo["ano"].unique().tolist(), reverse=True
        )

        ano_selecionado_sexo = st.selectbox(
            "Selecione o ano para visualizar a proporção por sexo:",
            options=anos_disponiveis,
            key="selectbox_ano_sexo",
        )

        titulo_centralizado(
            f"Proporção da População por Sexo ({ano_selecionado_sexo})", 5
        )

        df_sexo_grafico = preparar_dados_grafico_sexo_proporcao(
            df_filtrado_sexo, ano_selecionado_sexo
        )

        fig_sexo = criar_grafico_barras(
            df=df_sexo_grafico,
            titulo="",
            label_y="Proporção (%)",
            barmode="group",
            height=400,
            data_label_format=",.1f",
            hover_label_format=",.1f",
            color_map=CORES_SEXO,
        )
        st.plotly_chart(fig_sexo, use_container_width=True)

    with tab_densidade:
        titulo_centralizado("Densidade Demográfica", 5)

        df_densidade_demografica = preparar_dados_graficos_populacao_densidade(
            df_filtrado=df_filtrado, coluna_selecionada="densidade_demografica"
        )
        fig = criar_grafico_barras(
            df=df_densidade_demografica,
            titulo="",
            label_y="Habitantes/Km²",
            barmode="group",
            height=400,
            data_label_format=",.0f",
            hover_label_format=",.0f",
            color_map=CORES_MUNICIPIOS,
        )
        st.plotly_chart(fig, width="stretch")


def display_populacao_piramide_etaria_expander(df_filtrado_sexo, municipio_interesse):
    anos_disponiveis = sorted(
        df_filtrado_sexo[df_filtrado_sexo["municipio"] == municipio_interesse]["ano"]
        .unique()
        .tolist(),
        reverse=True,
    )

    if not anos_disponiveis:
        st.warning(f"Não há dados de faixa etária para {municipio_interesse}.")
        return

    ano_selecionado = st.selectbox(
        "Selecione o ano para a pirâmide etária:",
        options=anos_disponiveis,
        key="selectbox_ano_piramide",
    )

    df_plot = preparar_dados_grafico_piramide_etaria(
        df_filtrado_sexo=df_filtrado_sexo,
        municipio_de_interesse=municipio_interesse,
        ano_selecionado=ano_selecionado,
    )

    if df_plot.empty:
        st.warning(f"Não há dados para {municipio_interesse} em {ano_selecionado}.")
        return

    ORDEM_FAIXA_ETARIA = [
        "Menos de 1 ano",
        "1 a 4 anos",
        "5 a 9 anos",
        "10 a 14 anos",
        "15 a 19 anos",
        "20 a 24 anos",
        "25 a 29 anos",
        "30 a 34 anos",
        "35 a 39 anos",
        "40 a 44 anos",
        "45 a 49 anos",
        "50 a 54 anos",
        "55 a 59 anos",
        "60 a 64 anos",
        "65 a 69 anos",
        "70 a 74 anos",
        "75 a 79 anos",
        "80 ou mais",
    ]

    max_val = df_plot["proporcao"].abs().max()
    axis_max = (max_val // 1) + 1

    fig = px.bar(
        df_plot,
        y="faixa_etaria",
        x="proporcao",
        color="sexo",
        height=550,
        orientation="h",
        barmode="relative",
        color_discrete_map={"Masculino": "#4C82F7", "Feminino": "#FF6BE1"},
        title="",
        labels={"proporcao": "Porcentagem da População", "faixa_etaria": ""},
        category_orders={
            "faixa_etaria": ORDEM_FAIXA_ETARIA,
            "sexo": ["Masculino", "Feminino"],
        },
        text=df_plot["proporcao"].apply(
            lambda x: f"{abs(x):.1f}".replace(".", ",") + "%"
        ),
    )

    fig.update_layout(
        barmode="relative",
        yaxis_title="",
        xaxis_title="Porcentagem da População",
        legend_title_text="",
        legend_orientation="h",
        legend_yanchor="bottom",
        legend_y=1.0,
        xaxis=dict(
            tickvals=[-axis_max, -axis_max / 2, 0, axis_max / 2, axis_max],
            ticktext=[
                f"{axis_max:.1f}%",
                f"{axis_max / 2:.1f}%",
                "0%",
                f"{axis_max / 2:.1f}%",
                f"{axis_max:.1f}%",
            ],
            range=[-axis_max - 1, axis_max + 1],
        ),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{data.name}</b><br>"
            "Faixa: %{y}<br>"
            "População: %{customdata[0]:,.0f}<br>"
            "Proporção: %{customdata[1]}<extra></extra>"
        ),
        customdata=df_plot[["pop_estimada", "proporcao"]].abs(),
    )
    titulo_centralizado(
        f"Pirâmide Etária de {municipio_interesse} ({ano_selecionado})", 5
    )
    st.plotly_chart(fig, use_container_width=True)


def show_page_demografia(df_populacao_densidade, df_populacao_sexo_idade):
    titulo_centralizado("Dashboard de Demográfia", 1)
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)
    with st.expander("Indicadores demográficos dos Municípios"):
        display_populacao_densidade_expander(
            df_filtrado=df_populacao_densidade,
            df_filtrado_sexo=df_populacao_sexo_idade,
        )

    with st.expander(f"Pirâmide Etária de {municipio_de_interesse}"):
        display_populacao_piramide_etaria_expander(
            df_filtrado_sexo=df_populacao_sexo_idade,
            municipio_interesse=municipio_de_interesse,
        )
