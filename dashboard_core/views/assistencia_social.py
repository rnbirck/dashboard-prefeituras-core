import streamlit as st
import pandas as pd

# ==============================================================================
# IMPORTAÇÕES DE FUNÇÕES E DADOS
# ==============================================================================

from dashboard_core.utils import (
    MESES_DIC,
    criar_grafico_barras,
    titulo_centralizado,
    calcular_yoy,
)

municipio_de_interesse = None
CORES_MUNICIPIOS = {}
anos_de_interesse = []


def set_assistencia_social_config(municipio, cores_municipios, anos_interesse):
    """
    Configura valores específicos do município.
    """
    global municipio_de_interesse, CORES_MUNICIPIOS, anos_de_interesse
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}
    anos_de_interesse = anos_interesse or []


# --- FUNÇÕES DE CALLBACK ---
def set_expander_open(key):
    """Define o estado de um expander específico como True (aberto)."""
    st.session_state[key] = True


def cad_callback():
    set_expander_open("cad_expander_state")


def bolsa_callback():
    set_expander_open("bolsa_expander_state")


# ==============================================================================
# PREPARAÇÃO DE DADOS (ADAPTADO PARA ESTOQUE/SOCIAL)
# ==============================================================================


@st.cache_data
def preparar_dados_graficos_assistencia(
    df_filtrado, coluna_selecionada, anos_visualizacao, is_percentage=False
):
    """
    Prepara os DataFrames pivotados.
    Args:
        is_percentage (bool): Se True, calcula a variação como diferença absoluta (p.p.),
                              caso contrário, calcula variação percentual (%).
    """
    df_hist = pd.DataFrame()
    df_acum, df_acum_var = pd.DataFrame(), pd.DataFrame()
    df_anual, df_anual_var = pd.DataFrame(), pd.DataFrame()
    ult_ano, ult_mes = None, None

    if not df_filtrado.empty and coluna_selecionada in df_filtrado.columns:
        # Pega o último ano/mês DENTRO dos anos de visualização
        df_range_visualizacao = df_filtrado[df_filtrado["ano"].isin(anos_visualizacao)]

        if df_range_visualizacao.empty:
            ult_ano = df_filtrado["ano"].max()
        else:
            ult_ano = df_range_visualizacao["ano"].max()

        # Garante que pegamos o último mês com dados desse ano
        ult_mes = df_filtrado[df_filtrado["ano"] == ult_ano]["mes"].max()

        # 1. Histórico Mensal
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
                values=coluna_selecionada,
                aggfunc="sum",
                fill_value=0,
            )
            .sort_index()
        )
        df_hist = df_hist_full[df_hist_full.index.year.isin(anos_visualizacao)]

        # 2. "Mês" (Para estoque = Posição do Último Mês)
        df_mes_atual = df_filtrado[(df_filtrado["mes"] == ult_mes)]

        df_acum_full = df_mes_atual.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_selecionada,
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        # Variação YoY
        if is_percentage:
            df_acum_var_full = df_acum_full.diff()
        else:
            df_acum_var_full = df_acum_full.pct_change() * 100

        # Filtra anos
        df_acum = df_acum_full[df_acum_full.index.isin(anos_visualizacao)]
        df_acum_var = df_acum_var_full[df_acum_var_full.index.isin(anos_visualizacao)]

        # 3. Anual (VALOR DE DEZEMBRO)
        # Filtra apenas os registros onde o mês é 12 (Dezembro)
        df_dezembro = df_filtrado[df_filtrado["mes"] == 12]

        df_anual_calc = df_dezembro.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_selecionada,
            aggfunc="sum",  # Como já filtramos 1 registro por ano/mun, sum ou mean dá na mesma
            fill_value=0,
        ).sort_index()

        if is_percentage:
            df_anual_var_full = df_anual_calc.diff()
        else:
            df_anual_var_full = df_anual_calc.pct_change() * 100

        # Filtra e ordena
        df_anual = df_anual_calc[
            df_anual_calc.index.isin(anos_visualizacao)
        ].sort_index(ascending=True)

        df_anual_var = df_anual_var_full[
            df_anual_var_full.index.isin(anos_visualizacao)
        ].sort_index(ascending=True)

    return df_hist, df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes


# ==============================================================================
# VISUALIZAÇÃO
# ==============================================================================


def display_secao_assistencia_padrao(
    df,
    titulo_expander,
    dicionario_indicadores,
    key_prefix,
    expander_state_key,
    callback_func,
    label_desc="Total",
    anos_visuais=None,
):
    """
    Exibe uma seção de indicadores com navegação persistente (substituindo st.tabs).
    """
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    if anos_visuais is None:
        anos_visuais = anos_de_interesse

    with st.expander(titulo_expander, expanded=st.session_state[expander_state_key]):
        # Mensagem informativa específica para Cadastro Único
        if key_prefix == "cad":
            st.info("ℹ️ Dados do CadÚnico para março de 2025 não foram divulgados.")

        # Mensagem informativa específica para Novo Bolsa Família
        if key_prefix == "bolsa":
            st.info(
                "ℹ️ Dados do Novo Bolsa Família disponíveis a partir de março de 2023."
            )

        # --- 1. SELETOR DE INDICADOR ---
        indicador_selecionado = st.selectbox(
            "Selecione um indicador:",
            options=list(dicionario_indicadores.keys()),
            key=f"{key_prefix}_selectbox",
            on_change=callback_func,
        )
        coluna_selecionada = dicionario_indicadores[indicador_selecionado]

        # Verifica se é o indicador de vulnerabilidade (percentual)
        is_vuln = (
            indicador_selecionado == "População em situação de vulnerabilidade (%)"
        )

        # Define rótulos de variação
        label_var = "Variação (p.p.)" if is_vuln else "Variação (%)"
        fmt_var = "+,.2f" if is_vuln else "+,.1f"

        # --- 2. PREPARAÇÃO DOS DADOS ---
        (
            hist_abs,
            acum_abs,
            acum_var_abs,
            anual_abs,
            anual_var_abs,
            ult_ano,
            ult_mes,
        ) = preparar_dados_graficos_assistencia(
            df, coluna_selecionada, anos_visuais, is_percentage=is_vuln
        )

        anos_disponiveis = sorted(list(anos_visuais), reverse=True)

        # --- 3. NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        # Chave única para o estado da aba principal deste expander
        key_main_tab = f"main_tab_nav_{key_prefix}"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Evolução Mensal"

        # Seletor que age como abas
        aba_selecionada = st.pills(
            "Selecione o tipo de análise temporal:",
            options=["Evolução Mensal", "Mês", "Anual"],
            selection_mode="single",
            key=key_main_tab,
            width=600,
        )

        # Fallback caso o usuário desmarque
        if not aba_selecionada:
            aba_selecionada = "Evolução Mensal"

        # --- CONTEÚDO DA ABA 1: EVOLUÇÃO ---
        if aba_selecionada == "Evolução Mensal":
            with st.container():
                col_ano, _ = st.columns([0.5, 0.5])

                with col_ano:
                    ano_hist = st.selectbox(
                        "Ano:",
                        options=anos_disponiveis,
                        index=0,
                        key=f"hist_ano_{key_prefix}",
                        on_change=callback_func,
                        label_visibility="visible",
                    )

                df_plot = hist_abs
                lbl_y = label_desc
                fmt = ",.1f" if is_vuln else ",.0f"
                hover = ",.2f" if is_vuln else ",.0f"

                titulo_grafico = (
                    f"Evolução Mensal - {indicador_selecionado} - {ano_hist}"
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

        # --- CONTEÚDO DA ABA 2: ACUMULADO NO ANO ---
        elif aba_selecionada == "Mês":
            if ult_mes:
                with st.container():
                    col_opt_ac, _ = st.columns([0.6, 0.4])

                    with col_opt_ac:
                        key_acum = f"acum_mode_{key_prefix}"
                        if key_acum not in st.session_state:
                            st.session_state[key_acum] = label_desc

                        modo_acum = st.segmented_control(
                            "Opções:",
                            options=[label_desc, label_var],
                            key=key_acum,
                            selection_mode="single",
                            label_visibility="collapsed",
                        )

                        if not modo_acum:
                            modo_acum = label_desc

                    periodo_txt = f"{MESES_DIC[ult_mes]}"

                    if modo_acum == label_var:
                        titulo_centralizado(
                            f"{indicador_selecionado} - {label_var} - {periodo_txt}", 5
                        )
                        df_var_plot = acum_var_abs.copy().sort_index(ascending=True)

                        # Remove anos com variação nula (NaN) em todas as colunas
                        df_var_plot = df_var_plot.dropna(how="all")

                        df_var_plot.index = [
                            f"{MESES_DIC[ult_mes]}/{str(y)[2:]}"
                            for y in df_var_plot.index
                        ]

                        fig = criar_grafico_barras(
                            df=df_var_plot,
                            titulo="",
                            label_y=label_var,
                            barmode="group",
                            height=400,
                            data_label_format=fmt_var,
                            color_map=CORES_MUNICIPIOS,
                            hover_label_format=fmt_var,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        df_plot = acum_abs.copy()
                        lbl_y = label_desc
                        fmt = ",.1f" if is_vuln else ",.0f"
                        hover = ",.2f" if is_vuln else ",.0f"

                        titulo_grafico = f"{indicador_selecionado} em {periodo_txt}"

                        titulo_centralizado(titulo_grafico, 5)

                        df_plot.index = [
                            f"{MESES_DIC[ult_mes]}/{str(y)[2:]}" for y in df_plot.index
                        ]

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
            else:
                st.warning("Dados no mês não disponíveis.")

        # --- CONTEÚDO DA ABA 3: ANUAL ---
        elif aba_selecionada == "Anual":
            with st.container():
                col_opt_an, _ = st.columns([0.6, 0.4])

                with col_opt_an:
                    key_anual = f"anual_mode_{key_prefix}"
                    if key_anual not in st.session_state:
                        st.session_state[key_anual] = label_desc

                    modo_anual = st.segmented_control(
                        "Opções:",
                        options=[label_desc, label_var],
                        key=key_anual,
                        selection_mode="single",
                        label_visibility="collapsed",
                    )

                    if not modo_anual:
                        modo_anual = label_desc

                if modo_anual == label_var:
                    titulo_centralizado(
                        f"{indicador_selecionado} - {label_var} Anual ", 5
                    )
                    df_var_plot = anual_var_abs.copy()

                    # Remove anos com variação nula (NaN) em todas as colunas
                    df_var_plot = df_var_plot.dropna(how="all")

                    df_var_plot.index = df_var_plot.index.astype(str)

                    fig = criar_grafico_barras(
                        df=df_var_plot,
                        titulo="",
                        label_y=label_var,
                        barmode="group",
                        height=400,
                        data_label_format=fmt_var,
                        color_map=CORES_MUNICIPIOS,
                        hover_label_format=fmt_var,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    df_plot = anual_abs
                    lbl_y = f"{label_desc}"
                    fmt = ",.1f" if is_vuln else ",.0f"
                    hover = ",.2f" if is_vuln else ",.0f"

                    titulo_grafico = f"{indicador_selecionado} - Anual"

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


# ==============================================================================
# CARDS KPI
# ==============================================================================


def display_assistencia_kpi_cards(df_cad, df_bolsa, municipio_interesse):
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


# ==============================================================================
# FUNÇÃO PRINCIPAL DA PÁGINA
# ==============================================================================


def show_page_assistencia_social(df_cad, df_bolsa, municipio_interesse):
    if "cad_expander_state" not in st.session_state:
        st.session_state.cad_expander_state = False
    if "bolsa_expander_state" not in st.session_state:
        st.session_state.bolsa_expander_state = False

    titulo_centralizado("Dashboard de Assistência Social", 1)

    # Dicionários
    INDICADORES_CAD = {
        "Número de Pessoas": "total_pessoas",
        "Número de Famílias": "total_familias",
        "Quantidade de famílias em situação de pobreza": "qtd_fam_pob",
        "Quantidade de famílias de baixa renda": "qtd_fam_baixa_renda",
        "Quantidade de famílias com renda per capita mensal de até meio salário-mínimo": "qtd_fam_ate_meio_sm",
        "Quantidade de famílias com renda per capita mensal acima de meio salário-mínimo": "qtd_fam_acima_meio_sm",
        "População em situação de vulnerabilidade (%)": "pop_vulnerabilidade",
    }

    INDICADORES_BOLSA = {
        "Número de Beneficiários": "qtd_beneficiados",
        "Valor Total do Benefício": "valor_total_beneficio",
        "Valor Médio do Benefício": "beneficio_medio",
    }

    # KPIs
    display_assistencia_kpi_cards(
        df_cad=df_cad, df_bolsa=df_bolsa, municipio_interesse=municipio_de_interesse
    )
    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

    # CADASTRO ÚNICO
    display_secao_assistencia_padrao(
        df=df_cad,
        titulo_expander="Cadastro Único",
        dicionario_indicadores=INDICADORES_CAD,
        key_prefix="cad",
        expander_state_key="cad_expander_state",
        callback_func=cad_callback,
        label_desc="Total",
        anos_visuais=anos_de_interesse,
    )

    # BOLSA FAMÍLIA
    display_secao_assistencia_padrao(
        df=df_bolsa,
        titulo_expander="Novo Bolsa Família",
        dicionario_indicadores=INDICADORES_BOLSA,
        key_prefix="bolsa",
        expander_state_key="bolsa_expander_state",
        callback_func=bolsa_callback,
        label_desc="Valor/Qtd",
        anos_visuais=anos_de_interesse,
    )
