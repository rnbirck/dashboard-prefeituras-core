import numpy as np
import pandas as pd
import streamlit as st

from dashboard_core.config import (
    CORES_MUNICIPIOS,
)

# ==============================================================================
# IMPORTAÇÕES DE FUNÇÕES E DADOS
# ==============================================================================
from dashboard_core.utils import criar_grafico_barras, titulo_centralizado, BIMESTRE_MAP


# ==============================================================================
# FUNÇÕES DA PÁGINA DE FINANÇAS
# ==============================================================================
@st.cache_data
def preparar_dados_siconfi(df, cod_conta):
    """Prepara os dados brutos do SICONFI para um município e conta específicos."""
    return (
        df[(df["cod_conta"] == cod_conta)]
        .sort_values(by=["municipio", "coluna", "bimestre", "ano"])
        .assign(
            valor_milhoes=lambda x: x["valor"] / 1000000,
            valor_ano_anterior=lambda x: x.groupby(["municipio", "coluna", "bimestre"])[
                "valor"
            ].shift(1),
        )
        .pipe(
            lambda x: x.assign(
                variacao_yoy=lambda x: np.where(
                    x["valor_ano_anterior"].notna() & x["valor_ano_anterior"] != 0,
                    (x["valor"] / x["valor_ano_anterior"] - 1) * 100,
                    np.nan,
                )
            )
        )
    )


@st.cache_data
def _pivot_siconfi_data(df_preparado, coluna_valor, coluna_filtro):
    """
    Função auxiliar para pivotar os dados do SICONFI e formatar o índice.
    """
    if df_preparado.empty:
        return pd.DataFrame()

    df_pivot = df_preparado.query(f"coluna == '{coluna_filtro}'").pivot_table(
        index=["ano", "bimestre"],
        columns="municipio",
        values=coluna_valor,
        aggfunc="sum",
        fill_value=0,
    )

    if df_pivot.empty:
        return pd.DataFrame()

    bimestre_txt = (
        df_pivot.index.get_level_values("bimestre").map(BIMESTRE_MAP).fillna("Desconh.")
    )
    ano_txt = df_pivot.index.get_level_values("ano").astype(str).str.slice(-2)
    df_pivot.index = bimestre_txt + "-" + ano_txt

    return df_pivot


def display_siconfi_consolidado(df, expanded=False):
    """
    Exibe um expander consolidado para todos os indicadores do SICONFI
    com seletores internos.
    """
    # --- LÓGICA DOS ANOS ---
    if df.empty:
        st.warning("Não há dados financeiros (SICONFI) disponíveis.")
        return

    anos_unicos_total = sorted(df["ano"].unique())

    if len(anos_unicos_total) <= 1:
        st.warning("Não há dados suficientes para comparação YoY (SICONFI).")
        return

    anos_validos_selecao = anos_unicos_total[1:]

    min_ano_valido = min(anos_validos_selecao)
    max_ano_valido = max(anos_validos_selecao)

    # Define o default para os dois últimos anos
    if len(anos_validos_selecao) >= 2:
        default_start = anos_validos_selecao[-2]
        default_end = anos_validos_selecao[-1]
    else:  # Apenas um ano válido
        default_start = min_ano_valido
        default_end = max_ano_valido

    CONTAS_SICONFI = {
        "Receitas Correntes": "ReceitasCorrentes",
        "Total de Receitas": "TotalReceitas",
        "Transferências Correntes": "TransferenciasCorrentes",
        "Impostos": "Impostos",
        # Adicione outras contas aqui (ex: Despesas)
    }

    with st.expander("Indicadores Bimestrais da Execução Orçamentária", expanded=False):
        col1, col3, col2 = st.columns([0.5, 0.05, 0.45])
        with col1:
            conta_selecionada = st.selectbox(
                "Selecione a Conta:",
                options=list(CONTAS_SICONFI.keys()),
                key="siconfi_conta_selectbox",
            )
            cod_conta = CONTAS_SICONFI[conta_selecionada]

        with col2:
            view_mode = st.radio(
                "Selecione a Visualização:",
                options=["Valor (Milhões R$)", "Variação Anual (%)"],
                horizontal=True,
                key="siconfi_view_mode_radio",
            )

        col_radio1, col_radio3, col_radio2 = st.columns([0.5, 0.05, 0.45])
        with col_radio1:
            anos_selecionados_slider = st.slider(
                "Selecione o Período (Anos):",
                min_value=min_ano_valido,
                max_value=max_ano_valido,
                value=(default_start, default_end),
                step=1,
                key="siconfi_ano_slider",
                format="%d",
            )

        with col_radio2:
            periodo_mode = st.radio(
                "Selecione o Período:",
                options=["No Bimestre", "Até o Bimestre"],
                horizontal=True,
                key="siconfi_periodo_mode_radio",
            )

        start_ano_slider, end_ano_slider = anos_selecionados_slider

        anos_para_visualizar = list(range(start_ano_slider, end_ano_slider + 1))

        ano_anterior_inicio = start_ano_slider - 1

        anos_para_dados = list(range(ano_anterior_inicio, end_ano_slider + 1))

        df_filtrado_anos = df[df["ano"].isin(anos_para_dados)]

        # Prepara os dados uma única vez com base na conta e anos selecionados
        df_siconfi_mun = preparar_dados_siconfi(
            df=df_filtrado_anos,
            cod_conta=cod_conta,
        )

        # Define os parâmetros do gráfico com base nas seleções
        if view_mode == "Valor (Milhões R$)":
            coluna_valor = "valor_milhoes"
            label_y = "Valor (Milhões R$)"
            data_label_format = ".1f"
            hover_label_format = ",.2f"
        else:  # Variação Anual
            coluna_valor = "variacao_yoy"
            label_y = "Variação Anual (%)"
            data_label_format = ".1f"
            hover_label_format = ",.2f"

        if periodo_mode == "No Bimestre":
            coluna_filtro = "No Bimestre (b)"
            titulo_grafico = f"{conta_selecionada} - {view_mode} (Por Bimestre)"
        else:  # Até o Bimestre
            coluna_filtro = "Até o Bimestre (c)"
            titulo_grafico = (
                f"{conta_selecionada} - {view_mode} (Acumulado até o Bimestre)"
            )

        # Pivota os dados e formata o índice
        df_graf_bruto = _pivot_siconfi_data(
            df_preparado=df_siconfi_mun,
            coluna_valor=coluna_valor,
            coluna_filtro=coluna_filtro,
        )

        anos_para_visualizar_str = tuple(
            [str(ano)[-2:] for ano in anos_para_visualizar]
        )

        df_graf = df_graf_bruto[
            df_graf_bruto.index.str.endswith(anos_para_visualizar_str)
        ]

        titulo_centralizado(titulo_grafico, 5)

        fig_siconfi = criar_grafico_barras(
            df=df_graf,
            titulo="",
            label_y=label_y,
            barmode="group",
            height=400,
            data_label_format=data_label_format,
            hover_label_format=hover_label_format,
            color_map=CORES_MUNICIPIOS,
        )

        st.plotly_chart(fig_siconfi, use_container_width=True)


@st.cache_data
def preparar_dados_grafico_indicador_financeiros(
    df_indicadores_financeiros, coluna_selecionada
):
    df_graf = df_indicadores_financeiros.pivot_table(
        index="ano",
        columns="municipio",
        values=coluna_selecionada,
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    return df_graf


def display_indicadores_financeiros(
    df_filtrado,
    titulo_expander,
    key_prefix,
    dicionario_indicadores,
    label_y,
    data_label_format,
    hover_label_format,
    pdf_data,
):
    with st.expander(f"{titulo_expander}", expanded=False):
        indicador_selecionado = st.selectbox(
            "Selecione um Indicador Financeiro:",
            options=list(dicionario_indicadores.keys()),
            key=f"{key_prefix}_selectbox_indicadores",
        )

        coluna_selecionada, subtitulo = dicionario_indicadores[indicador_selecionado]

        df_graf = preparar_dados_grafico_indicador_financeiros(
            df_indicadores_financeiros=df_filtrado,
            coluna_selecionada=coluna_selecionada,
        )

        titulo_centralizado(f" Indicador de {indicador_selecionado} (%)", 5)
        titulo_centralizado(f"{subtitulo}", 6)

        fig = criar_grafico_barras(
            df=df_graf,
            titulo="",
            label_y=f"{label_y}",
            barmode="group",
            height=400,
            data_label_format=f"{data_label_format}",
            hover_label_format=f"{hover_label_format}",
            color_map=CORES_MUNICIPIOS,
        )
        if indicador_selecionado == "Execução Orçamentária Corrente":
            fig.add_hline(
                y=95,
                line_dash="dash",
                line_color="yellow",
                annotation_text="Limite (95%)",
                annotation_position="bottom right",
                annotation_font_color="yellow",
            )
        elif indicador_selecionado == "Endividamento":
            fig.add_hline(
                y=120,
                line_dash="dash",
                line_color="yellow",
                annotation_text="Limite (120%)",
                annotation_position="bottom right",
                annotation_font_color="yellow",
            )
        st.plotly_chart(fig, use_container_width=False)
        titulo_centralizado(
            "Download do relatório metodológico que detalha a construção dos indicadores fiscais dos municípios",
            6,
            cor="yellow",
        )
        if pdf_data:
            st.write("")
            pdf_data.seek(0)
            st.download_button(
                label="📥 Baixar PDF",
                data=pdf_data,
                file_name="Indicadores Fiscais Municípios.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


def show_page_financas(df_financas, df_indicadores_financeiros, pdf_indicadores):
    """Função principal que renderiza a página de Finanças Públicas."""
    titulo_centralizado("Dashboard de Finanças Públicas", 1)
    titulo_centralizado("Indicadores de Finanças Públicas", 3)
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

    INDICADORES_FINANCEIROS = {
        "Execução Orçamentária Corrente": (
            "exec_orc_corrente",
            "Quanto menor, melhor, indicando fôlego para assumir novos compromissos financeiros.",
        ),
        "Autonomia Fiscal": (
            "autonomia_fiscal",
            "Quanto maior, melhor, indicando menor dependência de transferências de outros entes e autossuficiência.",
        ),
        "Endividamento": (
            "endividamento",
            "Quanto menor, melhor, indicando menores compromissos financeiros e maior disponibilidade para a busca de recursos com operações de crédito.",
        ),
        "Despesas com Pessoal": (
            "despesas_pessoal",
            "Quanto menor, melhor, indicando menores compromissos com despesas continuadas, pois após concedidos reajustes e outros incrementos nas despesas com pessoal, devem ser honrados por um longo prazo, se tratando de despesas de difícil contingenciamento.",
        ),
        "Investimentos": (
            "investimento",
            "Quanto maior, melhor, indicando maior disponibilização de recursos para despesas de capital em relação a despesas de custeio.",
        ),
        "Disponibilidade de Caixa": (
            "disponibilidade_caixa",
            "Quanto maior, melhor, indicando a existência de reserva financeira para manutenção de serviços.",
        ),
        "Geração de Caixa": (
            "geracao_de_caixa",
            "Quanto maior, melhor, indicando a sobra de recursos financeiros ao final do período.",
        ),
        "Restos a Pagar": (
            "restos_a_pagar",
            "Quanto menor, melhor. Índices altos podem significar contas em atraso.",
        ),
    }
    display_indicadores_financeiros(
        df_filtrado=df_indicadores_financeiros,
        titulo_expander="Indicadores Financeiros",
        dicionario_indicadores=INDICADORES_FINANCEIROS,
        key_prefix="indicadores_financeiros",
        label_y="Percentual (%)",
        hover_label_format=",.2f",
        data_label_format=",.1f",
        pdf_data=pdf_indicadores,
    )
    display_siconfi_consolidado(
        df=df_financas,
        expanded=True,
    )
