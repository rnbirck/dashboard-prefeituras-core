import pandas as pd
import streamlit as st

from dashboard_core.utils import (
    MESES_DIC,
    criar_grafico_barras,
    checar_ult_ano_completo,
    titulo_centralizado,
    style_saldo_variacao,  # Adicionado para estilizar a tabela
)

CORES_MUNICIPIOS = {}
ANOS_DE_INTERESSE = []
municipio_de_interesse = None  # Variável global para o município foco


def set_saude_config(municipio, cores_municipios, anos_de_interesse):
    """
    Configura valores específicos do município que antes eram importados
    do dashboard_core.config. Deve ser chamado pelo app.py antes de
    renderizar a página de saude.
    """
    global CORES_MUNICIPIOS, ANOS_DE_INTERESSE, municipio_de_interesse
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}
    ANOS_DE_INTERESSE = anos_de_interesse or []


# --- FUNÇÕES AUXILIARES DE FORMATAÇÃO ---
def formatar_valor_br(x):
    """Formata número float para padrão BR (1.000.000) sem decimais."""
    if pd.isna(x):
        return "-"
    return f"{x:,.0f}".replace(",", ".")


def formatar_pct_br(x):
    """Formata número float para percentual BR (+1,2%) com 1 casa decimal."""
    if pd.isna(x):
        return "-"
    return f"{x:+,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")


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


def internacoes_residentes_callback():
    set_expander_open("internacoes_residentes_expander_state")


def sisab_callback():
    set_expander_open("sisab_expander_state")


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


def obitos_causa_basica_callback():
    set_expander_open("obitos_causa_basica_expander_state")


def preparar_dados_graficos_saude_mensal(
    df_filtrado,
    coluna_selecionada,
    metodo_agg="sum",
    anos_visualizacao=None,
    col_numerador=None,
    col_denominador=None,
    fator_multiplicacao=1,
):
    """
    Prepara os DataFrames para os gráficos, usando o método de agregação correto.
    'sum' para números absolutos, 'ratio' para taxas/proporções calculadas.
    Retorna também DataFrames de variação.

    Args:
        col_numerador: Nome da coluna numerador para cálculo de proporção/taxa
        col_denominador: Nome da coluna denominador para cálculo de proporção/taxa
        fator_multiplicacao: Fator para multiplicar o resultado (ex: 100 para %, 1000 para taxas por mil)
    """
    # Inicializa DataFrames vazios como retorno padrão
    df_hist = pd.DataFrame()
    df_acum, df_acum_var = pd.DataFrame(), pd.DataFrame()
    df_anual, df_anual_var = pd.DataFrame(), pd.DataFrame()
    ult_ano, ult_mes = None, None

    # VERIFICAÇÃO CRÍTICA: Retorna valores padrão se df_filtrado for None ou vazio
    if df_filtrado is None:
        return df_hist, df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes

    if df_filtrado.empty:
        return df_hist, df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes

    # Continua o processamento normal se houver dados
    if True:  # Mantém a estrutura original de indentação
        # Para cálculo de proporção/taxa, não filtra NaN pois vai calcular a partir de numerador e denominador
        # Para soma, filtra registros com dados válidos
        if metodo_agg == "ratio":
            df_com_dados = df_filtrado.copy()
            # Preenche NaN com 0 para as colunas de cálculo
            if col_numerador:
                df_com_dados[col_numerador] = df_com_dados[col_numerador].fillna(0)
            if col_denominador:
                df_com_dados[col_denominador] = df_com_dados[col_denominador].fillna(0)
        else:
            df_com_dados = df_filtrado[df_filtrado[coluna_selecionada].notna()].copy()

        if df_com_dados.empty:
            return (
                df_hist,
                df_acum,
                df_acum_var,
                df_anual,
                df_anual_var,
                ult_ano,
                ult_mes,
            )

        # Se anos_visualizacao for fornecido, usa para determinar o último ano
        if anos_visualizacao:
            df_range_visualizacao = df_com_dados[
                df_com_dados["ano"].isin(anos_visualizacao)
            ]
            if df_range_visualizacao.empty:
                ult_ano = df_com_dados["ano"].max()
            else:
                ult_ano = df_range_visualizacao["ano"].max()
        else:
            ult_ano = df_com_dados["ano"].max()

        # Para proporções/taxas, calcula ult_mes baseado nos dados válidos das colunas específicas
        if metodo_agg == "ratio" and col_numerador and col_denominador:
            # Filtra registros onde AMBAS as colunas têm dados válidos (não-zero e não-nulo)
            df_validos = df_com_dados[
                (df_com_dados[col_numerador].notna())
                & (df_com_dados[col_numerador] > 0)
                & (df_com_dados[col_denominador].notna())
                & (df_com_dados[col_denominador] > 0)
            ]
            if not df_validos.empty:
                ult_mes = df_validos[df_validos["ano"] == ult_ano]["mes"].max()
            else:
                ult_mes = df_com_dados[df_com_dados["ano"] == ult_ano]["mes"].max()
        else:
            ult_mes = df_com_dados[df_com_dados["ano"] == ult_ano]["mes"].max()

        # Evolução Mensal
        df_hist_full = (
            df_com_dados.assign(
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
            )
            .dropna(how="all")  # Remove datas onde todos os municípios têm NaN
            .sort_index()
        )

        # Filtra Evolução por anos de interesse
        if anos_visualizacao:
            df_hist = df_hist_full[df_hist_full.index.year.isin(anos_visualizacao)]
        else:
            df_hist = df_hist_full

        # Lógica de Agregação para Acumulado e Anual
        is_taxa = metodo_agg == "ratio"  # Se for ratio, é taxa/proporção calculada

        # Acumulado no Ano
        df_acum_temp = df_com_dados[df_com_dados["mes"] <= ult_mes]

        if metodo_agg == "ratio":
            # Para proporções/taxas, soma numerador e denominador separadamente
            df_num = (
                df_acum_temp.pivot_table(
                    index="ano",
                    columns="municipio",
                    values=col_numerador,
                    aggfunc="sum",
                )
                .dropna(how="all")
                .sort_index()
            )
            df_den = (
                df_acum_temp.pivot_table(
                    index="ano",
                    columns="municipio",
                    values=col_denominador,
                    aggfunc="sum",
                )
                .dropna(how="all")
                .sort_index()
            )
            # Calcula a proporção/taxa
            df_acum_full = (df_num / df_den.replace(0, pd.NA)) * fator_multiplicacao
        else:
            df_acum_full = (
                df_acum_temp.pivot_table(
                    index="ano",
                    columns="municipio",
                    values=coluna_selecionada,
                    aggfunc="sum",
                )
                .dropna(how="all")
                .sort_index()
            )  # Remove anos sem dados

        # Calcula variação (diferença para taxas, percentual para valores absolutos)
        if is_taxa:
            df_acum_var_full = df_acum_full.diff()
        else:
            df_acum_var_full = df_acum_full.pct_change() * 100

        # Aplica filtro de anos apenas aos valores absolutos
        if anos_visualizacao:
            df_acum = df_acum_full[df_acum_full.index.isin(anos_visualizacao)]
        else:
            df_acum = df_acum_full
        df_acum_var = df_acum_var_full  # Variação mantém todos os anos

        # Anual
        ano_completo = checar_ult_ano_completo(df_com_dados)
        df_anual_temp = df_com_dados[df_com_dados["ano"] <= ano_completo]

        if metodo_agg == "ratio":
            # Para proporções/taxas, soma numerador e denominador separadamente
            df_num = (
                df_anual_temp.pivot_table(
                    index="ano",
                    columns="municipio",
                    values=col_numerador,
                    aggfunc="sum",
                )
                .dropna(how="all")
                .sort_index()
            )
            df_den = (
                df_anual_temp.pivot_table(
                    index="ano",
                    columns="municipio",
                    values=col_denominador,
                    aggfunc="sum",
                )
                .dropna(how="all")
                .sort_index()
            )
            # Calcula a proporção/taxa
            df_anual_full = (df_num / df_den.replace(0, pd.NA)) * fator_multiplicacao
        else:
            df_anual_full = (
                df_anual_temp.pivot_table(
                    index="ano",
                    columns="municipio",
                    values=coluna_selecionada,
                    aggfunc="sum",
                )
                .dropna(how="all")
                .sort_index()
            )  # Remove anos sem dados

        # Calcula variação
        if is_taxa:
            df_anual_var_full = df_anual_full.diff()
        else:
            df_anual_var_full = df_anual_full.pct_change() * 100

        # Aplica filtro de anos apenas aos valores absolutos
        if anos_visualizacao:
            df_anual = df_anual_full[
                df_anual_full.index.isin(anos_visualizacao)
            ].sort_index(ascending=False)
        else:
            df_anual = df_anual_full.sort_index(ascending=False)
        df_anual_var = df_anual_var_full  # Variação mantém todos os anos

    return df_hist, df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes


# --- PREPARAÇÃO DE DADOS PARA TABELA DE ÓBITOS ---
@st.cache_data
def preparar_dados_obitos_tipo_tabela(df, municipio, anos_interesse=None):
    """
    Prepara a tabela dinâmica de óbitos por tipo para o município selecionado.
    Retorna DF de Valores e DF de Variação Percentual.
    """
    if df.empty or not municipio:
        return pd.DataFrame(), pd.DataFrame()

    df_filt = df[df["municipio"] == municipio].copy()

    if df_filt.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Verifica se as colunas necessárias existem
    colunas_necessarias = [
        "causa_basica",
        "descricao_subcategoria",
        "ano",
        "num_obitos",
    ]
    if not all(col in df_filt.columns for col in colunas_necessarias):
        return pd.DataFrame(), pd.DataFrame()

    # Cria coluna combinada Causa + Descrição para facilitar leitura
    df_filt["causa_completa"] = (
        df_filt["causa_basica"] + " - " + df_filt["descricao_subcategoria"]
    )
    pivot_val = df_filt.pivot_table(
        index="causa_completa",
        columns="ano",
        values="num_obitos",
        aggfunc="sum",
        fill_value=0,
    )

    # Ordena pelo último ano disponível com dados
    if not pivot_val.empty:
        ult_ano = pivot_val.columns.max()
        pivot_val = pivot_val.sort_values(by=ult_ano, ascending=False)

    # Calcula Variação Percentual (Ano X vs Ano X-1)
    # pct_change faz (atual - anterior) / anterior
    pivot_pct = pivot_val.pct_change(axis=1) * 100

    # Filtra pelos anos de interesse
    if anos_interesse:
        colunas_interesse = [c for c in pivot_val.columns if c in anos_interesse]
        pivot_val = pivot_val[colunas_interesse]
        pivot_pct = pivot_pct[colunas_interesse]

    # Renomeia o índice para "Causa Básica"
    pivot_val.index.name = "Causa Básica"
    pivot_pct.index.name = "Causa Básica"

    return pivot_val, pivot_pct


def preparar_dados_graficos_saude_anual(
    df_filtrado, coluna_selecionada, is_percentual=False, anos_visualizacao=None
):
    """
    Prepara os DataFrames para os gráficos anuais.
    Retorna também DataFrame de variação.
    """
    df_anual_full = (
        df_filtrado.pivot_table(
            index="ano",
            columns="municipio",
            values=coluna_selecionada,
            aggfunc="sum",
        )
        .dropna(how="all")
        .sort_index()
    )  # Remove anos sem dados

    # Calcula variação
    if is_percentual:
        df_anual_var = df_anual_full.diff()
    else:
        df_anual_var = df_anual_full.pct_change() * 100

    # Aplica filtro de anos apenas aos valores absolutos
    if anos_visualizacao:
        df_anual = df_anual_full[
            df_anual_full.index.isin(anos_visualizacao)
        ].sort_index(ascending=False)
    else:
        df_anual = df_anual_full.sort_index(ascending=False)

    return df_anual, df_anual_var


def display_obitos_causa_basica_expander(
    df_obitos_tipo,
    expander_state_key,
    callback_func,
):
    """Função dedicada para exibir o detalhamento de óbitos por causa básica."""
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(
        "Detalhamento de Óbitos por Causa Básica",
        expanded=st.session_state[expander_state_key],
    ):
        if df_obitos_tipo is None or df_obitos_tipo.empty:
            st.warning("Dados detalhados de óbitos não disponíveis.")
            return

        titulo_centralizado(f"Detalhamento de Óbitos - {municipio_de_interesse}", 5)

        # Preparação dos dados da tabela
        df_val, df_pct = preparar_dados_obitos_tipo_tabela(
            df_obitos_tipo, municipio_de_interesse, anos_interesse=ANOS_DE_INTERESSE
        )

        if df_val.empty:
            st.info(
                f"Não há registros detalhados de óbitos para {municipio_de_interesse}."
            )
            return

        # Controles da Tabela
        col_busca, col_metric = st.columns([0.6, 0.4])
        with col_busca:
            texto_busca = st.text_input(
                "🔍 Pesquisar Causa:",
                placeholder="Ex: Neoplasia, Hipertensão",
                key="obitos_causa_basica_busca",
            )
        with col_metric:
            modo_metrica = st.segmented_control(
                "Métrica:",
                options=["Nᵒ Óbitos", "Variação (%)"],
                selection_mode="single",
                default="Nᵒ Óbitos",
                key="obitos_causa_basica_metrica",
            )
            if not modo_metrica:
                modo_metrica = "Nᵒ Óbitos"

        # Filtragem por busca
        if texto_busca:
            mask = df_val.index.str.contains(texto_busca, case=False, na=False)
            df_val = df_val[mask]
            df_pct = df_pct[mask]

        # Seleção do DataFrame para exibição
        if modo_metrica == "Nᵒ Óbitos":
            df_show = df_val
            formatter = formatar_valor_br
            cmap = "Blues"
            style_func = None
        else:
            df_show = df_pct
            formatter = formatar_pct_br
            cmap = None
            style_func = style_saldo_variacao

        # Renderização da Tabela
        if not df_show.empty:
            # Converte colunas (anos) para string para exibição limpa
            df_show.columns = [str(c) for c in df_show.columns]

            styler = df_show.style.format(formatter)

            if cmap:
                styler = styler.background_gradient(cmap=cmap, axis=0)
            if style_func:
                styler = styler.map(style_func)

            st.dataframe(styler, height=400, use_container_width=True)
        else:
            st.warning("Nenhum registro encontrado para a busca.")


def display_mortalidade_prematura(
    df_mort_prematura, df_saude_mensal, key_prefix, callback_func
):
    """Exibe os gráficos de mortalidade prematura por DCNT."""

    # Mapeamento de nomes das doenças
    DOENCAS_MAP = {
        "Câncer": "cancer",
        "Diabetes": "diabetes",
        "Doenças do Aparelho Circulatório": "doencas_aparelho_circulatorio",
        "Doenças Crônicas Respiratórias": "doencas_cronicas_respiratorias",
    }

    QUADRIMESTRES_LABEL = {
        1: "1º Quadrimestre",
        2: "2º Quadrimestre",
        3: "3º Quadrimestre",
    }

    # --- NAVEGAÇÃO ENTRE TIPOS DE ANÁLISE (PILLS) ---
    key_tipo_analise = f"tipo_analise_{key_prefix}"
    if key_tipo_analise not in st.session_state:
        st.session_state[key_tipo_analise] = "DCNT em relação ao total de óbitos"

    tipo_analise = st.pills(
        "Selecione o tipo de análise:",
        options=["DCNT em relação ao total de óbitos", "Participação de cada DCNT"],
        selection_mode="single",
        key=key_tipo_analise,
    )

    if not tipo_analise:
        tipo_analise = "DCNT em relação ao total de óbitos"

    # --- NAVEGAÇÃO ENTRE "ABAS" TEMPORAIS (PILLS) ---
    key_main_tab = f"main_tab_nav_{key_prefix}"
    if key_main_tab not in st.session_state:
        st.session_state[key_main_tab] = "Acumulado no Ano"

    aba_selecionada = st.pills(
        "Selecione o tipo de análise temporal:",
        options=["Acumulado no Ano", "Anual"],
        selection_mode="single",
        key=key_main_tab,
    )

    if not aba_selecionada:
        aba_selecionada = "Acumulado no Ano"

    # ========== ANÁLISE 1: DCNT EM RELAÇÃO AO TOTAL DE ÓBITOS ==========
    if tipo_analise == "DCNT em relação ao total de óbitos":
        label_y = "Proporção de DCNT no Total de Óbitos (%)"
        label_var = "Variação (p.p.)"
        data_format = ".1f"
        hover_format = ".2f"
        fmt_var = "+,.2f"

        # --- ABA 1: ACUMULADO NO ANO (QUADRIMESTRAL) ---
        if aba_selecionada == "Acumulado no Ano":
            # Obter último quadrimestre disponível
            ult_quadrimestre = int(df_mort_prematura["quadrimestre"].max())

            # Preparar dados de DCNT
            df_dcnt = df_mort_prematura.copy()

            # Preparar dados de óbitos totais - somar por quadrimestre
            df_obitos = df_saude_mensal.copy()
            df_obitos["quadrimestre"] = df_obitos["mes"].apply(
                lambda m: 1 if m in [1, 2, 3, 4] else (2 if m in [5, 6, 7, 8] else 3)
            )

            # Agrupar óbitos totais por ano, município e quadrimestre
            df_obitos_quad = (
                df_obitos.groupby(["ano", "municipio", "quadrimestre"])
                .agg({"obitos_totais": "sum"})
                .reset_index()
            )

            # Filtrar até o último quadrimestre
            df_dcnt_acum = df_dcnt[df_dcnt["quadrimestre"] <= ult_quadrimestre].copy()
            df_obitos_acum = df_obitos_quad[
                df_obitos_quad["quadrimestre"] <= ult_quadrimestre
            ].copy()

            # Agrupar DCNT por ano (soma dos quadrimestres até o último)
            df_dcnt_sum = (
                df_dcnt_acum.groupby(["ano", "municipio"])
                .agg({"dcnt": "sum"})
                .reset_index()
            )

            # Agrupar óbitos totais por ano (soma dos quadrimestres até o último)
            df_obitos_sum = (
                df_obitos_acum.groupby(["ano", "municipio"])
                .agg({"obitos_totais": "sum"})
                .reset_index()
            )

            # Fazer merge dos dois dataframes
            df_merged = pd.merge(
                df_dcnt_sum, df_obitos_sum, on=["ano", "municipio"], how="inner"
            )

            # Calcular proporção
            df_merged["proporcao"] = (
                df_merged["dcnt"] / df_merged["obitos_totais"]
            ) * 100

            # Pivotar
            df_acum_pivot = df_merged.pivot(
                index="ano", columns="municipio", values="proporcao"
            ).sort_index()

            # Calcular variação
            df_acum_var = df_acum_pivot.diff()

            # Filtrar por anos de interesse
            if ANOS_DE_INTERESSE:
                df_acum_pivot_filtrado = df_acum_pivot[
                    df_acum_pivot.index.isin(ANOS_DE_INTERESSE)
                ]
            else:
                df_acum_pivot_filtrado = df_acum_pivot

            # Seletor de modo (Proporção ou Variação)
            key_acum = f"acum_mode_{key_prefix}"
            if key_acum not in st.session_state:
                st.session_state[key_acum] = label_y

            modo_acum = st.segmented_control(
                "Visualizar:",
                options=[label_y, label_var],
                key=key_acum,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_acum:
                modo_acum = label_y

            periodo_txt = QUADRIMESTRES_LABEL.get(
                ult_quadrimestre, f"{ult_quadrimestre}º Quadrimestre"
            )

            if modo_acum == label_var:
                titulo_centralizado(
                    f"Taxa de Mortalidade Prematura por Doenças Crônicas Não Transmissíveis - {label_var} - Até {periodo_txt}",
                    5,
                )
                df_var_plot = (
                    df_acum_var.copy().sort_index(ascending=True).dropna(how="all")
                )
                df_var_plot.index = (
                    "1º-"
                    + str(ult_quadrimestre)
                    + "º Quadrimestre/"
                    + df_var_plot.index.astype(str).str.slice(-2)
                )

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y=label_var,
                    barmode="group",
                    height=400,
                    data_label_format=fmt_var,
                    hover_label_format=fmt_var,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                titulo_centralizado(
                    f"Taxa de Mortalidade Prematura por Doenças Crônicas Não Transmissíveis - Até {periodo_txt}",
                    5,
                )
                df_plot = df_acum_pivot_filtrado.copy()
                df_plot.index = (
                    "1º-"
                    + str(ult_quadrimestre)
                    + "º Quadrimestre/"
                    + df_plot.index.astype(str).str.slice(-2)
                )

                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=data_format,
                    hover_label_format=hover_format,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)

        # --- ABA 2: ANUAL ---
        elif aba_selecionada == "Anual":
            # Preparar dados de DCNT
            df_dcnt = df_mort_prematura.copy()

            # Preparar dados de óbitos totais - somar por quadrimestre
            df_obitos = df_saude_mensal.copy()
            df_obitos["quadrimestre"] = df_obitos["mes"].apply(
                lambda m: 1 if m in [1, 2, 3, 4] else (2 if m in [5, 6, 7, 8] else 3)
            )

            # Agrupar óbitos totais por ano, município e quadrimestre
            df_obitos_quad = (
                df_obitos.groupby(["ano", "municipio", "quadrimestre"])
                .agg({"obitos_totais": "sum"})
                .reset_index()
            )

            # Agrupar DCNT por ano (soma de todos os quadrimestres)
            df_dcnt_sum = (
                df_dcnt.groupby(["ano", "municipio"]).agg({"dcnt": "sum"}).reset_index()
            )

            # Agrupar óbitos totais por ano (soma de todos os quadrimestres)
            df_obitos_sum = (
                df_obitos_quad.groupby(["ano", "municipio"])
                .agg({"obitos_totais": "sum"})
                .reset_index()
            )

            # Fazer merge dos dois dataframes
            df_merged = pd.merge(
                df_dcnt_sum, df_obitos_sum, on=["ano", "municipio"], how="inner"
            )

            # Calcular proporção
            df_merged["proporcao"] = (
                df_merged["dcnt"] / df_merged["obitos_totais"]
            ) * 100

            # Pivotar
            df_anual = df_merged.pivot(
                index="ano", columns="municipio", values="proporcao"
            ).sort_index()

            # Calcular variação
            df_anual_var = df_anual.diff()

            # Filtrar por anos de interesse
            if ANOS_DE_INTERESSE:
                df_anual_filtrado = df_anual[df_anual.index.isin(ANOS_DE_INTERESSE)]
            else:
                df_anual_filtrado = df_anual

            # Seletor de modo (Proporção ou Variação)
            key_anual = f"anual_mode_{key_prefix}"
            if key_anual not in st.session_state:
                st.session_state[key_anual] = label_y

            modo_anual = st.segmented_control(
                "Visualizar:",
                options=[label_y, label_var],
                key=key_anual,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_anual:
                modo_anual = label_y

            if modo_anual == label_var:
                titulo_centralizado(
                    f"Taxa de Mortalidade Prematura por Doenças Crônicas Não Transmissíveis - {label_var} Anual",
                    5,
                )
                df_var_plot = (
                    df_anual_var.copy().sort_index(ascending=True).dropna(how="all")
                )

                df_var_plot.index = df_var_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y=label_var,
                    barmode="group",
                    height=400,
                    data_label_format=fmt_var,
                    hover_label_format=fmt_var,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                titulo_centralizado(
                    "Taxa de Mortalidade Prematura por Doenças Crônicas Não Transmissíveis - Análise Anual",
                    5,
                )
                df_plot = df_anual_filtrado.copy().sort_index(ascending=False)
                df_plot.index = df_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=data_format,
                    hover_label_format=hover_format,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)

    # ========== ANÁLISE 2: PARTICIPAÇÃO DE CADA DCNT ==========
    elif tipo_analise == "Participação de cada DCNT":
        label_y = "Participação no Total de DCNT (%)"
        label_var = "Variação (p.p.)"
        data_format = ".1f"
        hover_format = ".2f"
        fmt_var = "+,.2f"

        # --- ABA 1: ACUMULADO NO ANO (QUADRIMESTRAL) ---
        if aba_selecionada == "Acumulado no Ano":
            # Obter último quadrimestre disponível
            ult_quadrimestre = int(df_mort_prematura["quadrimestre"].max())

            # Seletor de doença (Segmented Control)
            key_doenca_acum = f"doenca_acum_{key_prefix}"
            if key_doenca_acum not in st.session_state:
                st.session_state[key_doenca_acum] = "Câncer"

            doenca_selecionada = st.segmented_control(
                "Selecione a doença:",
                options=list(DOENCAS_MAP.keys()),
                key=key_doenca_acum,
                selection_mode="single",
                on_change=callback_func,
            )

            if not doenca_selecionada:
                doenca_selecionada = "Câncer"

            coluna_doenca = DOENCAS_MAP[doenca_selecionada]

            # Preparar dados
            df_calc = df_mort_prematura.copy()

            # Filtrar até o último quadrimestre
            df_acum = df_calc[df_calc["quadrimestre"] <= ult_quadrimestre].copy()

            # Agrupar por ano (soma dos quadrimestres até o último)
            df_acum_sum = (
                df_acum.groupby(["ano", "municipio"])
                .agg({coluna_doenca: "sum", "dcnt": "sum"})
                .reset_index()
            )

            # Calcular participação
            df_acum_sum["participacao"] = (
                df_acum_sum[coluna_doenca] / df_acum_sum["dcnt"]
            ) * 100

            # Pivotar
            df_acum_pivot = df_acum_sum.pivot(
                index="ano", columns="municipio", values="participacao"
            ).sort_index()

            # Calcular variação
            df_acum_var = df_acum_pivot.diff()

            # Filtrar por anos de interesse
            if ANOS_DE_INTERESSE:
                df_acum_pivot_filtrado = df_acum_pivot[
                    df_acum_pivot.index.isin(ANOS_DE_INTERESSE)
                ]
            else:
                df_acum_pivot_filtrado = df_acum_pivot

            # Seletor de modo (Participação ou Variação)
            key_acum = f"acum_mode_part_{key_prefix}"
            if key_acum not in st.session_state:
                st.session_state[key_acum] = label_y

            modo_acum = st.segmented_control(
                "Visualizar:",
                options=[label_y, label_var],
                key=key_acum,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_acum:
                modo_acum = label_y

            periodo_txt = QUADRIMESTRES_LABEL.get(
                ult_quadrimestre, f"{ult_quadrimestre}º Quadrimestre"
            )

            if modo_acum == label_var:
                titulo_centralizado(
                    f"Participação de {doenca_selecionada} no Total de Mortes Prematuras por DCNT - {label_var} - Até {periodo_txt}",
                    5,
                )
                df_var_plot = (
                    df_acum_var.copy().sort_index(ascending=True).dropna(how="all")
                )
                df_var_plot.index = (
                    "1º-"
                    + str(ult_quadrimestre)
                    + "º Quadrimestre/"
                    + df_var_plot.index.astype(str).str.slice(-2)
                )

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y=label_var,
                    barmode="group",
                    height=400,
                    data_label_format=fmt_var,
                    hover_label_format=fmt_var,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                titulo_centralizado(
                    f"Participação de {doenca_selecionada} no Total de Mortes Prematuras por DCNT - Até {periodo_txt}",
                    5,
                )
                df_plot = df_acum_pivot_filtrado.copy()
                df_plot.index = (
                    "1º-"
                    + str(ult_quadrimestre)
                    + "º Quadrimestre/"
                    + df_plot.index.astype(str).str.slice(-2)
                )

                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=data_format,
                    hover_label_format=hover_format,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)

        # --- ABA 2: ANUAL ---
        elif aba_selecionada == "Anual":
            # Seletor de doença (Segmented Control)
            key_doenca_anual = f"doenca_anual_{key_prefix}"
            if key_doenca_anual not in st.session_state:
                st.session_state[key_doenca_anual] = "Câncer"

            doenca_selecionada = st.segmented_control(
                "Selecione a doença:",
                options=list(DOENCAS_MAP.keys()),
                key=key_doenca_anual,
                selection_mode="single",
                on_change=callback_func,
            )

            if not doenca_selecionada:
                doenca_selecionada = "Câncer"

            coluna_doenca = DOENCAS_MAP[doenca_selecionada]

            # Preparar dados
            df_calc = df_mort_prematura.copy()

            # Agrupar por ano e município (soma de todos os quadrimestres)
            df_anual_sum = (
                df_calc.groupby(["ano", "municipio"])
                .agg({coluna_doenca: "sum", "dcnt": "sum"})
                .reset_index()
            )

            # Calcular participação
            df_anual_sum["participacao"] = (
                df_anual_sum[coluna_doenca] / df_anual_sum["dcnt"]
            ) * 100

            # Pivotar
            df_anual = df_anual_sum.pivot(
                index="ano", columns="municipio", values="participacao"
            ).sort_index()

            # Calcular variação
            df_anual_var = df_anual.diff()

            # Filtrar por anos de interesse
            if ANOS_DE_INTERESSE:
                df_anual_filtrado = df_anual[df_anual.index.isin(ANOS_DE_INTERESSE)]
            else:
                df_anual_filtrado = df_anual

            # Seletor de modo (Participação ou Variação)
            key_anual = f"anual_mode_part_{key_prefix}"
            if key_anual not in st.session_state:
                st.session_state[key_anual] = label_y

            modo_anual = st.segmented_control(
                "Visualizar:",
                options=[label_y, label_var],
                key=key_anual,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_anual:
                modo_anual = label_y

            if modo_anual == label_var:
                titulo_centralizado(
                    f"Participação de {doenca_selecionada} no Total de Mortes Prematuras por DCNT - {label_var} Anual",
                    5,
                )
                df_var_plot = (
                    df_anual_var.copy().sort_index(ascending=True).dropna(how="all")
                )

                df_var_plot.index = df_var_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y=label_var,
                    barmode="group",
                    height=400,
                    data_label_format=fmt_var,
                    hover_label_format=fmt_var,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                titulo_centralizado(
                    f"Participação de {doenca_selecionada} no Total de Mortes Prematuras por DCNT - Análise Anual",
                    5,
                )
                df_plot = df_anual_filtrado.copy().sort_index(ascending=False)
                df_plot.index = df_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=data_format,
                    hover_label_format=hover_format,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)


def display_sisab_expander(
    df_sisab,
    titulo_expander,
    dicionario_indicadores,
    key_prefix,
    expander_state_key,
    callback_func,
):
    """Função especializada para exibir indicadores SISAB (dados quadrimestrais)."""
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(titulo_expander, expanded=st.session_state[expander_state_key]):
        # Disclaimer sobre a descontinuação da série
        st.warning(
            "⚠️ **Atenção:** A série histórica do SISAB foi descontinuada pelo Ministério da Saúde. "
            "Os dados apresentados referem-se ao período em que o sistema estava ativo."
        )

        if df_sisab is None or df_sisab.empty:
            st.warning("Dados SISAB não disponíveis.")
            return

        # Seletor de indicador
        indicador_selecionado = st.selectbox(
            "Selecione um indicador para visualizar:",
            options=list(dicionario_indicadores.keys()),
            key=f"{key_prefix}_selectbox",
            on_change=callback_func,
        )

        coluna_selecionada, label_y, data_format = dicionario_indicadores[
            indicador_selecionado
        ]

        # Preparar dados
        df_com_dados = df_sisab[df_sisab[coluna_selecionada].notna()].copy()

        if df_com_dados.empty:
            st.warning(f"Não há dados disponíveis para {indicador_selecionado}.")
            return

        # Obter anos disponíveis
        anos_disponiveis = sorted(df_com_dados["ano"].unique())

        if len(anos_disponiveis) < 2:
            anos_padrao = anos_disponiveis
        else:
            # Seleciona os dois últimos anos como padrão
            anos_padrao = anos_disponiveis[-2:]

        # Seletor de range de anos em coluna de 60%
        col_slider, col_empty = st.columns([0.6, 0.4])
        with col_slider:
            anos_selecionados = st.slider(
                "Selecione o período de análise:",
                min_value=int(min(anos_disponiveis)),
                max_value=int(max(anos_disponiveis)),
                value=(int(min(anos_padrao)), int(max(anos_padrao))),
                key=f"{key_prefix}_anos_slider",
            )

        # Filtrar dados pelos anos selecionados
        df_filtrado = df_com_dados[
            (df_com_dados["ano"] >= anos_selecionados[0])
            & (df_com_dados["ano"] <= anos_selecionados[1])
        ].copy()

        if df_filtrado.empty:
            st.warning("Não há dados para o período selecionado.")
            return

        # Criar coluna de período (ano + quadrimestre)
        df_filtrado["periodo"] = (
            df_filtrado["ano"].astype(str)
            + " - Q"
            + df_filtrado["quadrimestre"].astype(str)
        )

        # Ordenar por ano e quadrimestre para garantir ordem cronológica
        df_filtrado = df_filtrado.sort_values(["ano", "quadrimestre"])

        # Pivotar dados
        df_pivot = df_filtrado.pivot(
            index="periodo", columns="municipio", values=coluna_selecionada
        )

        # Verificar se há dados para exibir
        if df_pivot.empty:
            st.warning("Não há dados suficientes para gerar o gráfico.")
            return

        # Determinar formato de hover
        hover_format = (
            f",.{int(data_format.split('.')[-1][0]) + 1}f"
            if "." in data_format
            else ",.0f"
        )

        # Título
        titulo_centralizado(indicador_selecionado, 5)

        # Criar gráfico
        fig = criar_grafico_barras(
            df=df_pivot,
            titulo="",
            label_y=label_y,
            barmode="group",
            height=400,
            data_label_format=data_format,
            hover_label_format=hover_format,
            color_map=CORES_MUNICIPIOS,
        )
        st.plotly_chart(fig, use_container_width=True)


def display_saude_expander(
    df_filtrado,
    titulo_expander,
    dicionario_indicadores,
    key_prefix,
    expander_state_key,
    callback_func,
    df_mort_prematura=None,
):
    """Função genérica para exibir uma seção de indicadores de saúde."""
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(titulo_expander, expanded=st.session_state[expander_state_key]):
        # Verifica se os dados estão disponíveis
        if df_filtrado is None or df_filtrado.empty:
            st.warning(f"Dados não disponíveis para {titulo_expander}.")
            return

        indicador_selecionado = st.selectbox(
            "Selecione um indicador para visualizar:",
            options=list(dicionario_indicadores.keys()),
            key=f"{key_prefix}_selectbox",
            on_change=callback_func,
        )

        # TRATAMENTO ESPECIAL PARA MORTALIDADE PREMATURA
        if indicador_selecionado == "Taxa de Mortalidade Prematura por DCNT":
            if df_mort_prematura is not None and not df_mort_prematura.empty:
                display_mortalidade_prematura(
                    df_mort_prematura, df_filtrado, key_prefix, callback_func
                )
            else:
                st.warning("Dados de mortalidade prematura não disponíveis.")
            return

        # --- LÓGICA PADRÃO PARA GRÁFICOS ---
        config_indicador = dicionario_indicadores[indicador_selecionado]

        # Desempacotar configuração do indicador
        if len(config_indicador) == 4:
            # Formato antigo: (coluna, agg_method, label_y, data_format)
            coluna_selecionada, agg_method, label_y, data_format = config_indicador
            col_numerador = None
            col_denominador = None
            fator_mult = 1
        else:
            # Formato novo: (coluna, agg_method, label_y, data_format, col_num, col_den, fator)
            (
                coluna_selecionada,
                agg_method,
                label_y,
                data_format,
                col_numerador,
                col_denominador,
                fator_mult,
            ) = config_indicador

        # Verifica se é taxa/proporção para definir tipo de variação
        is_taxa = agg_method == "ratio"
        label_var = "Variação (p.p.)" if is_taxa else "Variação (%)"
        fmt_var = "+,.2f" if is_taxa else "+,.1f"

        hover_format = (
            f",.{int(data_format.split('.')[-1][0]) + 1}f"
            if "." in data_format
            else ",.0f"
        )

        df_hist, df_acum, df_acum_var, df_anual, df_anual_var, ult_ano, ult_mes = (
            preparar_dados_graficos_saude_mensal(
                df_filtrado,
                coluna_selecionada,
                agg_method,
                anos_visualizacao=ANOS_DE_INTERESSE,
                col_numerador=col_numerador,
                col_denominador=col_denominador,
                fator_multiplicacao=fator_mult,
            )
        )

        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = f"main_tab_nav_{key_prefix}"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Acumulado no Ano"

        aba_selecionada = st.pills(
            "Selecione o tipo de análise temporal:",
            options=["Acumulado no Ano", "Anual"],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = "Acumulado no Ano"

        # --- ABA 1: ACUMULADO NO ANO ---
        if aba_selecionada == "Acumulado no Ano":
            if ult_mes:
                # Seletor de modo
                key_acum = f"acum_mode_{key_prefix}"
                if key_acum not in st.session_state:
                    st.session_state[key_acum] = label_y

                modo_acum = st.segmented_control(
                    "Visualizar:",
                    options=[label_y, label_var],
                    key=key_acum,
                    selection_mode="single",
                    on_change=callback_func,
                )

                if not modo_acum:
                    modo_acum = label_y

                periodo_txt = f"Jan a {MESES_DIC[ult_mes][:3]}"

                if modo_acum == label_var:
                    titulo_centralizado(
                        f"{indicador_selecionado} - {label_var} - {periodo_txt}", 5
                    )
                    df_var_plot = df_acum_var.copy().sort_index(ascending=True)

                    # Remove anos com variação nula
                    df_var_plot = df_var_plot.dropna(how="all")

                    df_var_plot.index = (
                        "Jan-"
                        + MESES_DIC[ult_mes][:3]
                        + "/"
                        + df_var_plot.index.astype(str).str.slice(-2)
                    )

                    fig = criar_grafico_barras(
                        df=df_var_plot,
                        titulo="",
                        label_y=label_var,
                        barmode="group",
                        height=400,
                        data_label_format=fmt_var,
                        hover_label_format=fmt_var,
                        color_map=CORES_MUNICIPIOS,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    df_plot = df_acum.copy()
                    df_plot.index = (
                        "Jan-"
                        + MESES_DIC[ult_mes][:3]
                        + "/"
                        + df_plot.index.astype(str).str.slice(-2)
                    )
                    titulo_centralizado(
                        f"{indicador_selecionado} - {periodo_txt}",
                        5,
                    )
                    fig = criar_grafico_barras(
                        df=df_plot,
                        titulo="",
                        label_y=label_y,
                        barmode="group",
                        height=400,
                        data_label_format=data_format,
                        hover_label_format=hover_format,
                        color_map=CORES_MUNICIPIOS,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Dados acumulados não disponíveis.")

        # --- ABA 2: ANUAL ---
        elif aba_selecionada == "Anual":
            # Seletor de modo
            key_anual = f"anual_mode_{key_prefix}"
            if key_anual not in st.session_state:
                st.session_state[key_anual] = label_y

            modo_anual = st.segmented_control(
                "Visualizar:",
                options=[label_y, label_var],
                key=key_anual,
                selection_mode="single",
                on_change=callback_func,
            )

            if not modo_anual:
                modo_anual = label_y

            if modo_anual == label_var:
                titulo_centralizado(f"{indicador_selecionado} - {label_var} Anual", 5)
                df_var_plot = df_anual_var.copy()

                # Remove anos com variação nula
                df_var_plot = df_var_plot.dropna(how="all")

                df_var_plot = df_var_plot.sort_index(ascending=True)
                df_var_plot.index = df_var_plot.index.astype(str)

                fig = criar_grafico_barras(
                    df=df_var_plot,
                    titulo="",
                    label_y=label_var,
                    barmode="group",
                    height=400,
                    data_label_format=fmt_var,
                    hover_label_format=fmt_var,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
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

        # Verifica se é percentual/cobertura para definir tipo de variação
        is_percentual = (
            "(%)" in indicador_selecionado
            or "Cobertura" in indicador_selecionado
            or "Percentual" in indicador_selecionado
        )
        label_var = "Variação (p.p.)" if is_percentual else "Variação (%)"
        fmt_var = "+,.2f" if is_percentual else "+,.1f"

        hover_format = (
            f",.{int(data_format.split('.')[-1][0]) + 1}f"
            if "." in data_format
            else ",.0f"
        )

        df_anual, df_anual_var = preparar_dados_graficos_saude_anual(
            df_filtrado=df_filtrado,
            coluna_selecionada=coluna_selecionada,
            is_percentual=is_percentual,
            anos_visualizacao=ANOS_DE_INTERESSE,
        )

        # --- NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = f"main_tab_nav_{key_prefix}"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = label_y

        aba_selecionada = st.pills(
            "Selecione a visualização:",
            options=[label_y, label_var],
            selection_mode="single",
            key=key_main_tab,
        )

        if not aba_selecionada:
            aba_selecionada = label_y

        if aba_selecionada == label_var:
            titulo_centralizado(f"{indicador_selecionado} - {label_var}", 5)
            df_var_plot = df_anual_var.copy()

            # Remove anos com variação nula
            df_var_plot = df_var_plot.dropna(how="all")

            df_var_plot = df_var_plot.sort_index(ascending=True)
            df_var_plot.index = df_var_plot.index.astype(str)

            fig = criar_grafico_barras(
                df=df_var_plot,
                titulo="",
                label_y=label_var,
                barmode="group",
                height=400,
                data_label_format=fmt_var,
                hover_label_format=fmt_var,
                color_map=CORES_MUNICIPIOS,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            titulo_centralizado(f"{indicador_selecionado}", 5)
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
    df_saude_internacoes_residentes=None,
    df_saude_mort_prematura=None,
    df_obitos_tipo=None,
    df_saude_sisab=None,
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
    if "internacoes_residentes_expander_state" not in st.session_state:
        st.session_state.internacoes_residentes_expander_state = False
    if "sisab_expander_state" not in st.session_state:
        st.session_state.sisab_expander_state = False
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
    if "obitos_causa_basica_expander_state" not in st.session_state:
        st.session_state.obitos_causa_basica_expander_state = False

    # Calcular colunas de percentual para médicos e leitos
    if (
        not df_saude_medicos.empty
        and "qtd_medicos" in df_saude_medicos.columns
        and "qtd_medicos_sus" in df_saude_medicos.columns
    ):
        df_saude_medicos = df_saude_medicos.copy()
        df_saude_medicos["percentual_medicos_sus"] = (
            df_saude_medicos["qtd_medicos_sus"]
            * 100.0
            / df_saude_medicos["qtd_medicos"].replace(0, pd.NA)
        ).round(1)

    if (
        not df_saude_leitos.empty
        and "qtd_leitos" in df_saude_leitos.columns
        and "qtd_leitos_sus" in df_saude_leitos.columns
    ):
        df_saude_leitos = df_saude_leitos.copy()
        df_saude_leitos["percentual_leitos_sus"] = (
            df_saude_leitos["qtd_leitos_sus"]
            * 100.0
            / df_saude_leitos["qtd_leitos"].replace(0, pd.NA)
        ).round(1)

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
            None,
            "ratio",
            "Proporção (%)",
            ".1f",
            "obitos_causa_definida",  # numerador
            "obitos_totais",  # denominador
            100,  # fator para percentual
        ),
        "Proporção de Óbitos com Causas Não Definidas (%)": (
            None,
            "ratio",
            "Proporção (%)",
            ".1f",
            "obitos_causa_nao_definida",
            "obitos_totais",
            100,
        ),
        "Taxa de Mortalidade Prematura por DCNT": (
            "dcnt",
            "mortality_rate",
            "Taxa por 100 mil hab.",
            ".1f",
        ),
    }

    INDICADORES_NASCIMENTOS = {
        "Nascidos Vivos": ("nascimentos_total", "sum", "Nº de Nascidos", ",.0f"),
        "Nascidos por Mil Habitantes": (
            "nascimentos/1000_hab",
            "sum",
            "Nascidos por mil hab.",
            ".2f",
        ),
        "Mortalidade Infantil (por mil nascidos vivos)": (
            None,
            "ratio",
            "Taxa de Mort. Infantil por mil nasc.",
            ".1f",
            "obitos_infantis",
            "nascimentos_mort_infantil",
            1000,
        ),
        "Proporção de Nascidos Vivos com Baixo Peso ao Nascer (%)": (
            None,
            "ratio",
            "Prop. de Nascidos Vivos (%)",
            ".1f",
            "nasc_baixo_peso",
            "nascimentos_total",
            100,
        ),
        "Proporção de Nascidos Vivos com Sete ou Mais Consultas de Pré-Natal (%)": (
            None,
            "ratio",
            "Prop. de Nascidos Vivos (%)",
            ".1f",
            "consultas_pre_natal",
            "nascimentos_pre_natal_total",
            100,
        ),
    }

    INDICADORES_GESTANTES = {
        "Proporção de Gravidez na Adolescência entre as Faixas Etárias 10 a 19 anos (%)": (
            None,
            "ratio",
            "Prop. de Gravidez (%)",
            ".1f",
            "num_adolescentes",
            "nascimentos_adolesc",
            100,
        ),
        "Coeficiente de Mortalidade Neonatal (por mil nascidos vivos)": (
            None,
            "ratio",
            "Coeficiente por mil nascidos vivos",
            ".1f",
            "obitos_neonatal",
            "nascimentos_total",
            1000,
        ),
        "Número de casos novos de sífilis congênita em menores de 1 ano de idade": (
            "casos_sifilis_congenita",
            "sum",
            "Nº de casos",
            ",.0f",
        ),
    }
    INDICADORES_ATENCAO_BASICA_MENSAL = {
        "Internações por Condições Sensíveis à Atenção Básica - ICSAB": (
            "internacoes_icsab",
            "sum",
            "Núm. de Internações",
            ",.0f",
        ),
        "Proporção das Internações por Condições Sensíveis à Atenção Básica - ICSAB (%)": (
            None,
            "ratio",
            "Prop. de Internações (%)",
            ".1f",
            "internacoes_icsab",
            "internacoes_totais",
            100,
        ),
    }
    INDICADORES_INTERNACOES_HOSPITALARES = {
        "Total de Internações no Município": (
            "internacoes_total",
            "sum",
            "Núm. de Internações",
            ",.0f",
        ),
        "Total de Internações no Município de Residentes": (
            "internacoes_municipio",
            "sum",
            "Núm. de Internações",
            ",.0f",
        ),
        "Participação de Residentes no Total de Internações Hospitalares (%)": (
            None,
            "ratio",
            "Participação (%)",
            ".1f",
            "internacoes_municipio",
            "internacoes_total",
            100,
        ),
    }

    INDICADORES_SISAB = {
        "Proporção de gestantes com pelo menos 6 consultas pré-natal realizadas, sendo a 1ª até a 12ª semana de gestação": (
            "gestantes_pre_natal",
            "Proporção (%)",
            ".1f",
        ),
        "Proporção de gestantes com realização de exames para sífilis e HIV": (
            "gestantes_sifilis",
            "Proporção (%)",
            ".1f",
        ),
        "Proporção de gestantes com atendimento odontológico realizado": (
            "gestantes_odonto",
            "Proporção (%)",
            ".1f",
        ),
        "Proporção de mulheres com coleta de citopatológico na APS": (
            "mulheres_cito",
            "Proporção (%)",
            ".1f",
        ),
        "Proporção de crianças de 1 ano de idade vacinadas na APS contra Difteria, Tétano, Coqueluche, Hepatite B, infecções causadas por haemophilus influenzae tipo b e Poliomielite inativada": (
            "criancas_vacinadas_aps",
            "Proporção (%)",
            ".1f",
        ),
        "Proporção de pessoas com hipertensão, com consulta e pressão arterial aferida no semestre": (
            "consultas_hipertensao",
            "Proporção (%)",
            ".1f",
        ),
        "Proporção de pessoas com diabetes, com consulta e hemoglobina glicada solicitada no semestre": (
            "consultas_diabetes",
            "Proporção (%)",
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
            None,
            "ratio",
            "Taxa por 10 mil Hab.",
            ".2f",
            "notificacoes_acidentes_trab",
            "populacao",
            10000,
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
        "Número Total de Médicos": (
            "qtd_medicos",
            "Núm. de Médicos",
            ",.0f",
        ),
        "Número de Médicos que atendem pelo SUS": (
            "qtd_medicos_sus",
            "Núm. de Médicos",
            ",.0f",
        ),
        "Percentual de Médicos que atendem pelo SUS (%)": (
            "percentual_medicos_sus",
            "Percentual (%)",
            ",.1f",
        ),
        "Número de Médicos que atendem pelo SUS por mil habitantes": (
            "qtd_medicos_sus_mil_hab",
            "Núm. de Médicos por mil hab.",
            ",.2f",
        ),
    }

    INDICADORES_LEITOS = {
        "Número Total de Leitos de Internação e Complementares": (
            "qtd_leitos",
            "Núm. de Leitos",
            ",.0f",
        ),
        "Número de Leitos de Internação e Complementares disponíveis pelo SUS": (
            "qtd_leitos_sus",
            "Núm. de Leitos",
            ",.0f",
        ),
        "Percentual de Leitos disponíveis pelo SUS (%)": (
            "percentual_leitos_sus",
            "Percentual (%)",
            ",.1f",
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
        df_mort_prematura=df_saude_mort_prematura,
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
        df_filtrado=df_saude_internacoes_residentes,
        titulo_expander="Internações Hospitalares",
        dicionario_indicadores=INDICADORES_INTERNACOES_HOSPITALARES,
        key_prefix="internacoes_residentes",
        expander_state_key="internacoes_residentes_expander_state",
        callback_func=internacoes_residentes_callback,
    )

    # Disclaimer sobre descontinuação do SISAB

    display_sisab_expander(
        df_sisab=df_saude_sisab,
        titulo_expander="Indicadores SISAB - Sistema de Informação em Saúde para a Atenção Básica (Série Descontinuada)",
        dicionario_indicadores=INDICADORES_SISAB,
        key_prefix="sisab",
        expander_state_key="sisab_expander_state",
        callback_func=sisab_callback,
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

    display_obitos_causa_basica_expander(
        df_obitos_tipo=df_obitos_tipo,
        expander_state_key="obitos_causa_basica_expander_state",
        callback_func=obitos_causa_basica_callback,
    )

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
        titulo_expander="Médicos",
        dicionario_indicadores=INDICADORES_MEDICOS,
        key_prefix="medicos",
        expander_state_key="medicos_expander_state",
        callback_func=medicos_callback,
    )

    display_saude_anual_expander(
        df_filtrado=df_saude_leitos,
        titulo_expander="Leitos de Internação e Complementares",
        dicionario_indicadores=INDICADORES_LEITOS,
        key_prefix="leitos",
        expander_state_key="leitos_expander_state",
        callback_func=leitos_callback,
    )
