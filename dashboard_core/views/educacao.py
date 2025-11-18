import pandas as pd
import streamlit as st

from dashboard_core.utils import (
    criar_grafico_barras,
    titulo_centralizado,
)

CORES_MUNICIPIOS = {}


def set_educacao_config(cores_municipios):
    """
    Configura valores específicos do município que antes eram importados
    do dashboard_core.config. Deve ser chamado pelo app.py antes de
    renderizar a página de educacao.
    """
    global CORES_MUNICIPIOS
    CORES_MUNICIPIOS = cores_municipios or {}


# --- FUNÇÕES DE CALLBACK ---


def set_expander_open(key):
    """Define o estado de um expander específico como True (aberto)."""
    st.session_state[key] = True


# Funções específicas para callbacks (melhorando a rastreabilidade em relação a lambdas)
def escolas_callback():
    set_expander_open("escolas_expander_state")


def matriculas_callback():
    set_expander_open("matriculas_expander_state")


def docentes_callback():
    set_expander_open("docentes_expander_state")


def turmas_callback():
    set_expander_open("turmas_expander_state")


def rendimento_callback():
    set_expander_open("rendimento_expander_state")


def ideb_mun_callback():
    set_expander_open("ideb_mun_expander_state")


def ideb_escolas_callback():
    set_expander_open("ideb_escolas_expander_state")


@st.cache_data
def preparar_dados_grafico_educacao(
    df_filtrado, coluna_selecionada, dependencia, municipios_selecionados
):
    if df_filtrado.empty:
        return pd.DataFrame()

    df_processed = pd.DataFrame()

    if dependencia == "total":
        total_pre_calculado = df_filtrado[df_filtrado["dependencia"] == "total"]

        if not total_pre_calculado.empty:
            df_processed = total_pre_calculado
        else:
            df_processed = df_filtrado.groupby(
                ["ano", "municipio"], as_index=False
            ).agg({coluna_selecionada: "sum"})
    else:
        df_processed = df_filtrado[df_filtrado["dependencia"] == dependencia]

    if df_processed.empty:
        return pd.DataFrame()

    anos = sorted(df_filtrado["ano"].unique())

    df_grid = pd.MultiIndex.from_product(
        [anos, municipios_selecionados], names=["ano", "municipio"]
    ).to_frame(index=False)

    df_completo = pd.merge(
        df_grid, df_processed, on=["ano", "municipio"], how="left"
    ).fillna(0)

    df_graf = df_completo.pivot_table(
        index="ano",
        columns="municipio",
        values=coluna_selecionada,
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    return df_graf


@st.cache_data
def preparar_dados_grafico_ideb_municipio(
    df, indicador, categoria, dependencia, municipios_selecionados
):
    df_filtrado = df[
        (df["dependencia"] == dependencia)
        & (df["indicador"] == indicador)
        & (df["categoria"] == categoria)
    ]

    anos = sorted(df_filtrado["ano"].unique())

    df_grid = pd.MultiIndex.from_product(
        [anos, municipios_selecionados], names=["ano", "municipio"]
    ).to_frame(index=False)

    df_completo = pd.merge(
        df_grid, df_filtrado, on=["ano", "municipio"], how="left"
    ).fillna(0)

    df_graf = df_completo.pivot_table(
        index="ano",
        columns="municipio",
        values="valor",
        aggfunc="sum",
        fill_value=0,
    ).sort_index()

    return df_graf


@st.cache_data
def preparar_dados_tabela_ideb_escolas(df, categoria, dependencia):
    df_filtrado = df[
        (df["dependencia"] == dependencia) & (df["categoria"] == categoria)
    ]

    df_tab = (
        df_filtrado.pivot_table(
            index=["ano", "municipio", "escola"],
            columns="indicador",
            values="valor",
            aggfunc="sum",
        ).assign(nota_media=lambda x: (x["nota_mat"] + x["nota_port"]) / 2)
    ).sort_values(by="nota_media", ascending=False)

    return df_tab


def display_educacao(
    df_filtrado,
    municipios_selecionados,
    titulo_expander,
    key_prefix,
    dicionario_indicadores,
    dicionario_dependencia,
    label_y,
    data_label_format,
    hover_label_format,
    expander_state_key,  # NOVO
    callback_func,  # NOVO
):
    """Função genérica para exibir a seção de educacao matriculas e rendimento."""

    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(
        f"{titulo_expander}", expanded=st.session_state[expander_state_key]
    ):
        titulo_centralizado(f"Indicadores de {titulo_expander}", 5)
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            indicador_selecionado = st.selectbox(
                "Selecione um indicador:",
                options=list(dicionario_indicadores.keys()),
                key=f"{key_prefix}_selectbox_indicadores",
                on_change=callback_func,  # ADICIONADO CALLBACK
            )
        with col2:
            dependecia_selecionada = st.selectbox(
                "Selecione uma dependência:",
                options=list(dicionario_dependencia.keys()),
                key=f"{key_prefix}_selectbox_dependencia",
                on_change=callback_func,  # ADICIONADO CALLBACK
            )

        coluna_selecionada = dicionario_indicadores[indicador_selecionado]

        dependencia_selecionada = dicionario_dependencia[dependecia_selecionada]

        df_graf = preparar_dados_grafico_educacao(
            df_filtrado=df_filtrado,
            coluna_selecionada=coluna_selecionada,
            dependencia=dependencia_selecionada,
            municipios_selecionados=municipios_selecionados,
        )

        titulo_centralizado(
            f"{titulo_expander} - {indicador_selecionado} - {dependecia_selecionada}", 5
        )
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
        st.plotly_chart(
            fig, use_container_width=True
        )  # Ajustado para use_container_width=True


def display_taxa_rendimento(
    df_filtrado,
    municipios_selecionados,
    titulo_expander,
    key_prefix,
    dicionario_indicador_base,
    dicionario_nivel_ensino,
    dicionario_dependencia,
    label_y,
    data_label_format,
    hover_label_format,
    expander_state_key,  # NOVO
    callback_func,  # NOVO
):
    """Função específica para Taxas de Rendimento com 3 seletores."""

    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(
        f"{titulo_expander}", expanded=st.session_state[expander_state_key]
    ):
        titulo_centralizado(f"Indicadores de {titulo_expander}", 5)

        col1, col2, col3 = st.columns([0.3, 0.4, 0.3])

        with col1:
            indicador_selecionado_label = st.selectbox(
                "Selecione um indicador:",
                options=list(dicionario_indicador_base.keys()),
                key=f"{key_prefix}_selectbox_indicador",
                on_change=callback_func,  # ADICIONADO CALLBACK
            )
        with col2:
            nivel_selecionado_label = st.selectbox(
                "Selecione o nível de ensino:",
                options=list(dicionario_nivel_ensino.keys()),
                key=f"{key_prefix}_selectbox_nivel",
                on_change=callback_func,  # ADICIONADO CALLBACK
            )
        with col3:
            dependencia_selecionada_label = st.selectbox(
                "Selecione uma dependência:",
                options=list(dicionario_dependencia.keys()),
                key=f"{key_prefix}_selectbox_dependencia",
                on_change=callback_func,  # ADICIONADO CALLBACK
            )

        indicador_base = dicionario_indicador_base[indicador_selecionado_label]
        nivel_base = dicionario_nivel_ensino[nivel_selecionado_label]
        dependencia_valor = dicionario_dependencia[dependencia_selecionada_label]

        coluna_selecionada = f"{indicador_base}_{nivel_base}"

        df_graf = preparar_dados_grafico_educacao(
            df_filtrado=df_filtrado,
            coluna_selecionada=coluna_selecionada,
            dependencia=dependencia_valor,
            municipios_selecionados=municipios_selecionados,
        )

        titulo_centralizado(
            f"{indicador_selecionado_label} - {nivel_selecionado_label} - {dependencia_selecionada_label}",
            5,
        )

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
        st.plotly_chart(
            fig, use_container_width=True
        )  # Ajustado para use_container_width=True


def display_ideb_mun(
    df_filtrado,
    municipios_selecionados,
    titulo_expander,
    key_prefix,
    dicionario_indicadores,
    dicionario_dependencia,
    dicionario_categoria,
    expander_state_key,  # NOVO
    callback_func,  # NOVO
):
    """Função genérica para exibir a seção de IDEB MUNCIPIOS."""

    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(
        f"{titulo_expander}", expanded=st.session_state[expander_state_key]
    ):
        titulo_centralizado(f"Indicadores do {titulo_expander}", 5)
        titulo_centralizado(
            "O Índice de Desenvolvimento da Educação Básica (Ideb) reúne, em um só indicador, os resultados de dois conceitos igualmente importantes para a qualidade da educação: o fluxo escolar e as médias de desempenho nas avaliações. O Ideb é calculado a partir dos dados sobre aprovação escolar, obtidos no Censo Escolar, e das médias de desempenho no Sistema de Avaliação da Educação Básica (Saeb).",
            6,
        )
        col1, col2, col3 = st.columns([0.4, 0.3, 0.3])
        with col1:
            categoria_selecionada = st.selectbox(
                "Selecione uma etapa de ensino:",
                options=list(dicionario_categoria.keys()),
                key=f"{key_prefix}_selectbox_categoria",
                on_change=callback_func,  # ADICIONADO CALLBACK
            )
        with col2:
            indicador_selecionado = st.selectbox(
                "Selecione um indicador:",
                options=list(dicionario_indicadores.keys()),
                key=f"{key_prefix}_selectbox_indicadores",
                on_change=callback_func,  # ADICIONADO CALLBACK
            )
        with col3:
            dependencia_selecionada = st.selectbox(
                "Selecione uma dependência:",
                options=list(dicionario_dependencia.keys()),
                key=f"{key_prefix}_selectbox_dependencia",
                on_change=callback_func,  # ADICIONADO CALLBACK
            )

        categoria = dicionario_categoria[categoria_selecionada]

        indicador = dicionario_indicadores[indicador_selecionado]

        dependencia = dicionario_dependencia[dependencia_selecionada]

        df_graf = preparar_dados_grafico_ideb_municipio(
            df=df_filtrado,
            categoria=categoria,
            indicador=indicador,
            dependencia=dependencia,
            municipios_selecionados=municipios_selecionados,
        )

        if not df_graf.empty:
            df_graf.index = df_graf.index.astype(str)

        titulo_centralizado(
            f"{indicador_selecionado} - {dependencia_selecionada}",
            5,
        )
        fig = criar_grafico_barras(
            df=df_graf,
            titulo="",
            label_y=f"{indicador_selecionado}",
            barmode="group",
            height=400,
            data_label_format=",.1f",
            hover_label_format=",.1f",
            color_map=CORES_MUNICIPIOS,
        )
        st.plotly_chart(
            fig, use_container_width=True
        )  # Ajustado para use_container_width=True


def display_ideb_escolas(
    df_filtrado,
    titulo_expander,
    key_prefix,
    dicionario_dependencia,
    dicionario_categoria,
    expander_state_key,  # NOVO
    callback_func,  # NOVO
):
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(
        f"{titulo_expander}", expanded=st.session_state[expander_state_key]
    ):
        titulo_centralizado(f"Indicadores do {titulo_expander}", 5)
        titulo_centralizado(
            "O Índice de Desenvolvimento da Educação Básica (Ideb) reúne, em um só indicador, os resultados de dois conceitos igualmente importantes para a qualidade da educação: o fluxo escolar e as médias de desempenho nas avaliações. O Ideb é calculado a partir dos dados sobre aprovação escolar, obtidos no Censo Escolar, e das médias de desempenho no Sistema de Avaliação da Educação Básica (Saeb).",
            6,
        )

        anos_disponiveis = sorted(df_filtrado["ano"].unique().tolist(), reverse=True)
        col1, col2, col3 = st.columns([0.2, 0.4, 0.4])
        with col1:
            ANO_SELECIONADO = st.selectbox(
                "Selecione o ano para a tabela:",
                options=anos_disponiveis,
                index=0,
                key="hist_ano_escolas",
                on_change=callback_func,
            )

        df_filtrado = df_filtrado[df_filtrado["ano"] == ANO_SELECIONADO]
        with col2:
            categoria_selecionada = st.selectbox(
                "Selecione uma etapa de ensino:",
                options=list(dicionario_categoria.keys()),
                key=f"{key_prefix}_selectbox_categoria",
                on_change=callback_func,
            )
        with col3:
            dependencia_selecionada = st.selectbox(
                "Selecione uma dependência:",
                options=list(dicionario_dependencia.keys()),
                key=f"{key_prefix}_selectbox_dependencia",
                on_change=callback_func,
            )

        categoria = dicionario_categoria[categoria_selecionada]

        dependencia = dicionario_dependencia[dependencia_selecionada]

        df_tab = preparar_dados_tabela_ideb_escolas(
            df_filtrado, categoria=categoria, dependencia=dependencia
        ).query("ideb != 0")

        df_tab_renomeado = (
            df_tab.rename_axis(
                index={"ano": "Ano", "municipio": "Município", "escola": "Escola"}
            )
            .rename(
                columns={
                    "ideb": "IDEB",
                    "nota_mat": "Nota SAEB Matemática",
                    "nota_port": "Nota SAEB Português",
                    "nota_media": "Nota SAEB Média",
                }
            )
            .style.format(lambda x: f"{x:,.2f}".replace(".", ","))
            .background_gradient(cmap="GnBu")
        )

        st.dataframe(
            df_tab_renomeado, use_container_width=True
        )  # Ajustado para use_container_width=True


def show_page_educacao(
    df_matriculas,
    df_rendimento,
    df_ideb_municipio,
    df_ideb_escolas,
    municipios_selecionados_global,
):
    # 1. INICIALIZAÇÃO DOS ESTADOS DOS EXPANDERS (Fechados por padrão)
    if "escolas_expander_state" not in st.session_state:
        st.session_state.escolas_expander_state = False
    if "matriculas_expander_state" not in st.session_state:
        st.session_state.matriculas_expander_state = False
    if "docentes_expander_state" not in st.session_state:
        st.session_state.docentes_expander_state = False
    if "turmas_expander_state" not in st.session_state:
        st.session_state.turmas_expander_state = False
    if "rendimento_expander_state" not in st.session_state:
        st.session_state.rendimento_expander_state = False
    if "ideb_mun_expander_state" not in st.session_state:
        st.session_state.ideb_mun_expander_state = False
    if "ideb_escolas_expander_state" not in st.session_state:
        st.session_state.ideb_escolas_expander_state = False

    titulo_centralizado("Dashboard de Educação", 1)

    DEPENDENCIA = {
        "Total": "total",
        "Municipal": "municipal",
        "Estadual": "estadual",
        "Privada": "privada",
    }

    DEPENDENCIA_RENDIMENTO = {
        "Total": "total",
        "Pública": "publica",
        "Municipal": "municipal",
        "Estadual": "estadual",
        "Privada": "privada",
    }

    DEPENDENCIA_IDEB = {
        "Pública": "publica",
        "Municipal": "municipal",
        "Estadual": "estadual",
    }

    DEPENDENCIA_ESCOLAS = {
        "Municipal": "municipal",
        "Estadual": "estadual",
    }

    CATEGORIA_IDEB = {"Anos Iniciais": "anos_iniciais", "Anos Finais": "anos_finais"}

    INDICADOR_MATRICULA = {
        "Creche": "mat_infantil_creche",
        "Taxa - Creche": "taxa_matricula_creche",
        "Educação Básica": "mat_basico",
        "Educação Infantil": "mat_infantil",
        "Ensino Fundamental": "mat_fundamental",
        "Ensino Médio": "mat_medio",
        "Ensino Profissional": "mat_profissional",
        "EJA (Educação de Jovens e Adultos)": "mat_eja",
    }

    INDICADOR_DOCENTES = {
        "Educação Básica": "docentes_basico",
        "Educação Infantil": "docentes_infantil",
        "Ensino Fundamental": "docentes_fundamental",
        "Ensino Médio": "docentes_medio",
        "Ensino Profissional": "docentes_profissional",
        "EJA (Educação de Jovens e Adultos)": "docentes_eja",
    }

    INDICADOR_TURMAS = {
        "Educação Básica": "turmas_basico",
        "Educação Infantil": "turmas_infantil",
        "Ensino Fundamental": "turmas_fundamental",
        "Ensino Médio": "turmas_medio",
        "Ensino Profissional": "turmas_profissional",
        "EJA (Educação de Jovens e Adultos)": "turmas_eja",
    }

    INDICADOR_BASE_RENDIMENTO = {
        "Taxa de Aprovação": "taxa_aprovacao",
        "Taxa de Reprovação": "taxa_reprovacao",
        "Taxa de Abandono": "taxa_abandono",
        "Taxa de Distorção Idade-Série": "taxa_distorcao",
    }

    NIVEL_ENSINO_RENDIMENTO = {
        "Ensino Fundamental": "fundamental",
        "Anos Iniciais do Ens. Fundamental": "fundamental_anos_iniciais",
        "Anos Finais do Ens. Fundamental": "fundamental_anos_finais",
    }

    INDICADOR_ESCOLAS = {"Número de Escolas": "qntd_escolas"}

    INDICADOR_IDEB = {
        "Nota SAEB Português": "nota_port",
        "Nota SAEB Matemática": "nota_mat",
        "IDEB": "ideb",
    }

    titulo_centralizado("Clique nos menus abaixo para explorar os dados", 5)
    st.markdown("###### Indicadores do Censo Escolar")

    # CHAMADAS COM CALLBACKS

    # 1. Escolas
    display_educacao(
        df_filtrado=df_matriculas,
        titulo_expander="Escolas",
        municipios_selecionados=municipios_selecionados_global,
        dicionario_dependencia=DEPENDENCIA,
        dicionario_indicadores=INDICADOR_ESCOLAS,
        key_prefix="escolas",
        label_y="Número de Escolas",
        hover_label_format=",.0f",
        data_label_format=",.0f",
        expander_state_key="escolas_expander_state",
        callback_func=escolas_callback,
    )

    # 2. Matrículas
    display_educacao(
        df_filtrado=df_matriculas,
        titulo_expander="Matrículas",
        municipios_selecionados=municipios_selecionados_global,
        dicionario_dependencia=DEPENDENCIA,
        dicionario_indicadores=INDICADOR_MATRICULA,
        key_prefix="matriculas",
        label_y="Número de Matrículas",
        hover_label_format=",.0f",
        data_label_format=",.0f",
        expander_state_key="matriculas_expander_state",
        callback_func=matriculas_callback,
    )

    # 3. Docentes
    display_educacao(
        df_filtrado=df_matriculas,
        titulo_expander="Docentes",
        municipios_selecionados=municipios_selecionados_global,
        dicionario_dependencia=DEPENDENCIA,
        dicionario_indicadores=INDICADOR_DOCENTES,
        key_prefix="docentes",
        label_y="Número de Docentes",
        hover_label_format=",.0f",
        data_label_format=",.0f",
        expander_state_key="docentes_expander_state",
        callback_func=docentes_callback,
    )

    # 4. Turmas
    display_educacao(
        df_filtrado=df_matriculas,
        titulo_expander="Turmas",
        municipios_selecionados=municipios_selecionados_global,
        dicionario_dependencia=DEPENDENCIA,
        dicionario_indicadores=INDICADOR_TURMAS,
        key_prefix="turmas",
        label_y="Número de Turmas",
        hover_label_format=",.0f",
        data_label_format=",.0f",
        expander_state_key="turmas_expander_state",
        callback_func=turmas_callback,
    )

    st.markdown("###### Taxas de Rendimento Escolar")

    # 5. Taxas de Rendimento
    display_taxa_rendimento(
        df_filtrado=df_rendimento,
        titulo_expander="Taxas de Rendimento",
        municipios_selecionados=municipios_selecionados_global,
        dicionario_dependencia=DEPENDENCIA_RENDIMENTO,
        dicionario_indicador_base=INDICADOR_BASE_RENDIMENTO,
        dicionario_nivel_ensino=NIVEL_ENSINO_RENDIMENTO,
        key_prefix="rendimento",
        label_y="Taxa (%)",
        hover_label_format=",.1f",
        data_label_format=",.1f",
        expander_state_key="rendimento_expander_state",
        callback_func=rendimento_callback,
    )

    st.markdown(
        "###### Índice de Desenvolvimento da Educação Básica (IDEB) e Notas do SAEB"
    )

    # 6. IDEB - Municípios
    display_ideb_mun(
        df_filtrado=df_ideb_municipio,
        titulo_expander="IDEB - Municípios",
        municipios_selecionados=municipios_selecionados_global,
        dicionario_dependencia=DEPENDENCIA_IDEB,
        dicionario_indicadores=INDICADOR_IDEB,
        dicionario_categoria=CATEGORIA_IDEB,
        key_prefix="ideb",
        expander_state_key="ideb_mun_expander_state",
        callback_func=ideb_mun_callback,
    )

    # 7. IDEB - Escolas
    display_ideb_escolas(
        df_filtrado=df_ideb_escolas,
        titulo_expander="IDEB - Escolas",
        dicionario_dependencia=DEPENDENCIA_ESCOLAS,
        dicionario_categoria=CATEGORIA_IDEB,
        key_prefix="ideb_escolas",
        expander_state_key="ideb_escolas_expander_state",
        callback_func=ideb_escolas_callback,
    )
