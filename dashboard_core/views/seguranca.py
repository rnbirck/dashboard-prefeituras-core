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

# --- VARIÁVEIS GLOBAIS DO MÓDULO ---
CORES_MUNICIPIOS = {}
anos_de_interesse = []


def set_seguranca_config(cores_municipios, anos_interesse):
    """
    Configura valores específicos do município e anos de interesse.
    Deve ser chamado pelo app.py antes de renderizar a página.
    """
    global CORES_MUNICIPIOS, anos_de_interesse
    CORES_MUNICIPIOS = cores_municipios or {}
    anos_de_interesse = anos_interesse or []


# --- FUNÇÕES AUXILIARES ---
def formatar_valor_br(x):
    """Formata número float para padrão BR."""
    if pd.isna(x):
        return "-"
    if isinstance(x, int) or x.is_integer():
        return f"{x:,.0f}".replace(",", ".")
    return f"{x:,.2f}".replace(".", ",")


# --- FUNÇÕES DE CALLBACK ---


def set_expander_open(key):
    """Define o estado de um expander específico como True (aberto)."""
    st.session_state[key] = True


def geral_callback():
    set_expander_open("geral_expander_state")


def mulher_callback():
    set_expander_open("mulher_expander_state")


def drogas_callback():
    set_expander_open("drogas_expander_state")


# ==============================================================================
# FUNÇÕES DA PÁGINA DE SEGURANÇA
# ==============================================================================


@st.cache_data
def preparar_dados_graficos_seguranca(
    df_filtrado, coluna_selecionada, anos_visualizacao, is_taxa=False
):
    """
    Prepara os DataFrames pivotados para as abas da página de segurança.
    Retorna também os DataFrames de Variação (%) para Acumulado e Anual.
    """
    df_hist = pd.DataFrame()
    df_acum, df_acum_var = pd.DataFrame(), pd.DataFrame()
    df_anual, df_anual_var = pd.DataFrame(), pd.DataFrame()
    ult_ano, ult_mes = None, None

    coluna_valor = f"taxa_{coluna_selecionada}" if is_taxa else coluna_selecionada

    if not df_filtrado.empty and coluna_valor in df_filtrado.columns:
        # Pega o último ano DENTRO dos anos de visualização desejados
        df_range_visualizacao = df_filtrado[df_filtrado["ano"].isin(anos_visualizacao)]
        if df_range_visualizacao.empty:
            ult_ano = df_filtrado["ano"].max()
        else:
            ult_ano = df_range_visualizacao["ano"].max()

        ult_mes = df_filtrado[df_filtrado["ano"] == ult_ano]["mes"].max()

        # 1. Evolução Mensal
        df_hist_full = (
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
        df_hist = df_hist_full[df_hist_full.index.year.isin(anos_visualizacao)]

        # 2. Acumulado no Ano
        df_acum_temp = df_filtrado[df_filtrado["mes"] <= ult_mes]

        df_acum_full = df_acum_temp.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_valor,
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        # Cálculo da Variação (usando o ano buffer)
        df_acum_var_full = df_acum_full.pct_change() * 100

        # Filtra anos
        df_acum = df_acum_full[df_acum_full.index.isin(anos_visualizacao)]
        df_acum_var = df_acum_var_full[df_acum_var_full.index.isin(anos_visualizacao)]

        # 3. Anual (Anos Completos)
        ano_completo = checar_ult_ano_completo(df_filtrado)
        df_anual_temp = df_filtrado[df_filtrado["ano"] <= ano_completo]

        df_anual_calc = df_anual_temp.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_valor,
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        df_anual_var_full = df_anual_calc.pct_change() * 100

        # Filtra e ordena
        df_anual = df_anual_calc[
            df_anual_calc.index.isin(anos_visualizacao)
        ].sort_index(ascending=False)
        df_anual_var = df_anual_var_full[
            df_anual_var_full.index.isin(anos_visualizacao)
        ].sort_index(ascending=False)

    return df_hist, df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes


def display_secao_seguranca(
    df_seguranca,
    df_seguranca_taxa,
    titulo_expander,
    dicionario_indicadores,
    key_prefix,
    expander_state_key,
    callback_func,
    label_taxa_desc="Taxa por 10 mil hab.",
    anos_visuais=None,
):
    """
    Exibe uma seção de indicadores de segurança com controles dentro das abas.
    """
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    # Usa a variável global se não for passado argumento
    if anos_visuais is None:
        anos_visuais = anos_de_interesse

    with st.expander(titulo_expander, expanded=st.session_state[expander_state_key]):
        # --- 1. SELETOR DE INDICADOR ---
        indicador_selecionado = st.selectbox(
            "Selecione um indicador:",
            options=list(dicionario_indicadores.keys()),
            key=f"{key_prefix}_selectbox",
            on_change=callback_func,
        )
        coluna_selecionada = dicionario_indicadores[indicador_selecionado]

        # --- 2. PREPARAÇÃO DOS DADOS ---
        # Dados Absolutos
        (
            hist_abs,
            acum_abs,
            acum_var_abs,
            anual_abs,
            anual_var_abs,
            ult_ano,
            ult_mes,
        ) = preparar_dados_graficos_seguranca(
            df_seguranca, coluna_selecionada, anos_visuais, is_taxa=False
        )

        # Dados Taxa
        (hist_taxa, acum_taxa, _, anual_taxa, _, _, _) = (
            preparar_dados_graficos_seguranca(
                df_seguranca_taxa, coluna_selecionada, anos_visuais, is_taxa=True
            )
        )

        anos_disponiveis = sorted(list(anos_visuais), reverse=True)

        # --- 3. NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = f"main_tab_nav_{key_prefix}"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Evolução Mensal"

        aba_selecionada = st.pills(
            "Selecione o tipo de análise temporal:",
            options=["Evolução Mensal", "Acumulado no Ano", "Anual"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Evolução Mensal"

        # --- ABA 1: Evolução ---
        if aba_selecionada == "Evolução Mensal":
            col_opt, col_ano = st.columns([0.5, 0.5])
            with col_opt:
                # CORREÇÃO: Inicialização explícita da chave
                key_hist = f"hist_mode_{key_prefix}"
                if key_hist not in st.session_state:
                    st.session_state[key_hist] = "Nº Ocorrências"

                modo_hist = st.segmented_control(
                    "Visualizar:",
                    options=["Nº Ocorrências", label_taxa_desc],
                    key=key_hist,
                    selection_mode="single",
                    on_change=callback_func,
                )

                # Fallback: se desmarcar (None), força o padrão
                if not modo_hist:
                    modo_hist = "Nº Ocorrências"

            with col_ano:
                ano_hist = st.selectbox(
                    "Ano:",
                    options=anos_disponiveis,
                    index=0,
                    key=f"hist_ano_{key_prefix}",
                    on_change=callback_func,
                    label_visibility="visible",
                )

            if modo_hist == "Nº Ocorrências":
                df_plot = hist_abs
                lbl_y = "Ocorrências"
                fmt = ",.0f"
                hover = ",.0f"
                titulo_grafico = (
                    f"Número de Ocorrências - {indicador_selecionado} - {ano_hist}"
                )
            else:
                df_plot = hist_taxa
                lbl_y = label_taxa_desc
                fmt = ",.1f"
                hover = ",.2f"
                titulo_grafico = (
                    f"{label_taxa_desc} - {indicador_selecionado} - {ano_hist}"
                )

            titulo_centralizado(titulo_grafico, 5)

            if not df_plot.empty:
                df_plot_ano = df_plot[df_plot.index.year == ano_hist]
                if not df_plot_ano.empty:
                    df_plot_ano.index = [
                        f"{MESES_DIC[d.month][:3]}/{str(d.year)[2:]}"
                        for d in df_plot_ano.index
                    ]
                    fig = criar_grafico_barras(
                        df=df_plot_ano,
                        titulo="",
                        label_y=lbl_y,
                        barmode="group",
                        height=400,
                        data_label_format=fmt,
                        color_map=CORES_MUNICIPIOS,
                        hover_label_format=hover,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"Sem dados mensais para {ano_hist}.")
            else:
                st.warning("Sem dados disponíveis.")

        # --- ABA 2: ACUMULADO ---
        if ult_mes and aba_selecionada == "Acumulado no Ano":
            # CORREÇÃO: Inicialização explícita da chave
            key_acum = f"acum_mode_{key_prefix}"
            if key_acum not in st.session_state:
                st.session_state[key_acum] = "Nº Ocorrências"

            modo_acum = st.segmented_control(
                "Visualizar:",
                options=["Nº Ocorrências", label_taxa_desc, "Variação (%)"],
                key=key_acum,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_acum:
                modo_acum = "Nº Ocorrências"

            periodo_txt = f"Jan a {MESES_DIC[ult_mes]}"

            if modo_acum == "Variação (%)":
                titulo_centralizado(
                    f"Variação Acumulada - {indicador_selecionado} - {periodo_txt}",
                    5,
                )
                df_var_plot = acum_var_abs.copy().sort_index(ascending=False)
                df_var_plot.index = df_var_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y="Variação (%)",
                    barmode="group",
                    height=400,
                    data_label_format="+,.1f",
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format="+,.2f",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                if modo_acum == "Nº Ocorrências":
                    df_plot = acum_abs.copy()
                    lbl_y = "Ocorrências"
                    fmt = ",.0f"
                    hover = ",.0f"
                    titulo_grafico = f"Número de Ocorrências - {indicador_selecionado} - {periodo_txt}"
                else:
                    df_plot = acum_taxa.copy()
                    lbl_y = label_taxa_desc
                    fmt = ",.1f"
                    hover = ",.2f"
                    titulo_grafico = (
                        f"{label_taxa_desc} - {indicador_selecionado} - {periodo_txt}"
                    )

                titulo_centralizado(titulo_grafico, 5)

                df_plot.index = (
                    "Jan-"
                    + MESES_DIC[ult_mes][:3]
                    + "/"
                    + df_plot.index.astype(str).str.slice(-2)
                )
                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=lbl_y,
                    barmode="group",
                    height=400,
                    data_label_format=fmt,
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format=hover,
                )
                st.plotly_chart(fig, use_container_width=True)

        # --- ABA 3: ANUAL ---
        if aba_selecionada == "Anual":
            # CORREÇÃO: Inicialização explícita da chave
            key_anual = f"anual_mode_{key_prefix}"
            if key_anual not in st.session_state:
                st.session_state[key_anual] = "Nº Ocorrências"

            modo_anual = st.segmented_control(
                "Visualizar:",
                options=["Nº Ocorrências", label_taxa_desc, "Variação (%)"],
                key=key_anual,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_anual:
                modo_anual = "Nº Ocorrências"

            if modo_anual == "Variação (%)":
                titulo_centralizado(f"Variação Anual - {indicador_selecionado}", 5)
                df_var_plot = anual_var_abs.copy()
                df_var_plot.index = df_var_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y="Variação (%)",
                    barmode="group",
                    height=400,
                    data_label_format="+,.1f",
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format="+,.2f",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                if modo_anual == "Nº Ocorrências":
                    df_plot = anual_abs
                    lbl_y = "Ocorrências"
                    fmt = ",.0f"
                    hover = ",.0f"
                    titulo_grafico = (
                        f"Número de Ocorrências - {indicador_selecionado} - Anual"
                    )
                else:
                    df_plot = anual_taxa
                    lbl_y = label_taxa_desc
                    fmt = ",.1f"
                    hover = ",.2f"
                    titulo_grafico = (
                        f"{label_taxa_desc} - {indicador_selecionado} - Anual"
                    )

                titulo_centralizado(titulo_grafico, 5)

                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=lbl_y,
                    barmode="group",
                    height=400,
                    data_label_format=fmt,
                    color_map=CORES_MUNICIPIOS,
                    hover_label_format=hover,
                )
                st.plotly_chart(fig, use_container_width=True)


def show_page_seguranca(df_seguranca, df_seguranca_taxa):
    # Inicialização dos estados dos expanders
    if "geral_expander_state" not in st.session_state:
        st.session_state.geral_expander_state = False
    if "mulher_expander_state" not in st.session_state:
        st.session_state.mulher_expander_state = False
    if "drogas_expander_state" not in st.session_state:
        st.session_state.drogas_expander_state = False

    titulo_centralizado("Dashboard de Segurança", 1)
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

    # Dicionários de Indicadores
    INDICADORES_GERAIS = {
        "Homicídio Doloso": "homicidio_doloso",
        "Furtos": "furtos",
        "Roubos": "roubos",
        "Furto de Veículo": "furto_veiculo",
        "Roubo de Veículo": "roubo_veiculo",
        "Estelionato": "estelionato",
    }

    INDICADORES_VIOLENCIA_MULHER = {
        "Feminicídio Consumado": "feminicidio_consumado",
        "Feminicídio Tentado": "feminicidio_tentado",
        "Ameaça": "ameaca",
        "Estupro": "estupro",
        "Lesão Corporal": "lesao_corporal",
    }

    INDICADORES_DROGAS_ARMAS = {
        "Delitos com Armas e Munições": "delitos_armas_municoes",
        "Posse de Entorpecentes": "entorpecentes_posse",
        "Tráfico de Entorpecentes": "entorpecentes_trafico",
    }

    # Renderização das Seções
    display_secao_seguranca(
        df_seguranca,
        df_seguranca_taxa,
        "Indicadores Gerais",
        INDICADORES_GERAIS,
        "geral",
        "geral_expander_state",
        geral_callback,
    )
    display_secao_seguranca(
        df_seguranca,
        df_seguranca_taxa,
        "Violência Contra a Mulher",
        INDICADORES_VIOLENCIA_MULHER,
        "mulher",
        "mulher_expander_state",
        mulher_callback,
        label_taxa_desc="Taxa por 10 mil mulheres",
    )
    display_secao_seguranca(
        df_seguranca,
        df_seguranca_taxa,
        "Crimes Relacionados à Drogas e Armas",
        INDICADORES_DROGAS_ARMAS,
        "drogas",
        "drogas_expander_state",
        drogas_callback,
    )
