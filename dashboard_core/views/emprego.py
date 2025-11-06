import streamlit as st
import pandas as pd

from dashboard_core.utils import (
    MESES_DIC,
    checar_ult_ano_completo,
    criar_grafico_barras,
    criar_tabela_formatada,
    criar_tabela_formatada_mes,
    criar_tabela_formatada_ano,
    titulo_centralizado,
    formatador_pt_br,
    criar_formatador_final,
    preparar_dados_graficos_anuais,
)

from dashboard_core.config import (
    municipio_de_interesse,
    CORES_MUNICIPIOS,
    ordem_instrucao,
)

# ==============================================================================
# FUNÇÕES DA PÁGINA DE EMPREGO
# ==============================================================================


def display_emprego_kpi_cards(df, municipio_interesse):
    """Exibe os cards de KPI de Emprego para um município específico."""

    titulo_centralizado(f"Saldo de Admissões e Demissões em {municipio_interesse}", 3)

    with st.container(border=False):
        filtro_municipio = df["municipio"] == municipio_interesse
        df_municipio = df[filtro_municipio]
        ano_completo = checar_ult_ano_completo(df_municipio)

        ult_ano = df_municipio["ano"].max()
        ult_mes = df_municipio[df_municipio["ano"] == ult_ano]["mes"].max()

        saldo_ult_mes = df_municipio[
            (df_municipio["ano"] == ult_ano) & (df_municipio["mes"] == ult_mes)
        ]["saldo_movimentacao"].sum()

        saldo_acu_ano = df_municipio[
            (df_municipio["ano"] == ult_ano) & (df_municipio["mes"] <= ult_mes)
        ]["saldo_movimentacao"].sum()

        saldo_ano_completo = df_municipio[df_municipio["ano"] == ano_completo][
            "saldo_movimentacao"
        ].sum()

        col1, col2, col3 = st.columns(3)
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
        col3.metric(
            label=f"{ano_completo}",
            value=f"{saldo_ano_completo:,.0f}".replace(",", "."),
            delta=None,
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

    # Histórico Mensal
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
            fill_value=0,
        )
        .sort_index()
    )

    ult_ano = df_filtrado["ano"].max()
    ult_mes = df_filtrado[df_filtrado["ano"] == ult_ano]["mes"].max()

    # Acumulado no Ano
    df_acum = (
        df_filtrado[df_filtrado["mes"] <= ult_mes]
        .pivot_table(
            index="ano",
            columns="municipio",
            values="saldo_movimentacao",
            aggfunc="sum",
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
            fill_value=0,
        )
        .sort_index(ascending=False)
    )

    return df_hist, df_acum, df_anual, ult_ano, ult_mes


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
        df=df_categoria, index_col=index_col, ult_ano=ult_ano, ult_mes=ult_mes
    ).sort_index()
    df_acum = criar_tabela_formatada(
        df=df_categoria, index_col=index_col, ult_ano=ult_ano, ult_mes=ult_mes
    ).sort_index()
    df_anual = criar_tabela_formatada_ano(
        df=df_categoria, index_col=index_col
    ).sort_index()

    return df_mes, df_acum, df_anual


def display_emprego_categoria_expander(
    df_sexo, df_faixa_etaria, df_raca_cor, df_grau_instrucao, ult_mes
):
    """Exibe o expander com análise de saldo de emprego por categoria (versão otimizada)."""
    with st.expander(
        f"Saldo de Emprego por Categoria em {municipio_de_interesse}",
        expanded=False,
    ):
        tab_sexo, tab_raca_cor, tab_faixa_etaria, tab_grau_instrucao = st.tabs(
            ["Sexo", "Raça/Cor", "Faixa Etária", "Grau de Instrução"],
        )

        def render_categoria_tab(
            df, index_col, titulo, sort_order=None, color_map=None
        ):
            """Função interna para renderizar o conteúdo de cada aba de categoria."""
            df_mes, df_acum, df_anual = preparar_dados_categoria_emprego(
                df, index_col, sort_order
            )

            view_mode = st.radio(
                "Selecione a Análise:",
                options=["Último Mês", "Acumulado no Ano", "Anual"],
                horizontal=True,
                label_visibility="collapsed",
                key=f"view_mode_cat_{index_col}",
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

        with tab_sexo:
            render_categoria_tab(
                df_sexo,
                "sexo",
                "Sexo",
                color_map={"Masculino": "#4C82F7", "Feminino": "#FF6BE1"},
            )
        with tab_raca_cor:
            render_categoria_tab(df_raca_cor, "raca_cor", "Raça/Cor")
        with tab_faixa_etaria:
            render_categoria_tab(df_faixa_etaria, "faixa_etaria", "Faixa Etária")
        with tab_grau_instrucao:
            render_categoria_tab(
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
            df=df_cnae, index_col=index_col, ult_ano=ult_ano, ult_mes=ult_mes
        )

        df_acum = criar_tabela_formatada(
            df=df_cnae, index_col=index_col, ult_ano=ult_ano, ult_mes=ult_mes
        )

        df_anual = criar_tabela_formatada_ano(df=df_cnae, index_col=index_col)

    return df_mes, df_acum, df_anual


def display_emprego_municipios_expander(
    df,
    categoria,
):
    """Exibe o expander com análise de saldo de emprego para múltiplos municípios."""
    with st.expander(
        "Saldo de Emprego por Município",
        expanded=st.session_state.emprego_expander_state,
    ):
        df_hist, df_acum, df_anual, ult_ano, ult_mes = preparar_dados_graficos_emprego(
            df
        )
        anos_disponiveis = sorted(df["ano"].unique().tolist(), reverse=True)

        tab_hist, tab_acum, tab_anual = st.tabs(
            ["Histórico Mensal", "Acumulado no Ano", "Anual"],
        )

        with tab_hist:
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

        with tab_acum:
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

        with tab_anual:
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


def display_emprego_cnae_expander(df_cnae_foco):
    """Exibe o expander com análise de saldo de emprego por Setor e CNAE"""
    with st.expander(
        f"Saldo de Emprego por Setor Econômico em {municipio_de_interesse}",
        expanded=False,
    ):
        tab_setor, tab_grupo, tab_subclasse = st.tabs(
            ["Setor", "CNAE - Grupo", "CNAE - Subclasse"]
        )

        def render_cnae_content(index_col, titulo_categoria, show_graph=True):
            """Função interna para renderizar o conteúdo de cada aba de CNAE."""
            df_mes, df_acum, df_anual = preparar_dados_graficos_cnae(
                df_cnae_foco, index_col
            )

            ult_ano = int(df_cnae_foco["ano"].max())
            ult_mes = int(df_cnae_foco[df_cnae_foco["ano"] == ult_ano]["mes"].max())

            view_mode = st.radio(
                "Selecione a Análise:",
                options=["Último Mês", "Acumulado no Ano", "Anual"],
                horizontal=True,
                label_visibility="collapsed",
                key=f"view_mode_cnae_{index_col}",
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
                df_selecionado = df_selecionado.style.format(
                    lambda x: f"{x:,.0f}".replace(",", ".")
                ).background_gradient(cmap="coolwarm_r", axis=0)
                st.dataframe(df_selecionado)

        with tab_setor:
            render_cnae_content("grupo_ibge", show_graph=True, titulo_categoria="Setor")
        with tab_grupo:
            render_cnae_content(
                "grupo", show_graph=False, titulo_categoria="CNAE - Grupo"
            )
        with tab_subclasse:
            render_cnae_content(
                "subclasse", show_graph=False, titulo_categoria="CNAE - Subclasse"
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
        fill_value=0,
    ).sort_index()
    return df_pivot


def render_vinculos_tab(
    df, coluna_agregacao, titulo_grafico, color_map=None, reorder_cols=None
):
    """
    Função auxiliar para renderizar uma aba de Vínculos Ativos.
    Prepara os dados, cria e exibe o gráfico de barras.
    """
    titulo_centralizado(titulo_grafico, 5)

    df_grafico = preparar_dados_graficos_anuais(
        df_filtrado=df,
        coluna_agregacao=coluna_agregacao,
        coluna_valores="vinculos_ativos",
    )

    # Reordena as colunas se uma ordem específica for fornecida (ex: Grau de Instrução)
    if reorder_cols and not df_grafico.empty:
        df_grafico = df_grafico.reindex(columns=reorder_cols, fill_value=0)

    fig = criar_grafico_barras(
        df=df_grafico,
        titulo="",
        label_y="Vínculos Ativos",
        color_map=color_map,
        data_label_format=",.0f",
        hover_label_format=",.0f",
    )
    st.plotly_chart(fig, width="stretch")


def display_vinculos(
    df_mun,
    df_vinculos_faixa_etaria,
    df_vinculos_grau_instrucao,
    df_vinculos_raca_cor,
    df_vinculos_sexo,
    df_vinculos_cnae,
    municipio_interesse,
    color_map=None,
):
    with st.expander("Vínculos Ativos", expanded=False):
        tabs = st.tabs(
            [
                "Município",
                "Sexo",
                "Raça/Cor",
                "Faixa Etária",
                "Grau de Instrução",
                "Setor",
                "CNAE - Grupo",
                "CNAE - Subclasse",
            ]
        )

        # Dicionário de configuração para as abas com gráficos
        config_tabs = {
            0: {
                "df": df_mun,
                "col": "municipio",
                "titulo": "Vínculos Ativos",
                "color_map": color_map,
            },
            1: {
                "df": df_vinculos_sexo,
                "col": "sexo",
                "titulo": f"Vínculos Ativos por Sexo em {municipio_de_interesse}",
                "color_map": {"Masculino": "#4C82F7", "Feminino": "#FF6BE1"},
            },
            2: {
                "df": df_vinculos_raca_cor,
                "col": "raca_cor",
                "titulo": f"Vínculos Ativos por Raça/Cor em {municipio_de_interesse}",
            },
            3: {
                "df": df_vinculos_faixa_etaria,
                "col": "faixa_etaria",
                "titulo": f"Vínculos Ativos por Faixa Etária em {municipio_de_interesse}",
            },
            4: {
                "df": df_vinculos_grau_instrucao,
                "col": "grau_instrucao",
                "titulo": f"Vínculos Ativos por Grau de Instrução em {municipio_de_interesse}",
                "reorder_cols": ordem_instrucao,
            },
            5: {
                "df": df_vinculos_cnae,
                "col": "grupo_ibge",
                "titulo": f"Vínculos Ativos por Setor em {municipio_de_interesse}",
            },
        }

        # Renderiza as abas de gráficos dinamicamente
        for i, tab in enumerate(tabs[:6]):
            with tab:
                if i in config_tabs:
                    cfg = config_tabs[i]
                    render_vinculos_tab(
                        df=cfg["df"],
                        coluna_agregacao=cfg["col"],
                        titulo_grafico=cfg["titulo"],
                        color_map=cfg.get("color_map"),
                        reorder_cols=cfg.get("reorder_cols"),
                    )

        # Abas de tabelas (CNAE Grupo e Subclasse)
        with tabs[6]:  # tab_cnae_grupo
            titulo_centralizado(
                f"Vínculos Ativos por CNAE - Grupo em {municipio_de_interesse}", 5
            )
            ult_ano_cnae = df_vinculos_cnae["ano"].max()
            df_pivot = df_vinculos_cnae.pivot_table(
                index="grupo",
                columns="ano",
                values="vinculos_ativos",
                aggfunc="sum",
                fill_value=0,
            ).sort_values(by=ult_ano_cnae, ascending=False)
            df_pivot.index.name = "CNAE-Grupo"
            st.dataframe(
                df_pivot.style.format(
                    lambda x: f"{x:,.0f}".replace(",", ".")
                ).background_gradient(cmap="GnBu"),
                width="stretch",
            )

        with tabs[7]:  # tab_cnae_subclasse
            titulo_centralizado(
                f"Vínculos Ativos por CNAE - Subclasse em {municipio_de_interesse}", 5
            )
            ult_ano_cnae = df_vinculos_cnae["ano"].max()
            df_pivot = df_vinculos_cnae.pivot_table(
                index="subclasse",
                columns="ano",
                values="vinculos_ativos",
                aggfunc="sum",
                fill_value=0,
            ).sort_values(by=ult_ano_cnae, ascending=False)
            df_pivot.index.name = "CNAE-Subclasse"
            st.dataframe(
                df_pivot.style.format(
                    lambda x: f"{x:,.0f}".replace(",", ".")
                ).background_gradient(cmap="GnBu"),
                width="stretch",
            )


def render_renda_grafico_tab(
    df,
    coluna_agregacao,
    coluna_valor,
    titulo_grafico,
    data_format,
    hover_format,
    color_map=None,
):
    """
    Função auxiliar para renderizar uma aba de Renda com um gráfico de barras.
    """
    titulo_centralizado(titulo_grafico, 5)

    df_grafico = preparar_dados_renda_grafico(df, coluna_agregacao, coluna_valor)

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

    tipo_renda = st.radio(
        "Selecione a métrica de remuneração:",
        ["Remuneração Nominal (R$)", "Remuneração (Salários Mínimos)"],
        key=f"radio_renda_{coluna_index}",
        horizontal=True,
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
        fill_value=0,
    ).sort_values(by=ult_ano, ascending=False)

    df_pivot.index.name = titulo_secao.split(" por ")[-1]

    st.dataframe(
        df_pivot.style.format(formatter).background_gradient(cmap="GnBu"),
        width="stretch",
    )


def display_renda(
    df_renda_mun,
    df_renda_sexo,
    df_renda_cnae,
    municipio_interesse,
):
    with st.expander("Remuneração Média", expanded=False):
        tabs = st.tabs(
            ["Municípios", "Sexo", "Setor", "CNAE - Grupo", "CNAE - Subclasse"]
        )

        # Aba 0: Comparativo entre Municípios
        with tabs[0]:
            tipo_renda_mun = st.radio(
                "Selecione a métrica de remuneração:",
                ["Remuneração Nominal (R$)", "Remuneração (Salários Mínimos)"],
                key="radio_renda_municipio",
                horizontal=True,
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
        with tabs[1]:
            tipo_renda_sexo = st.radio(
                "Selecione a métrica de remuneração:",
                ["Remuneração Nominal (R$)", "Remuneração (Salários Mínimos)"],
                key="radio_renda_sexo",
                horizontal=True,
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

        # Aba 2: Análise por Setor no município de interesse
        with tabs[2]:
            tipo_renda_setor = st.radio(
                "Selecione a métrica de remuneração:",
                ["Remuneração Nominal (R$)", "Remuneração (Salários Mínimos)"],
                key="radio_renda_setor",
                horizontal=True,
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

        # Aba 3: Tabela por CNAE - Grupo
        with tabs[3]:
            render_renda_tabela_tab(
                df=df_renda_cnae,
                coluna_index="grupo",
                titulo_secao="Remuneração por CNAE - Grupo",
                municipio_interesse=municipio_interesse,
            )

        # Aba 4: Tabela por CNAE - Subclasse
        with tabs[4]:
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
    df_vinculos,
    df_vinculos_cnae,
    df_vinculos_faixa_etaria,
    df_vinculos_grau_instrucao,
    df_vinculos_raca_cor,
    df_vinculos_sexo,
    df_renda_mun,
    df_renda_sexo,
    df_renda_cnae,
):
    """Função principal que renderiza a página de Emprego."""
    st.markdown(
        "<h1 style='text-align: center;'>Dashboard de Emprego</h1>",
        unsafe_allow_html=True,
    )
    ult_ano = int(df_caged["ano"].max())
    ult_mes = int(df_caged[df_caged["ano"] == ult_ano]["mes"].max())
    st.markdown("###### Dados disponibilizados pelo CAGED - Atualização Mensal")
    with st.expander("Saldo de Admissões e Demissões", expanded=True):
        display_emprego_kpi_cards(df_caged, municipio_de_interesse)

        titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)

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
    st.markdown("###### Dados disponibilizados pela RAIS - Atualização Anual")
    display_vinculos(
        df_mun=df_vinculos,
        df_vinculos_grau_instrucao=df_vinculos_grau_instrucao,
        df_vinculos_cnae=df_vinculos_cnae,
        df_vinculos_faixa_etaria=df_vinculos_faixa_etaria,
        df_vinculos_raca_cor=df_vinculos_raca_cor,
        df_vinculos_sexo=df_vinculos_sexo,
        municipio_interesse=municipio_de_interesse,
    )

    display_renda(
        df_renda_mun=df_renda_mun,
        df_renda_cnae=df_renda_cnae,
        df_renda_sexo=df_renda_sexo,
        municipio_interesse=municipio_de_interesse,
    )
