import pandas as pd
import streamlit as st

from dashboard_core.utils import (
    MESES_DIC,
    criar_grafico_barras,
    checar_ult_ano_completo,
    titulo_centralizado,
)

CORES_MUNICIPIOS = {}


def set_saude_config(cores_municipios):
    """
    Configura valores específicos do município que antes eram importados
    do dashboard_core.config. Deve ser chamado pelo app.py antes de
    renderizar a página de saude.
    """
    global CORES_MUNICIPIOS
    CORES_MUNICIPIOS = cores_municipios or {}


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


def preparar_dados_graficos_saude_mensal(
    df_filtrado, coluna_selecionada, metodo_agg="sum"
):
    """
    Prepara os DataFrames para os gráficos, usando o método de agregação correto.
    'sum' para números absolutos, 'mean' para taxas/proporções.
    """
    df_hist, df_acum, df_anual = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ult_ano, ult_mes = None, None

    if not df_filtrado.empty:
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
                values=coluna_selecionada,
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
        )

        # Lógica de Agregação para Acumulado e Anual
        agg_func = "mean" if metodo_agg == "mean" else "sum"

        # Acumulado no Ano
        df_acum_temp = df_filtrado[df_filtrado["mes"] <= ult_mes]
        df_acum = df_acum_temp.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_selecionada,
            aggfunc=agg_func,
            fill_value=0,
        ).sort_index()

        # Anual
        ano_completo = checar_ult_ano_completo(df_filtrado)
        df_anual_temp = df_filtrado[df_filtrado["ano"] <= ano_completo]
        df_anual = df_anual_temp.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_selecionada,
            aggfunc=agg_func,
            fill_value=0,
        ).sort_index(ascending=False)

    return df_hist, df_acum, df_anual, ult_ano, ult_mes


def preparar_dados_graficos_saude_anual(df_filtrado, coluna_selecionada):
    df_anual = df_filtrado.pivot_table(
        index="ano",
        columns="municipio",
        values=coluna_selecionada,
        aggfunc="sum",
        fill_value=0,
    ).sort_index(ascending=False)

    return df_anual


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

        coluna_selecionada, agg_method, label_y, data_format = dicionario_indicadores[
            indicador_selecionado
        ]

        hover_format = (
            f",.{int(data_format.split('.')[-1][0]) + 1}f"
            if "." in data_format
            else ",.0f"
        )

        df_hist, df_acum, df_anual, ult_ano, ult_mes = (
            preparar_dados_graficos_saude_mensal(
                df_filtrado, coluna_selecionada, agg_method
            )
        )

        anos_disponiveis = sorted(df_filtrado["ano"].unique().tolist(), reverse=True)

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
                    on_change=callback_func,
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
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=data_format,
                    hover_label_format=hover_format,
                    color_map=CORES_MUNICIPIOS,
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
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=data_format,
                    hover_label_format=hover_format,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)

        with tab_anual:
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

        hover_format = (
            f",.{int(data_format.split('.')[-1][0]) + 1}f"
            if "." in data_format
            else ",.0f"
        )

        df_anual = preparar_dados_graficos_saude_anual(
            df_filtrado=df_filtrado, coluna_selecionada=coluna_selecionada
        )
        titulo_centralizado(
            f"{indicador_selecionado}",
            5,
        )

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
