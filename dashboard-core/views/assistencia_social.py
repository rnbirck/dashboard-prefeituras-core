import streamlit as st
import pandas as pd

# ==============================================================================
# IMPORTAÇÕES DE FUNÇÕES E DADOS
# ==============================================================================

from src.utils import MESES_DIC, criar_grafico_barras, titulo_centralizado, calcular_yoy

from src.config import (
    municipio_de_interesse,
    CORES_MUNICIPIOS,
)

# ==============================================================================
# FUNÇÕES DA PÁGINA DE ASSISTENCIA SOCIAL
# ==============================================================================


def display_assistencia_kpi_cards(df_cad, df_bolsa, municipio_interesse):
    """Exibe os cards de KPI de Assistencia Social para um município específico."""
    titulo_centralizado(f"Indicadores de {municipio_interesse}", 3)

    with st.container(border=False):
        df_cad_mun = df_cad[df_cad["municipio"] == municipio_interesse]
        ult_ano_cad = df_cad_mun["ano"].max()
        ult_mes_cad = df_cad_mun[df_cad_mun["ano"] == ult_ano_cad]["mes"].max()

        df_bolsa_mun = df_bolsa[df_bolsa["municipio"] == municipio_interesse]
        ult_ano_bolsa = df_bolsa_mun["ano"].max()
        ult_mes_bolsa = df_bolsa_mun[df_bolsa_mun["ano"] == ult_ano_bolsa]["mes"].max()

        num_cad = df_cad_mun[
            (df_cad_mun["ano"] == ult_ano_cad) & (df_cad_mun["mes"] == ult_mes_cad)
        ]["total_familias"].sum()

        num_cad_yoy = calcular_yoy(
            df=df_cad_mun,
            municipio=municipio_de_interesse,
            ultimo_ano=ult_ano_cad,
            ultimo_mes=ult_mes_cad,
            coluna="total_familias",
            round=1,
        )

        num_bolsa = df_bolsa_mun[
            (df_bolsa_mun["ano"] == ult_ano_bolsa)
            & (df_bolsa_mun["mes"] == ult_mes_bolsa)
        ]["qtd_beneficiados"].sum()

        num_bolsa_yoy = calcular_yoy(
            df=df_bolsa_mun,
            municipio=municipio_de_interesse,
            ultimo_ano=ult_ano_bolsa,
            ultimo_mes=ult_mes_bolsa,
            coluna="qtd_beneficiados",
            round=1,
        )

        col1, col2 = st.columns(2)
        col1.metric(
            label=f"Famílias inscritas no CAD Único em {MESES_DIC[ult_mes_cad][:3]}/{str(ult_ano_cad)[-2:]}",
            value=f"{num_cad:,.0f}".replace(",", "."),
            delta=f"{num_cad_yoy}%".replace(".", ","),
            help="Taxa de Variação percentual em relação ao mesmo mês do ano anterior",
            border=True,
        )
        col2.metric(
            label=f"Beneficiários do Novo Bolsa Família em {MESES_DIC[ult_mes_bolsa][:3]}/{str(ult_ano_cad)[-2:]}",
            value=f"{num_bolsa:,.0f}".replace(",", "."),
            delta=f"{num_bolsa_yoy}%".replace(".", ","),
            help="Taxa de Variação percentual em relação ao mesmo mês do ano anterior",
            border=True,
        )


@st.cache_data
def preparar_dados_graficos_assistencia_social(df, coluna_selecionada):
    """Prepara os DataFrames pivotados para as abas da página de assistencia_social."""
    df_graf = pd.DataFrame()

    df_graf = (
        df.assign(
            date=lambda x: pd.to_datetime(
                x["ano"].astype(str) + "-" + x["mes"].astype(str).str.zfill(2) + "-01"
            )
        )
        .pivot_table(
            index="date",
            columns="municipio",
            values=coluna_selecionada,
            aggfunc="sum",
            fill_value=0,
        )
        .sort_index()
    )

    return df_graf


def display_assistencia(
    df, titulo_expander, key_prefix, dicionario_indicadores, label_y, markdown_final
):
    """Função genérica para exibir a seção do Cad Unico e do Bolsa Familia na pagina de Assistencia Social."""

    with st.expander(f"{titulo_expander}", expanded=False):
        titulo_centralizado(f"Indicadores do {titulo_expander}", 5)
        col1, col2 = st.columns([0.6, 0.5])

        with col1:
            indicador_selecionado = st.selectbox(
                "Selecione um indicador:",
                options=list(dicionario_indicadores.keys()),
                key=f"{key_prefix}_selectbox",
            )

        coluna_selecionada = dicionario_indicadores[indicador_selecionado]
        df_graf = preparar_dados_graficos_assistencia_social(
            df=df, coluna_selecionada=coluna_selecionada
        )

        anos_disponiveis = sorted(df["ano"].unique().tolist(), reverse=True)

        with col2:
            if not anos_disponiveis:
                st.warning("Nenhum dado disponível para os filtros selecionados.")
            else:
                ANO_SELECIONADO = st.selectbox(
                    "Selecione o ano para o gráfico:",
                    options=anos_disponiveis,
                    index=0,
                    key=f"selecionar_ano_{key_prefix}",
                )

                df_graf_anos = df_graf[df_graf.index.year == ANO_SELECIONADO]
                if not df_graf_anos.empty:
                    df_graf_anos.index = [
                        f"{MESES_DIC[date.month][:3]}/{str(date.year)[2:]}"
                        for date in df_graf_anos.index
                    ]

        titulo_centralizado(f"{indicador_selecionado} - {titulo_expander}", 5)
        fig = criar_grafico_barras(
            df=df_graf_anos,
            titulo="",
            label_y=f"{label_y}",
            barmode="group",
            height=400,
            data_label_format=",.0f",
            color_map=CORES_MUNICIPIOS,
            hover_label_format=",.0f",
        )
        st.plotly_chart(fig, use_container_width=False)
        st.markdown(f"###### {markdown_final}")


def show_page_assistencia_social(df_cad, df_bolsa, municipio_interesse):
    titulo_centralizado("Dashboard de Assistência Social", 1)
    INDICADORES_CAD = {
        "Total de Pessoas": "total_pessoas",
        "Total de Famílias": "total_familias",
        "Quantidade de famílias em situação de pobreza": "qtd_fam_pob",
        "Quantidade de famílias de baixa renda": "qtd_fam_baixa_renda",
        "Quantidade de famílias com renda per capita mensal de até meio salário-mínimo": "qtd_fam_ate_meio_sm",
        "Quantidade de famílias com renda per capita mensal acima de meio salário-mínimo": "qtd_fam_acima_meio_sm",
    }
    INDICADORES_BOLSA = {
        "Número de Beneficiários": "qtd_beneficiados",
        "Valor Total do Benefício": "valor_total_beneficio",
        "Valor Médio do Benefício": "beneficio_medio",
    }

    display_assistencia_kpi_cards(
        df_cad=df_cad, df_bolsa=df_bolsa, municipio_interesse=municipio_de_interesse
    )
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

    display_assistencia(
        df=df_cad,
        dicionario_indicadores=INDICADORES_CAD,
        titulo_expander="Cadastro Único",
        key_prefix="cad",
        label_y="Número de Cadastrados",
        markdown_final="*Dados para abril de 2025 não divulgados",
    )

    display_assistencia(
        df=df_bolsa,
        dicionario_indicadores=INDICADORES_BOLSA,
        titulo_expander="Novo Bolsa Família",
        key_prefix="bolsa",
        label_y="",
        markdown_final="*Dados a partir de Março de 2023",
    )
