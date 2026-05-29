import streamlit as st
import pandas as pd

from dashboard_core.utils import (
    MESES_DIC,
    checar_ult_ano_completo,
    criar_grafico_barras,
    criar_grafico_linhas,
    criar_tabela_formatada,
    criar_tabela_formatada_mes,
    criar_tabela_formatada_ano,
    criar_tabela_formatada_ano_estoque,
    titulo_centralizado,
    formatador_pt_br,
    criar_formatador_final,
    calcular_yoy,
    style_saldo_variacao,
)

municipio_de_interesse = None
CORES_MUNICIPIOS = {}
ordem_instrucao = []
ordem_faixa_salarial = []


def set_emprego_config(municipio, cores_municipios, ordem, ordem_faixa):
    """
    Configura valores específicos do município que antes eram importados
    do dashboard_core.config. Deve ser chamado pelo app.py antes de
    renderizar a página de emprego.
    """
    global \
        municipio_de_interesse, \
        CORES_MUNICIPIOS, \
        ordem_instrucao, \
        ordem_faixa_salarial
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}
    ordem_instrucao = ordem or []
    ordem_faixa_salarial = ordem_faixa or []


def formatar_data_index(idx):
    """Formata o índice de data para o padrão Mês/Ano curto (ex: Jan/23)."""
    return [f"{MESES_DIC[d.month][:3]}/{str(d.year)[2:]}" for d in idx]


# ==============================================================================
# FUNÇÕES DA PÁGINA DE EMPREGO
# ==============================================================================


def display_emprego_kpi_cards(df, municipio_interesse):
    """Exibe os cards de KPI de Emprego para um município específico."""

    titulo_centralizado(f"Saldo de Admissões e Demissões em {municipio_interesse}", 3)

    with st.container(border=False):
        filtro_municipio = df["municipio"] == municipio_interesse
        df_municipio = df[filtro_municipio]

        ult_ano = df_municipio["ano"].max()
        ult_mes = df_municipio[df_municipio["ano"] == ult_ano]["mes"].max()

        saldo_ult_mes = df_municipio[
            (df_municipio["ano"] == ult_ano) & (df_municipio["mes"] == ult_mes)
        ]["saldo_movimentacao"].sum()

        saldo_acu_ano = df_municipio[
            (df_municipio["ano"] == ult_ano) & (df_municipio["mes"] <= ult_mes)
        ]["saldo_movimentacao"].sum()

        col1, col2 = st.columns(2)
        col1.metric(
            label=f"{MESES_DIC[ult_mes]} de {ult_ano}",
            value=f"{saldo_ult_mes:,.0f}".replace(",", "."),
            delta=None,
            border=True,
        )
        col2.metric(
            label=f"Acumulado de Jan a {MESES_DIC[ult_mes][:3]} de {ult_ano}",
            value=f"{saldo_acu_ano:,.0f}".replace(",", "."),
            delta=None,
            border=True,
        )


def display_estoque_kpi_cards(df, municipio_interesse):
    """Exibe os cards de KPI de Estoque de Emprego para um município específico."""

    titulo_centralizado(f"Estoque de Emprego em {municipio_interesse}", 3)

    with st.container(border=False):
        filtro_municipio = df["municipio"] == municipio_interesse
        df_municipio = df[filtro_municipio]

        ult_ano = df_municipio["ano"].max()
        ult_mes = df_municipio[df_municipio["ano"] == ult_ano]["mes"].max()

        estoque_ult_mes = df_municipio[
            (df_municipio["ano"] == ult_ano) & (df_municipio["mes"] == ult_mes)
        ]["estoque_mensal"].sum()

        estoque_yoy = calcular_yoy(
            df=df,
            municipio=municipio_de_interesse,
            ultimo_ano=ult_ano,
            ultimo_mes=ult_mes,
            coluna="estoque_mensal",
            round=1,
        )

        st.metric(
            label=f"{MESES_DIC[ult_mes]} de {ult_ano}",
            value=f"{estoque_ult_mes:,.0f}".replace(",", "."),
            delta=f"{estoque_yoy}%".replace(".", ","),
            help="Taxa de Variação percentual em relação ao mesmo mês do ano anterior",
            border=True,
        )


def formatar_saldo_card(valor):
    valor_formatado = f"{abs(valor):,.0f}".replace(",", ".")
    if valor > 0:
        return f"+{valor_formatado}"
    elif valor < 0:
        return f"-{valor_formatado}"
    return "0"


def display_resumo_cards(df_caged, df_estoque, municipio_interesse):
    """Exibe os cards de resumo no topo da página com indicadores principais."""

    filtro_municipio_caged = df_caged["municipio"] == municipio_interesse
    df_municipio_caged = df_caged[filtro_municipio_caged]

    filtro_municipio_estoque = df_estoque["municipio"] == municipio_interesse
    df_municipio_estoque = df_estoque[filtro_municipio_estoque]

    ult_ano = int(df_municipio_caged["ano"].max())
    ult_mes = int(df_municipio_caged[df_municipio_caged["ano"] == ult_ano]["mes"].max())

    saldo_ult_mes = int(
        df_municipio_caged[
            (df_municipio_caged["ano"] == ult_ano) & (df_municipio_caged["mes"] == ult_mes)
        ]["saldo_movimentacao"].sum()
    )

    saldo_acu_ano = int(
        df_municipio_caged[
            (df_municipio_caged["ano"] == ult_ano) & (df_municipio_caged["mes"] <= ult_mes)
        ]["saldo_movimentacao"].sum()
    )

    estoque_ult_mes = int(
        df_municipio_estoque[
            (df_municipio_estoque["ano"] == ult_ano) & (df_municipio_estoque["mes"] == ult_mes)
        ]["estoque_mensal"].sum()
    )

    estoque_variacao = calcular_yoy(
        df=df_estoque,
        municipio=municipio_interesse,
        ultimo_ano=ult_ano,
        ultimo_mes=ult_mes,
        coluna="estoque_mensal",
        round=1,
    )

    saldo_formatado = formatar_saldo_card(saldo_ult_mes)
    acumulado_formatado = formatar_saldo_card(saldo_acu_ano)
    estoque_formatado = f"{estoque_ult_mes:,.0f}".replace(",", ".")

    if estoque_variacao is not None:
        estoque_delta = f"{estoque_variacao}%".replace(".", ",")
    else:
        estoque_delta = None

    def cor_saldo(valor):
        if valor > 0:
            return "#008A3D"
        elif valor < 0:
            return "#D92D20"
        return "#31333F"

    def render_card_saldo(label, valor_formatado, valor):
        cor = cor_saldo(valor)
        st.markdown(
            f"""
            <div style="
                border: 1px solid rgba(49, 51, 63, 0.2);
                border-radius: 0.5rem;
                padding: 1.25rem;
                text-align: center;
                min-height: 118px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="
                    font-size: 1rem;
                    margin-bottom: 0.35rem;
                    color: #000;
                ">
                    {label}
                </div>
                <div style="
                    font-size: 1.35rem;
                    font-weight: 600;
                    color: {cor};
                ">
                    {valor_formatado}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        render_card_saldo(
            label=f"Saldo no Mês em {MESES_DIC[ult_mes]} de {ult_ano}",
            valor_formatado=saldo_formatado,
            valor=saldo_ult_mes,
        )

    with col2:
        render_card_saldo(
            label=f"Saldo Acumulado de Jan a {MESES_DIC[ult_mes][:3]} de {ult_ano}",
            valor_formatado=acumulado_formatado,
            valor=saldo_acu_ano,
        )

    with col3:
        st.metric(
            label=f"Estoque de Emprego Estimado em {MESES_DIC[ult_mes]} de {ult_ano}",
            value=estoque_formatado,
            delta=estoque_delta,
            delta_color="normal",
            help="Taxa de variação percentual em relação ao mesmo mês do ano anterior",
            border=True,
        )


def expander_emprego_callback():
    """Garante que o expander de emprego permaneça aberto após a interação."""
    st.session_state.emprego_expander_state = True


@st.cache_data
def preparar_dados_graficos_emprego(df_filtrado):
    """
    Recebe um DataFrame filtrado e retorna todos os DataFrames pivotados e prontos
    para os gráficos do expander de emprego. Esta função é cacheada para performance.
    """
    if df_filtrado.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), None, None

    # Evolução Mensal
    df_hist = (
        df_filtrado.assign(
            date=lambda x: pd.to_datetime(
                x["ano"].astype(str) + "-" + x["mes"].astype(str).str.zfill(2) + "-01"
            )
        )
        .pivot_table(
            index="date",
            columns="municipio",
            values="saldo_movimentacao",
            aggfunc="sum",
            observed=False,
            fill_value=0,
        )
        .sort_index()
    )

    ult_ano = df_filtrado["ano"].max()
    ult_mes = df_filtrado[df_filtrado["ano"] == ult_ano]["mes"].max()

    # Mês

    df_mes = (
        df_filtrado[df_filtrado["mes"] == ult_mes]
        .pivot_table(
            index="ano",
            columns="municipio",
            values="saldo_movimentacao",
            aggfunc="sum",
            observed=False,
            fill_value=0,
        )
        .sort_index()
    )
    df_mes.index = MESES_DIC[ult_mes][:3] + "/" + df_mes.index.astype(str).str.slice(-2)

    # Acumulado no Ano
    df_acum = (
        df_filtrado[df_filtrado["mes"] <= ult_mes]
        .pivot_table(
            index="ano",
            columns="municipio",
            values="saldo_movimentacao",
            aggfunc="sum",
            observed=False,
            fill_value=0,
        )
        .sort_index()
    )
    df_acum.index = (
        "Jan-" + MESES_DIC[ult_mes][:3] + "/" + df_acum.index.astype(str).str.slice(-2)
    )

    # Anual
    ano_completo = checar_ult_ano_completo(df_filtrado)
    df_anual = (
        df_filtrado[df_filtrado["ano"] <= ano_completo]
        .pivot_table(
            index="ano",
            columns="municipio",
            values="saldo_movimentacao",
            aggfunc="sum",
            observed=False,
            fill_value=0,
        )
        .sort_index(ascending=False)
    )

    return df_hist, df_mes, df_acum, df_anual, ult_ano, ult_mes


def display_emprego_municipios_expander(
    df,
    categoria,
):
    """Exibe o expander com análise de saldo de emprego para múltiplos municípios."""
    with st.expander(
        "Saldo de Emprego por Município",
        expanded=st.session_state.emprego_expander_state,
    ):
        df_hist, df_mes, df_acum, df_anual, ult_ano, ult_mes = (
            preparar_dados_graficos_emprego(df)
        )
        anos_disponiveis = sorted(df["ano"].unique().tolist(), reverse=True)

        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = "main_tab_nav_emprego_mun"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Evolução Mensal"

        aba_selecionada = st.pills(
            "Selecione o tipo de análise temporal:",
            options=["Evolução Mensal", "Mês", "Acumulado no Ano", "Anual"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Evolução Mensal"

        if aba_selecionada == "Evolução Mensal":
            ANO_SELECIONADO = st.selectbox(
                "Selecione o ano para o gráfico:",
                options=anos_disponiveis,
                index=0,
                key="hist_ano_emprego",
            )

            df_hist = df_hist[df_hist.index.year == ANO_SELECIONADO]
            if not df_hist.empty:
                df_hist.index = [
                    f"{MESES_DIC[date.month][:3]}/{str(date.year)[2:]}"
                    for date in df_hist.index
                ]

            titulo_centralizado(f"Saldo de Emprego Mensal em {ANO_SELECIONADO}", 5)

            fig_hist = criar_grafico_barras(
                df=df_hist,
                titulo="",
                label_y="Saldo de Admissões e Demissões",
                barmode="group",
                height=400,
                data_label_format=",.0f",
                hover_label_format=",.0f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig_hist, width="stretch")

        elif aba_selecionada == "Mês":
            titulo_centralizado(f"Saldo de Emprego em {MESES_DIC[ult_mes]}", 5)
            fig_mes = criar_grafico_barras(
                df=df_mes,
                titulo="",
                label_y="Saldo de Admissões e Demissões",
                barmode="group",
                height=400,
                data_label_format=",.0f",
                hover_label_format=",.0f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig_mes, width="stretch")

        elif aba_selecionada == "Acumulado no Ano":
            titulo_centralizado(
                f"Saldo de Emprego de Janeiro a {MESES_DIC[ult_mes]}", 5
            )
            fig_acum = criar_grafico_barras(
                df=df_acum,
                titulo="",
                label_y="Saldo de Admissões e Demissões",
                barmode="group",
                height=400,
                data_label_format=",.0f",
                hover_label_format=",.0f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig_acum, width="stretch")

        elif aba_selecionada == "Anual":
            titulo_centralizado("Saldo Emprego Anual", 5)

            fig_anual = criar_grafico_barras(
                df=df_anual,
                titulo="",
                label_y="Saldo de Admissões e Demissões",
                barmode="group",
                height=400,
                data_label_format=",.0f",
                hover_label_format=",.0f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig_anual, width="stretch")


@st.cache_data
def preparar_dados_graficos_estoque(df_filtrado):
    """
    Recebe um DataFrame filtrado e retorna todos os DataFrames pivotados e prontos
    para os gráficos do expander de estoque de emprego.
    Otimizada para criar as estruturas de dados em memória de forma eficiente.
    """
    if df_filtrado.empty:
        empty_df = pd.DataFrame()
        return (
            empty_df,
            empty_df,  # Histórico
            empty_df,
            empty_df,  # Mês
            empty_df,
            empty_df,  # Anual
            None,
            None,  # Ultimo Ano/Mes
        )

    # Garante ordenação cronológica correta
    df_proc = df_filtrado.assign(
        date=lambda x: pd.to_datetime(
            x["ano"].astype(str) + "-" + x["mes"].astype(str).str.zfill(2) + "-01"
        )
    ).sort_values("date")

    ult_ano = df_filtrado["ano"].max()
    ult_mes = df_filtrado[df_filtrado["ano"] == ult_ano]["mes"].max()

    # Função auxiliar interna para pivotar
    def pivotar(df_in, index_col, value_col, ascending=True):
        # Para dados de estoque, usar mean para evitar soma incorreta de duplicatas
        agg_func = "mean" if "estoque" in value_col else "sum"

        return df_in.pivot_table(
            index=index_col,
            columns="municipio",
            values=value_col,
            aggfunc=agg_func,
            observed=False,
            fill_value=0,
        ).sort_index(ascending=ascending)

    # --- Evolução Mensal (Histórico) ---
    df_hist = pivotar(df_proc, "date", "estoque_mensal")
    df_hist_yoy = pivotar(df_proc, "date", "estoque_mensal_yoy")

    # --- Mês Específico (Comparativo do mesmo mês em vários anos) ---
    df_mes_filtrado = df_proc[df_proc["mes"] == ult_mes]

    df_mes = pivotar(df_mes_filtrado, "ano", "estoque_mensal")
    df_mes_yoy = pivotar(df_mes_filtrado, "ano", "estoque_mensal_yoy")

    # Formatação do índice para "Jan/23", "Jan/24" etc.
    prefixo_mes = MESES_DIC[ult_mes][:3]

    # Aplicar formatação de índice
    idx_fmt = prefixo_mes + "/" + df_mes.index.astype(str).str.slice(-2)
    df_mes.index = idx_fmt

    idx_fmt_yoy = prefixo_mes + "/" + df_mes_yoy.index.astype(str).str.slice(-2)
    df_mes_yoy.index = idx_fmt_yoy

    # --- Anual (Fechamento Dezembro) ---
    ano_completo = checar_ult_ano_completo(df_filtrado)
    # Filtra até o último ano completo e apenas mês 12
    df_anual_filtrado = df_proc[
        (df_proc["ano"] <= ano_completo) & (df_proc["mes"] == 12)
    ]

    df_anual = pivotar(df_anual_filtrado, "ano", "estoque_mensal", ascending=False)
    df_anual_yoy = pivotar(
        df_anual_filtrado, "ano", "estoque_mensal_yoy", ascending=False
    )

    return (
        df_hist,
        df_hist_yoy,
        df_mes,
        df_mes_yoy,
        df_anual,
        df_anual_yoy,
        ult_ano,
        ult_mes,
    )


def display_estoque_municipios_expander(df):
    """Exibe o expander com análise de estoque de emprego para múltiplos municípios."""

    with st.expander("Estoque de Emprego Estimado por Município", expanded=False):
        (
            df_hist,
            df_hist_yoy,
            df_mes,
            df_mes_yoy,
            df_anual,
            df_anual_yoy,
            ult_ano,
            ult_mes,
        ) = preparar_dados_graficos_estoque(df)

        if df_hist.empty:
            st.warning("Sem dados disponíveis para exibição.")
            return

        anos_disponiveis = sorted(df["ano"].unique().tolist(), reverse=True)

        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = "main_tab_nav_estoque_mun"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Evolução Mensal"

        aba_selecionada = st.pills(
            "Selecione o tipo de análise temporal:",
            options=["Evolução Mensal", "Mês", "Anual"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Evolução Mensal"

        # --- ABA 1: Evolução Mensal ---
        if aba_selecionada == "Evolução Mensal":
            col1, col2 = st.columns([1, 1])

            with col1:
                ANO_SELECIONADO = st.selectbox(
                    "Selecione o ano para o gráfico:",
                    options=anos_disponiveis,
                    index=0,
                    key="hist_ano_estoque_mun",
                )

            with col2:
                metric_mode_hist = (
                    st.segmented_control(
                        "Métrica:",
                        options=["Estoque", "Variação (%)"],
                        selection_mode="single",
                        default="Estoque",
                        key="metric_mode_estoque_hist_mun",
                    )
                    or "Estoque"
                )

            # Filtragem Visual (apenas para o gráfico)
            mask_ano = df_hist.index.year == ANO_SELECIONADO
            df_hist_view = df_hist[mask_ano].copy()
            df_hist_yoy_view = df_hist_yoy[mask_ano].copy()

            # Formatação do índice (Eixo X)
            if not df_hist_view.empty:
                df_hist_view.index = formatar_data_index(df_hist_view.index)
            if not df_hist_yoy_view.empty:
                df_hist_yoy_view.index = formatar_data_index(df_hist_yoy_view.index)

            if metric_mode_hist == "Estoque":
                titulo_centralizado(
                    f"Evolução Mensal do Estoque de Emprego em {ANO_SELECIONADO}", 5
                )
                fig = criar_grafico_barras(
                    df=df_hist_view,
                    titulo="",
                    label_y="Estoque de Emprego",
                    barmode="group",
                    height=400,
                    data_label_format=",.0f",
                    hover_label_format=",.0f",
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, width="stretch")

            else:  # Variação
                titulo_centralizado(
                    f"Variação Mensal do Estoque de Emprego em {ANO_SELECIONADO}", 5
                )
                fig = criar_grafico_barras(
                    df=df_hist_yoy_view,
                    titulo="",
                    label_y="Variação em relação ao mesmo período do ano anterior (%)",
                    barmode="group",
                    height=400,
                    data_label_format=",.1f",
                    hover_label_format=",.1f",
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, width="stretch")

        # --- ABA 2: Mês (Comparativo Histórico do Mês Atual) ---
        elif aba_selecionada == "Mês":
            col_m1, col_m2 = st.columns([2, 1])
            with col_m1:
                metric_mode_mes = (
                    st.segmented_control(
                        "Métrica:",
                        options=["Estoque", "Variação (%)"],
                        selection_mode="single",
                        default="Estoque",
                        key="metric_mode_estoque_mes_mun",
                        label_visibility="collapsed",
                    )
                    or "Estoque"
                )

            if metric_mode_mes == "Estoque":
                titulo_centralizado(f"Estoque de Emprego em {MESES_DIC[ult_mes]}", 5)
                fig = criar_grafico_barras(
                    df=df_mes,
                    titulo="",
                    label_y="Estoque de Emprego",
                    barmode="group",
                    height=400,
                    data_label_format=",.0f",
                    hover_label_format=",.0f",
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, width="stretch")
            else:
                titulo_centralizado(
                    f"Variação percentual do Estoque de Emprego em {MESES_DIC[ult_mes]}",
                    5,
                )
                fig = criar_grafico_barras(
                    df=df_mes_yoy,
                    titulo="",
                    label_y="Variação em relação ao mesmo período do ano anterior (%)",
                    barmode="group",
                    height=400,
                    data_label_format=",.1f",
                    hover_label_format=",.1f",
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, width="stretch")

        # --- ABA 3: Anual  ---
        elif aba_selecionada == "Anual":
            col_a1, col_a2 = st.columns([2, 1])
            with col_a1:
                metric_mode_anual = (
                    st.segmented_control(
                        "Métrica:",
                        options=["Estoque", "Variação (%)"],
                        selection_mode="single",
                        default="Estoque",
                        key="metric_mode_estoque_anual_mun",
                        label_visibility="collapsed",
                    )
                    or "Estoque"
                )

            if metric_mode_anual == "Estoque":
                titulo_centralizado("Estoque de Emprego Anual", 5)
                fig = criar_grafico_barras(
                    df=df_anual,
                    titulo="",
                    label_y="Estoque de Emprego",
                    barmode="group",
                    height=400,
                    data_label_format=",.0f",
                    hover_label_format=",.0f",
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, width="stretch")
            else:
                titulo_centralizado(
                    "Variação percentual do Estoque de Emprego Anual", 5
                )

                fig = criar_grafico_barras(
                    df=df_anual_yoy,
                    titulo="",
                    label_y="Variação em relação ao mesmo período do ano anterior (%)",
                    barmode="group",
                    height=400,
                    data_label_format=",.1f",
                    hover_label_format=",.1f",
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, width="stretch")


@st.cache_data
def preparar_dados_categoria_emprego(df_categoria, index_col, sort_order=None):
    """
    Prepara os DataFrames de Mês, Acumulado e Ano para uma categoria de emprego.
    Aplica ordenação customizada se fornecida.
    """
    if df_categoria.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Aplica ordenação categórica se uma ordem for especificada
    if sort_order:
        df_categoria[index_col] = pd.Categorical(
            df_categoria[index_col], categories=sort_order, ordered=True
        )
        df_categoria = df_categoria.dropna(subset=[index_col])

    ult_ano = int(df_categoria["ano"].max())
    ult_mes = int(df_categoria[df_categoria["ano"] == ult_ano]["mes"].max())

    # Delega a criação das tabelas para as funções já cacheadas de utils
    df_mes = criar_tabela_formatada_mes(
        df=df_categoria,
        index_col=index_col,
        ult_ano=ult_ano,
        ult_mes=ult_mes,
        coluna_agregacao="saldo_movimentacao",
    ).sort_index()
    df_acum = criar_tabela_formatada(
        df=df_categoria,
        index_col=index_col,
        ult_ano=ult_ano,
        ult_mes=ult_mes,
        coluna_agregacao="saldo_movimentacao",
    ).sort_index()
    df_anual = criar_tabela_formatada_ano(
        df=df_categoria, index_col=index_col, coluna_agregacao="saldo_movimentacao"
    ).sort_index()

    return df_mes, df_acum, df_anual


def display_emprego_categoria_expander(
    df_sexo, df_faixa_etaria, df_raca_cor, df_grau_instrucao, ult_mes
):
    """Exibe o expander com análise de saldo de emprego por categoria."""
    with st.expander(
        f"Saldo de Emprego por Categoria em {municipio_de_interesse}",
        expanded=False,
    ):
        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = "main_tab_nav_emprego_cat"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Sexo"

        aba_selecionada = st.pills(
            "Selecione uma categoria:",
            options=["Sexo", "Raça/Cor", "Faixa Etária", "Grau de Instrução"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Sexo"

        def render_categoria_tab(
            df, index_col, titulo, sort_order=None, color_map=None
        ):
            """Função interna para renderizar o conteúdo de cada aba de categoria."""
            df_mes, df_acum, df_anual = preparar_dados_categoria_emprego(
                df, index_col, sort_order
            )

            view_mode = (
                st.segmented_control(
                    "Selecione a Análise:",
                    options=["Último Mês", "Acumulado no Ano", "Anual"],
                    selection_mode="single",
                    default="Último Mês",
                    key=f"view_mode_cat_{index_col}",
                )
                or "Último Mês"
            )

            if view_mode == "Último Mês":
                titulo_centralizado(
                    f"Saldo de Emprego em {MESES_DIC[ult_mes]} por {titulo}",
                    5,
                )
                fig = criar_grafico_barras(
                    df=df_mes.T,
                    titulo="",
                    label_y="Saldo de Admissões e Demissões",
                    color_map=color_map,
                    data_label_format=",.0f",
                    hover_label_format=",.0f",
                )
                st.plotly_chart(fig, width="stretch")
            elif view_mode == "Acumulado no Ano":
                titulo_centralizado(
                    f"Saldo de Emprego de Janeiro a {MESES_DIC[ult_mes]} por {titulo}",
                    5,
                )
                fig = criar_grafico_barras(
                    df=df_acum.T,
                    titulo="",
                    label_y="Saldo de Admissões e Demissões",
                    color_map=color_map,
                    data_label_format=",.0f",
                    hover_label_format=",.0f",
                )
                st.plotly_chart(fig, width="stretch")
            elif view_mode == "Anual":
                titulo_centralizado(f"Saldo de Anual por {titulo}", 5)
                fig = criar_grafico_barras(
                    df=df_anual.T,
                    titulo="",
                    label_y="Saldo de Admissões e Demissões",
                    color_map=color_map,
                    data_label_format=",.0f",
                    hover_label_format=",.0f",
                )
                st.plotly_chart(fig, width="stretch")

        if aba_selecionada == "Sexo":
            render_categoria_tab(
                df_sexo,
                "sexo",
                "Sexo",
                color_map={"Masculino": "#4C82F7", "Feminino": "#FF6BE1"},
            )
        elif aba_selecionada == "Raça/Cor":
            render_categoria_tab(df_raca_cor, "raca_cor", "Raça/Cor")
        elif aba_selecionada == "Faixa Etária":
            render_categoria_tab(df_faixa_etaria, "faixa_etaria", "Faixa Etária")
        elif aba_selecionada == "Grau de Instrução":
            render_categoria_tab(
                df_grau_instrucao,
                "grau_instrucao",
                "Grau de Instrução",
                sort_order=ordem_instrucao,
            )


@st.cache_data
def preparar_dados_categoria_estoque(
    df_categoria,
    index_col,
    sort_order=None,
    coluna_agregacao="estoque_mensal",
    usar_dezembro_anual=False,
):
    """
    Prepara os DataFrames de Mês e Ano para uma categoria de emprego.

    OTIMIZAÇÃO:
    Agora apenas formata e pivota os dados, pois a coluna de variação (yoy)
    já vem calculada do banco de dados.
    """
    if df_categoria.empty:
        return pd.DataFrame(), pd.DataFrame()

    # 1. Aplica ordenação categórica se especificada
    if sort_order:
        df_categoria = df_categoria.copy()
        df_categoria[index_col] = pd.Categorical(
            df_categoria[index_col], categories=sort_order, ordered=True
        )
        df_categoria = df_categoria.dropna(subset=[index_col])

    # Definição de datas limites
    ult_ano = int(df_categoria["ano"].max())
    ult_mes = int(df_categoria[df_categoria["ano"] == ult_ano]["mes"].max())

    # 2. Pivotagem e Formatação

    # Tabela Mês (Comparativo do mesmo mês em vários anos)
    df_mes = criar_tabela_formatada_mes(
        df=df_categoria,
        index_col=index_col,
        ult_ano=ult_ano,
        ult_mes=ult_mes,
        coluna_agregacao=coluna_agregacao,
    ).sort_index()

    # Tabela Anual
    if usar_dezembro_anual:
        df_anual = criar_tabela_formatada_ano_estoque(
            df=df_categoria, index_col=index_col, coluna_agregacao=coluna_agregacao
        ).sort_index()
    else:
        df_anual = criar_tabela_formatada_ano(
            df=df_categoria, index_col=index_col, coluna_agregacao=coluna_agregacao
        ).sort_index()

    return df_mes, df_anual


def display_estoque_categoria_expander(
    df_sexo, df_faixa_etaria, df_raca_cor, df_grau_instrucao, ult_mes
):
    """Exibe o expander com análise de estoque de emprego por categoria (versão Otimizada DB)."""

    with st.expander(
        f"Estoque de Emprego por Categoria em {municipio_de_interesse}",
        expanded=False,
    ):
        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = "main_tab_nav_estoque_cat"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Sexo"

        aba_selecionada = st.pills(
            "Selecione uma categoria:",
            options=["Sexo", "Raça/Cor", "Faixa Etária", "Grau de Instrução"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Sexo"

        def render_estoque_categoria_tab(
            df, index_col, titulo, sort_order=None, color_map=None
        ):
            """Função interna para renderizar o conteúdo de cada aba de categoria."""

            # --- CONTROLES VISUAIS ---
            col1, col2 = st.columns(2)

            with col1:
                metric_mode = (
                    st.segmented_control(
                        "Métrica:",
                        options=["Estoque", "Variação (%)"],
                        selection_mode="single",
                        default="Estoque",
                        key=f"metric_mode_estoque_cat_{index_col}",
                    )
                    or "Estoque"
                )

            with col2:
                view_mode = (
                    st.segmented_control(
                        "Visualização:",
                        options=["Mês", "Anual"],
                        selection_mode="single",
                        default="Mês",
                        key=f"view_mode_estoque_cat_{index_col}",
                    )
                    or "Mês"
                )

            # --- CONFIGURAÇÃO DOS PARÂMETROS ---
            if metric_mode == "Variação (%)":
                coluna_agregacao = "estoque_mensal_yoy"
                usar_dezembro = True
                data_fmt = ",.1f"
                label_y = "Variação em relação ao mesmo período do ano anterior (%)"
            else:
                coluna_agregacao = "estoque_mensal"
                usar_dezembro = True  # Para estoque anual, sempre usar dezembro
                data_fmt = ",.0f"
                label_y = "Estoque"

            # --- PREPARAÇÃO DOS DADOS ---
            df_mes, df_anual = preparar_dados_categoria_estoque(
                df, index_col, sort_order, coluna_agregacao, usar_dezembro
            )

            # --- RENDERIZAÇÃO DOS GRÁFICOS ---
            df_to_plot = df_mes if view_mode == "Mês" else df_anual

            # Ajuste de título dinâmico
            if view_mode == "Mês" and metric_mode == "Estoque":
                titulo_grafico = f"Estoque em {MESES_DIC[ult_mes]} por {titulo}"
                key_suffix = "mes"
            elif view_mode == "Mês" and metric_mode == "Variação (%)":
                titulo_grafico = (
                    f"Variação do Estoque em {MESES_DIC[ult_mes]} por {titulo} (%)"
                )
                key_suffix = "mes_var"
            elif view_mode == "Anual" and metric_mode == "Estoque":
                titulo_grafico = f"Estoque Anual por {titulo}"
                key_suffix = "anual"
            else:
                titulo_grafico = f"Variação do Estoque Anual por {titulo} (%)"
                key_suffix = "anual_var"

            if df_to_plot.empty:
                st.warning("Sem dados para exibir nesta visualização.")
            else:
                titulo_centralizado(titulo_grafico, 5)

                fig = criar_grafico_barras(
                    df=df_to_plot.T,
                    titulo="",
                    label_y=label_y,
                    color_map=color_map,
                    data_label_format=data_fmt,
                    hover_label_format=data_fmt,
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                    key=f"estoque_{index_col}_{key_suffix}",
                )

        # --- CHAMADAS PARA CADA ABA ---
        if aba_selecionada == "Sexo":
            render_estoque_categoria_tab(
                df_sexo,
                "sexo",
                "Sexo",
                color_map={"Masculino": "#4C82F7", "Feminino": "#FF6BE1"},
            )
        elif aba_selecionada == "Raça/Cor":
            render_estoque_categoria_tab(df_raca_cor, "raca_cor", "Raça/Cor")
        elif aba_selecionada == "Faixa Etária":
            render_estoque_categoria_tab(
                df_faixa_etaria, "faixa_etaria", "Faixa Etária"
            )
        elif aba_selecionada == "Grau de Instrução":
            render_estoque_categoria_tab(
                df_grau_instrucao,
                "grau_instrucao",
                "Grau de Instrução",
                sort_order=ordem_instrucao,
            )


@st.cache_data
def preparar_dados_graficos_cnae(df_cnae, index_col):
    """
    Prepara os DataFrames para as visualizações de Mês, Acumulado e Ano para dados de CNAE.
    """
    df_mes, df_acum, df_anual = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if not df_cnae.empty:
        ult_ano = df_cnae["ano"].max()
        ult_mes = df_cnae[df_cnae["ano"] == ult_ano]["mes"].max()

        df_mes = criar_tabela_formatada_mes(
            df=df_cnae,
            index_col=index_col,
            ult_ano=ult_ano,
            ult_mes=ult_mes,
            coluna_agregacao="saldo_movimentacao",
        )

        df_acum = criar_tabela_formatada(
            df=df_cnae,
            index_col=index_col,
            ult_ano=ult_ano,
            ult_mes=ult_mes,
            coluna_agregacao="saldo_movimentacao",
        )

        df_anual = criar_tabela_formatada_ano(
            df=df_cnae, index_col=index_col, coluna_agregacao="saldo_movimentacao"
        )

    return df_mes, df_acum, df_anual


def display_emprego_cnae_expander(df_cnae_foco):
    """Exibe o expander com análise de saldo de emprego por Setor e CNAE"""
    with st.expander(
        f"Saldo de Emprego por Setor Econômico em {municipio_de_interesse}",
        expanded=False,
    ):
        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = "main_tab_nav_emprego_cnae"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Setor"

        aba_selecionada = st.pills(
            "Selecione o nível de agregação:",
            options=["Setor", "CNAE - Grupo", "CNAE - Subclasse"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Setor"

        def render_cnae_content(index_col, titulo_categoria, show_graph=True):
            """Função interna para renderizar o conteúdo de cada aba de CNAE."""
            df_mes, df_acum, df_anual = preparar_dados_graficos_cnae(
                df_cnae_foco, index_col
            )

            ult_ano = int(df_cnae_foco["ano"].max())
            ult_mes = int(df_cnae_foco[df_cnae_foco["ano"] == ult_ano]["mes"].max())

            view_mode = (
                st.segmented_control(
                    "Selecione a Análise:",
                    options=["Último Mês", "Acumulado no Ano", "Anual"],
                    selection_mode="single",
                    default="Último Mês",
                    key=f"view_mode_cnae_{index_col}",
                )
                or "Último Mês"
            )

            df_map = {
                "Último Mês": df_mes,
                "Acumulado no Ano": df_acum,
                "Anual": df_anual,
            }
            df_selecionado = df_map[view_mode]

            if view_mode == "Último Mês":
                titulo_centralizado(
                    f"Saldo em {MESES_DIC[ult_mes]} por {titulo_categoria}", 5
                )
            elif view_mode == "Acumulado no Ano":
                titulo_centralizado(f"Saldo Acumulado no Ano por {titulo_categoria}", 5)
            elif view_mode == "Anual":
                titulo_centralizado(f"Saldo Anual por {titulo_categoria}", 5)

            # Lógica para exibir gráfico ou tabela
            if show_graph:
                fig = criar_grafico_barras(
                    df=df_selecionado.sort_index().T,
                    titulo="",
                    label_y="Saldo de Admissões e Demissões",
                    data_label_format=",.0f",
                    hover_label_format=",.0f",
                )
                st.plotly_chart(fig, width="stretch")
            else:
                # --- USANDO A FUNÇÃO DO UTILS PARA O ESTILO ---
                styler = df_selecionado.style.format(
                    lambda x: f"{x:,.0f}".replace(",", ".")
                ).map(style_saldo_variacao)

                st.dataframe(styler, width="stretch")

        if aba_selecionada == "Setor":
            render_cnae_content("grupo_ibge", show_graph=True, titulo_categoria="Setor")
        elif aba_selecionada == "CNAE - Grupo":
            render_cnae_content(
                "grupo", show_graph=False, titulo_categoria="CNAE - Grupo"
            )
        elif aba_selecionada == "CNAE - Subclasse":
            render_cnae_content(
                "subclasse", show_graph=False, titulo_categoria="CNAE - Subclasse"
            )


@st.cache_data
def preparar_dados_graficos_estoque_cnae(
    df_cnae, index_col, coluna_agregacao="estoque_mensal", usar_dezembro_anual=True
):
    """
    Prepara os DataFrames de Mês e Ano para dados de CNAE (Estoque ou Variação).
    """
    df_mes, df_anual = pd.DataFrame(), pd.DataFrame()

    if df_cnae.empty:
        return df_mes, df_anual

    ult_ano = df_cnae["ano"].max()
    ult_mes = df_cnae[df_cnae["ano"] == ult_ano]["mes"].max()

    # Tabela Mês
    df_mes = criar_tabela_formatada_mes(
        df=df_cnae,
        index_col=index_col,
        ult_ano=ult_ano,
        ult_mes=ult_mes,
        coluna_agregacao=coluna_agregacao,
    )

    # Tabela Anual
    if usar_dezembro_anual:
        df_anual = criar_tabela_formatada_ano_estoque(
            df=df_cnae, index_col=index_col, coluna_agregacao=coluna_agregacao
        )
    else:
        df_anual = criar_tabela_formatada_ano(
            df=df_cnae, index_col=index_col, coluna_agregacao=coluna_agregacao
        )

    return df_mes, df_anual


def display_estoque_cnae_expander(df_cnae_setor, df_cnae_grupo, df_cnae_subclasse):
    """
    Exibe o expander com análise de estoque de emprego por Setor e CNAE.
    A ordenação das linhas é sempre baseada no volume de Estoque (do maior para o menor),
    mesmo quando se visualiza a Variação.
    """
    with st.expander(
        f"Estoque de Emprego Estimado por Setor Econômico em {municipio_de_interesse}",
        expanded=False,
    ):
        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = "main_tab_nav_estoque_cnae"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Setor"

        aba_selecionada = st.pills(
            "Selecione o nível de agregação:",
            options=["Setor", "CNAE - Grupo", "CNAE - Subclasse"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Setor"

        def render_cnae_content(df, index_col, titulo_categoria, show_graph=True):
            """Função interna para renderizar o conteúdo de cada aba de CNAE."""
            if df.empty:
                st.warning("Sem dados disponíveis para esta categoria.")
                return

            ult_mes = int(df[df["ano"] == df["ano"].max()]["mes"].max())

            col1, col2 = st.columns(2)

            with col1:
                metric_mode = (
                    st.segmented_control(
                        "Métrica:",
                        options=["Estoque", "Variação (%)"],
                        selection_mode="single",
                        default="Estoque",
                        key=f"metric_mode_cnae_estoque_{index_col}",
                    )
                    or "Estoque"
                )

            with col2:
                view_mode = (
                    st.segmented_control(
                        "Visualização:",
                        options=["Mês", "Anual"],
                        selection_mode="single",
                        default="Mês",
                        key=f"view_mode_cnae_estoque_{index_col}",
                    )
                    or "Mês"
                )

            # ==============================================================
            # PASSO 1: DEFINIR A ORDENAÇÃO (SEMPRE PELO ESTOQUE)
            # ==============================================================
            df_mes_ref, df_anual_ref = preparar_dados_graficos_estoque_cnae(
                df_cnae=df,
                index_col=index_col,
                coluna_agregacao="estoque_mensal",
                usar_dezembro_anual=True,
            )

            df_ref = df_mes_ref if view_mode == "Mês" else df_anual_ref

            ordenacao_fixa = []
            if not df_ref.empty:
                col_ordenacao = df_ref.columns[-1]
                ordenacao_fixa = df_ref.sort_values(
                    by=col_ordenacao, ascending=False
                ).index.tolist()

            # ==============================================================
            # PASSO 2: PREPARAR OS DADOS DE EXIBIÇÃO
            # ==============================================================
            if metric_mode == "Variação (%)":
                coluna_agregacao = "estoque_mensal_yoy"
                usar_dezembro = True
                label_y = "Variação em relação ao mesmo período do ano anterior (%)"
                data_fmt = ",.1f"
                hover_fmt = ",.1f"

                def table_fmt(x):
                    if pd.isna(x) or x == float("inf"):
                        return "-"
                    return (
                        f"{x:,.1f}%".replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )

                use_custom_style = True
            else:
                coluna_agregacao = "estoque_mensal"
                usar_dezembro = True
                label_y = "Estoque de Emprego"
                data_fmt = ",.0f"
                hover_fmt = ",.0f"

                def table_fmt(x):
                    if pd.isna(x):
                        return "-"
                    return f"{x:,.0f}".replace(",", ".")

                use_custom_style = False

            df_mes, df_anual = preparar_dados_graficos_estoque_cnae(
                df_cnae=df,
                index_col=index_col,
                coluna_agregacao=coluna_agregacao,
                usar_dezembro_anual=usar_dezembro,
            )

            df_to_plot = df_mes if view_mode == "Mês" else df_anual

            # ==============================================================
            # PASSO 3: APLICAR A ORDENAÇÃO FIXA E EXIBIR
            # ==============================================================
            if ordenacao_fixa and not df_to_plot.empty:
                indices_validos = [i for i in ordenacao_fixa if i in df_to_plot.index]
                df_to_plot = df_to_plot.reindex(indices_validos)

            df_to_plot.index.name = titulo_categoria

            if view_mode == "Mês" and metric_mode == "Estoque":
                titulo_final = (
                    f"Estoque de Emprego em {MESES_DIC[ult_mes]} por {titulo_categoria}"
                )
            elif view_mode == "Mês" and metric_mode == "Variação (%)":
                titulo_final = f"Variação Percentual do Estoque de Emprego em {MESES_DIC[ult_mes]} por {titulo_categoria}"
            elif view_mode == "Anual" and metric_mode == "Estoque":
                titulo_final = f"Estoque de Emprego Anual por {titulo_categoria}"
            else:
                titulo_final = f"Variação Percentual do Estoque de Emprego Anual por {titulo_categoria}"

            titulo_centralizado(titulo_final, 5)

            if show_graph:
                fig = criar_grafico_barras(
                    df=df_to_plot.T,
                    titulo="",
                    label_y=label_y,
                    data_label_format=data_fmt,
                    hover_label_format=hover_fmt,
                    barmode="group",
                )
                st.plotly_chart(
                    fig, width="stretch", key=f"chart_cnae_estoque_{index_col}"
                )
            else:
                if df_to_plot.empty:
                    st.warning("Sem dados disponíveis para os filtros selecionados.")
                else:
                    styler = df_to_plot.style.format(table_fmt)

                    if use_custom_style:
                        styler = styler.map(style_saldo_variacao)
                    else:
                        styler = styler.background_gradient(cmap="Blues", axis=0)

                    st.dataframe(
                        styler,
                        width="stretch",
                        height=500,
                    )

        if aba_selecionada == "Setor":
            render_cnae_content(
                df=df_cnae_setor,
                index_col="setor",
                titulo_categoria="Setor Econômico",
                show_graph=True,
            )

        elif aba_selecionada == "CNAE - Grupo":
            render_cnae_content(
                df=df_cnae_grupo,
                index_col="grupo",
                titulo_categoria="CNAE - Grupo",
                show_graph=False,
            )

        elif aba_selecionada == "CNAE - Subclasse":
            render_cnae_content(
                df=df_cnae_subclasse,
                index_col="subclasse",
                titulo_categoria="CNAE - Subclasse",
                show_graph=False,
            )


@st.cache_data
def preparar_dados_renda_grafico(df, coluna_agregacao, coluna_valor):
    """Prepara (pivota) os dados de renda para um gráfico anual."""
    if df is None or df.empty:
        return pd.DataFrame()

    df_pivot = df.pivot_table(
        index="ano",
        columns=coluna_agregacao,
        values=coluna_valor,
        aggfunc="mean",
        observed=False,
        fill_value=0,
    ).sort_index()
    return df_pivot


@st.cache_data
def preparar_dados_ranking_renda(df_filtrado, coluna_selecionada):
    """Prepara os dados para o gráfico de ranking de renda."""
    if df_filtrado.empty:
        return pd.DataFrame()

    df_pivot = df_filtrado.pivot_table(
        index="ano",
        columns="municipio",
        values=coluna_selecionada,
        aggfunc="mean",
        observed=False,
        fill_value=0,
    ).sort_index()

    df_pivot.index = df_pivot.index.astype(str)

    return df_pivot


@st.cache_data
def preparar_dados_renda_faixa_salarial(df):
    st.dataframe(df)


def render_renda_grafico_tab(
    df,
    coluna_agregacao,
    coluna_valor,
    titulo_grafico,
    data_format,
    hover_format,
    color_map=None,
    sort_order=None,
):
    """
    Função auxiliar para renderizar uma aba de Renda com um gráfico de barras.
    """
    titulo_centralizado(titulo_grafico, 5)

    if sort_order:
        df = df.copy()
        df[coluna_agregacao] = pd.Categorical(
            df[coluna_agregacao], categories=sort_order, ordered=True
        )
        df = df.dropna(subset=[coluna_agregacao])

    df_grafico = preparar_dados_renda_grafico(
        df, coluna_agregacao, coluna_valor
    ).sort_index()

    fig = criar_grafico_barras(
        df=df_grafico,
        titulo="",
        label_y=titulo_grafico,
        color_map=color_map,
        data_label_format=data_format,
        hover_label_format=hover_format,
    )
    st.plotly_chart(fig, width="stretch")


def render_renda_tabela_tab(df, coluna_index, titulo_secao, municipio_interesse):
    """
    Função auxiliar para renderizar uma aba de Renda com uma tabela dinâmica (CNAE).
    """

    tipo_renda = (
        st.segmented_control(
            "Selecione a métrica de remuneração:",
            options=["Remuneração Nominal (R$)", "Remuneração (Salários Mínimos)"],
            selection_mode="single",
            default="Remuneração Nominal (R$)",
            key=f"radio_renda_{coluna_index}",
        )
        or "Remuneração Nominal (R$)"
    )

    coluna_valor = (
        "remuneracao_media_dezembro"
        if tipo_renda == "Remuneração Nominal (R$)"
        else "valor_remuneracao_media_dezembro_sm"
    )

    titulo_centralizado(f"{titulo_secao} em {municipio_interesse}", 5)
    formatter = criar_formatador_final(tipo_renda, formatador_pt_br)

    ult_ano = int(df["ano"].max())
    df_pivot = df.pivot_table(
        index=coluna_index,
        columns="ano",
        values=coluna_valor,
        aggfunc="mean",
        observed=False,
        fill_value=0,
    ).sort_values(by=ult_ano, ascending=False)

    df_pivot.index.name = titulo_secao.split(" por ")[-1]

    st.dataframe(
        df_pivot.style.format(formatter).background_gradient(cmap="GnBu"),
        width="stretch",
    )


def display_renda_ranking(df_renda_ranking):
    """Exibe o expander com análise de participação na massa salarial do RS."""
    with st.expander("Participação na Massa Salarial do RS", expanded=False):
        if df_renda_ranking.empty:
            st.warning("Sem dados de ranking disponíveis.")
            return

        col1, col2 = st.columns([0.5, 0.5])

        with col1:
            visualizacao_selecionada = st.segmented_control(
                "Selecione a visualização:",
                options=["Participação no RS (%)", "Posição no Ranking"],
                selection_mode="single",
                default="Participação no RS (%)",
                key="ranking_renda_viz",
            )

        if not visualizacao_selecionada:
            visualizacao_selecionada = "Participação no RS (%)"

        if visualizacao_selecionada == "Participação no RS (%)":
            titulo_centralizado("Participação na Massa Salarial do RS", 5)

            df_grafico = preparar_dados_ranking_renda(
                df_filtrado=df_renda_ranking,
                coluna_selecionada="percentual_rs",
            )

            fig = criar_grafico_barras(
                df=df_grafico,
                titulo="",
                label_y="Participação (%)",
                height=400,
                data_label_format=",.2f",
                hover_label_format=",.2f",
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig, use_container_width=True)

        else:  # Posição no Ranking
            titulo_centralizado("Posição no Ranking de Massa Salarial do RS", 5)

            df_grafico = preparar_dados_ranking_renda(
                df_filtrado=df_renda_ranking,
                coluna_selecionada="ranking",
            )

            fig = criar_grafico_linhas(
                df=df_grafico,
                titulo="",
                label_y="Posição",
                height=400,
                data_label_format=",.0f",
                hover_label_format=",.0f",
                color_map=CORES_MUNICIPIOS,
                reverse_y=True,
            )
            st.plotly_chart(fig, use_container_width=True)


def display_renda(
    df_renda_mun,
    df_renda_sexo,
    df_renda_raca_cor,
    df_renda_faixa_salarial,
    df_renda_cnae,
    municipio_interesse,
):
    with st.expander("Remuneração Média", expanded=False):
        aba_selecionada = st.pills(
            "Selecione uma análise:",
            [
                "Municípios",
                "Sexo",
                "Raça/Cor",
                "Faixa Salarial",
                "Setor",
                "CNAE - Grupo",
                "CNAE - Subclasse",
            ],
            selection_mode="single",
            default="Municípios",
            key="main_tab_nav_renda",
        )
        if not aba_selecionada:
            aba_selecionada = "Municípios"

        # Aba 0: Comparativo entre Municípios
        if aba_selecionada == "Municípios":
            tipo_renda_mun = (
                st.segmented_control(
                    "Selecione a métrica de remuneração:",
                    options=[
                        "Remuneração Nominal (R$)",
                        "Remuneração (Salários Mínimos)",
                    ],
                    selection_mode="single",
                    default="Remuneração Nominal (R$)",
                    key="radio_renda_municipio",
                )
                or "Remuneração Nominal (R$)"
            )

            if tipo_renda_mun == "Remuneração Nominal (R$)":
                render_renda_grafico_tab(
                    df=df_renda_mun,
                    coluna_agregacao="municipio",
                    coluna_valor="remuneracao_media_dezembro",
                    titulo_grafico="Remuneração Média Nominal (R$)",
                    data_format=",.0f",
                    hover_format=",.2f",
                    color_map=CORES_MUNICIPIOS,
                )
            else:
                render_renda_grafico_tab(
                    df=df_renda_mun,
                    coluna_agregacao="municipio",
                    coluna_valor="valor_remuneracao_media_dezembro_sm",
                    titulo_grafico="Remuneração Média (em Salários Mínimos)",
                    data_format=",.2f",
                    hover_format=",.2f",
                    color_map=CORES_MUNICIPIOS,
                )

        # Aba 1: Análise por Sexo no município de interesse
        elif aba_selecionada == "Sexo":
            tipo_renda_sexo = (
                st.segmented_control(
                    "Selecione a métrica de remuneração:",
                    options=[
                        "Remuneração Nominal (R$)",
                        "Remuneração (Salários Mínimos)",
                    ],
                    selection_mode="single",
                    default="Remuneração Nominal (R$)",
                    key="radio_renda_sexo",
                )
                or "Remuneração Nominal (R$)"
            )

            if tipo_renda_sexo == "Remuneração Nominal (R$)":
                render_renda_grafico_tab(
                    df=df_renda_sexo,
                    coluna_agregacao="sexo",
                    coluna_valor="remuneracao_media_dezembro",
                    titulo_grafico=f"Remuneração Média Nominal (R$) por Sexo em {municipio_interesse}",
                    data_format=",.0f",
                    hover_format=",.2f",
                    color_map={"Masculino": "#4C82F7", "Feminino": "#FF6BE1"},
                )
            else:
                render_renda_grafico_tab(
                    df=df_renda_sexo,
                    coluna_agregacao="sexo",
                    coluna_valor="valor_remuneracao_media_dezembro_sm",
                    titulo_grafico=f"Remuneração Média (Salários Mínimos) por Sexo em {municipio_interesse}",
                    data_format=",.2f",
                    hover_format=",.2f",
                    color_map={"Masculino": "#4C82F7", "Feminino": "#FF6BE1"},
                )

        # Aba 2: Análise por Raça/Cor no município de interesse
        elif aba_selecionada == "Raça/Cor":
            tipo_renda_raca_cor = (
                st.segmented_control(
                    "Selecione a métrica de remuneração:",
                    options=[
                        "Remuneração Nominal (R$)",
                        "Remuneração (Salários Mínimos)",
                    ],
                    selection_mode="single",
                    default="Remuneração Nominal (R$)",
                    key="radio_renda_raca_cor",
                )
                or "Remuneração Nominal (R$)"
            )

            if tipo_renda_raca_cor == "Remuneração Nominal (R$)":
                render_renda_grafico_tab(
                    df=df_renda_raca_cor,
                    coluna_agregacao="raca_cor",
                    coluna_valor="remuneracao_media_dezembro",
                    titulo_grafico=f"Remuneração Média Nominal (R$) por Raça/Cor em {municipio_interesse}",
                    data_format=",.0f",
                    hover_format=",.2f",
                )
            else:
                render_renda_grafico_tab(
                    df=df_renda_raca_cor,
                    coluna_agregacao="raca_cor",
                    coluna_valor="valor_remuneracao_media_dezembro_sm",
                    titulo_grafico=f"Remuneração Média (Salários Mínimos) por Raça/Cor em {municipio_interesse}",
                    data_format=",.2f",
                    hover_format=",.2f",
                )

        # Aba 3: Análise por Faixa Salarial no município de interesse
        elif aba_selecionada == "Faixa Salarial":
            render_renda_grafico_tab(
                df=df_renda_faixa_salarial,
                coluna_agregacao="faixa_remun_media_sm",
                coluna_valor="vinculos_ativos",
                titulo_grafico=f"Número de Vínculos Ativos por Faixa Salarial em {municipio_interesse}",
                data_format=",.0f",
                hover_format=",.0f",
                sort_order=ordem_faixa_salarial,
            )

        # Aba 4: Análise por Setor no município de interesse
        elif aba_selecionada == "Setor":
            tipo_renda_setor = (
                st.segmented_control(
                    "Selecione a métrica de remuneração:",
                    options=[
                        "Remuneração Nominal (R$)",
                        "Remuneração (Salários Mínimos)",
                    ],
                    selection_mode="single",
                    default="Remuneração Nominal (R$)",
                    key="radio_renda_setor",
                )
                or "Remuneração Nominal (R$)"
            )

            if tipo_renda_setor == "Remuneração Nominal (R$)":
                render_renda_grafico_tab(
                    df=df_renda_cnae,
                    coluna_agregacao="grupo_ibge",
                    coluna_valor="remuneracao_media_dezembro",
                    titulo_grafico=f"Remuneração Média Nominal (R$) por Setor em {municipio_interesse}",
                    data_format=",.0f",
                    hover_format=",.2f",
                )
            else:
                render_renda_grafico_tab(
                    df=df_renda_cnae,
                    coluna_agregacao="grupo_ibge",
                    coluna_valor="valor_remuneracao_media_dezembro_sm",
                    titulo_grafico=f"Remuneração Média (Salários Mínimos) por Setor em {municipio_interesse}",
                    data_format=",.2f",
                    hover_format=",.2f",
                )

        # Aba 5: Tabela por CNAE - Grupo
        elif aba_selecionada == "CNAE - Grupo":
            render_renda_tabela_tab(
                df=df_renda_cnae,
                coluna_index="grupo",
                titulo_secao="Remuneração por CNAE - Grupo",
                municipio_interesse=municipio_interesse,
            )

        # Aba 6: Tabela por CNAE - Subclasse
        elif aba_selecionada == "CNAE - Subclasse":
            render_renda_tabela_tab(
                df=df_renda_cnae,
                coluna_index="subclasse",
                titulo_secao="Remuneração por CNAE - Subclasse",
                municipio_interesse=municipio_interesse,
            )


def show_page_emprego(
    df_caged,
    df_caged_cnae,
    df_caged_faixa_etaria,
    df_caged_raca_cor,
    df_caged_grau_instrucao,
    df_caged_sexo,
    municipio_de_interesse,
    df_estoque,
    df_estoque_cnae_setor,
    df_estoque_cnae_grupo,
    df_estoque_cnae_subclasse,
    df_estoque_faixa_etaria,
    df_estoque_raca_cor,
    df_estoque_grau_instrucao,
    df_estoque_sexo,
    df_renda_mun,
    df_renda_ranking,
    df_renda_sexo,
    df_renda_raca_cor,
    df_renda_cnae,
    df_renda_faixa_salarial,
):
    """Função principal que renderiza a página de Emprego."""
    st.markdown(
        "<h1 style='text-align: center;'>Dashboard de Emprego e Renda</h1>",
        unsafe_allow_html=True,
    )

    ult_ano = int(df_caged["ano"].max())
    ult_mes = int(df_caged[df_caged["ano"] == ult_ano]["mes"].max())

    display_resumo_cards(df_caged, df_estoque, municipio_de_interesse)

    st.markdown("---")
    st.markdown("##### Saldo de Admissões e Demissões")
    st.caption("Dados disponibilizados pelo CAGED - Atualização Mensal")

    display_emprego_municipios_expander(
        df_caged,
        municipio_de_interesse,
    )

    display_emprego_categoria_expander(
        df_faixa_etaria=df_caged_faixa_etaria,
        df_sexo=df_caged_sexo,
        df_raca_cor=df_caged_raca_cor,
        df_grau_instrucao=df_caged_grau_instrucao,
        ult_mes=ult_mes,
    )

    if not df_caged_cnae.empty:
        display_emprego_cnae_expander(df_caged_cnae)

    st.markdown("---")
    st.markdown("##### Estoque de Emprego Estimado")
    st.caption("Estimativa de Estoque de Emprego (Dados combinados da RAIS e CAGED) - Atualização Mensal")

    display_estoque_municipios_expander(
        df_estoque,
    )

    display_estoque_categoria_expander(
        df_sexo=df_estoque_sexo,
        df_faixa_etaria=df_estoque_faixa_etaria,
        df_raca_cor=df_estoque_raca_cor,
        df_grau_instrucao=df_estoque_grau_instrucao,
        ult_mes=ult_mes,
    )

    display_estoque_cnae_expander(
        df_cnae_grupo=df_estoque_cnae_grupo,
        df_cnae_setor=df_estoque_cnae_setor,
        df_cnae_subclasse=df_estoque_cnae_subclasse,
    )

    st.markdown("---")
    st.markdown("##### Renda do Trabalho")
    st.caption("Dados disponibilizados pela RAIS - Atualização Anual")

    display_renda(
        df_renda_mun=df_renda_mun,
        df_renda_cnae=df_renda_cnae,
        df_renda_sexo=df_renda_sexo,
        df_renda_raca_cor=df_renda_raca_cor,
        df_renda_faixa_salarial=df_renda_faixa_salarial,
        municipio_interesse=municipio_de_interesse,
    )

    display_renda_ranking(df_renda_ranking=df_renda_ranking)
