import numpy as np
import pandas as pd
import streamlit as st

# ==============================================================================
# IMPORTAÇÕES DE FUNÇÕES E DADOS
# ==============================================================================
from dashboard_core.utils import criar_grafico_barras, titulo_centralizado, BIMESTRE_MAP


CORES_MUNICIPIOS = {}


def set_financas_config(cores_municipios):
    """
    Configura valores específicos do município que antes eram importados
    do dashboard_core.config. Deve ser chamado pelo app.py antes de
    renderizar a página de financas.
    """
    global CORES_MUNICIPIOS
    CORES_MUNICIPIOS = cores_municipios or {}


# --- FUNÇÕES DE CALLBACK ---


def set_expander_open(key):
    """Define o estado de um expander específico como True (aberto)."""
    st.session_state[key] = True


def siconfi_callback():
    """Callback para manter o expander SICONFI aberto."""
    set_expander_open("siconfi_expander_state")


def indicadores_callback():
    """Callback para manter o expander Indicadores Financeiros aberto."""
    # Este callback será usado nos seletores internos da função display_indicadores_financeiros
    set_expander_open("indicadores_financeiros_expander_state")


# ==============================================================================
# FUNÇÕES DA PÁGINA DE FINANÇAS
# ==============================================================================
@st.cache_data
def preparar_dados_graficos_siconfi(df_filtrado, cod_conta, anos_visualizacao):
    """Prepara os DataFrames pivotados para as visualizações do SICONFI."""
    df_hist = pd.DataFrame()
    df_hist_var = pd.DataFrame()
    df_bim = pd.DataFrame()
    df_bim_var = pd.DataFrame()
    df_acum = pd.DataFrame()
    df_acum_var = pd.DataFrame()
    ult_ano, ult_bim = None, None

    if df_filtrado.empty:
        return (
            df_hist,
            df_hist_var,
            df_bim,
            df_bim_var,
            df_acum,
            df_acum_var,
            ult_ano,
            ult_bim,
        )

    # Filtrar pela conta
    df_conta = df_filtrado[df_filtrado["cod_conta"] == cod_conta].copy()

    if df_conta.empty:
        return (
            df_hist,
            df_hist_var,
            df_bim,
            df_bim_var,
            df_acum,
            df_acum_var,
            ult_ano,
            ult_bim,
        )

    # Converter valor para milhões
    df_conta["valor_milhoes"] = df_conta["valor"] / 1000000

    # Determinar último ano e bimestre
    df_range = df_conta[df_conta["ano"].isin(anos_visualizacao)]
    if df_range.empty:
        ult_ano = df_conta["ano"].max()
    else:
        ult_ano = df_range["ano"].max()

    ult_bim = df_conta[df_conta["ano"] == ult_ano]["bimestre"].max()

    # 1. EVOLUÇÃO BIMESTRAL (No Bimestre)
    df_no_bim = df_conta[df_conta["coluna"] == "No Bimestre (b)"].copy()

    if not df_no_bim.empty:
        # Criar índice combinado para evolução temporal
        # Mapear bimestre para nome legível
        df_no_bim["bimestre_nome"] = df_no_bim["bimestre"].map(BIMESTRE_MAP)
        df_no_bim["periodo"] = (
            df_no_bim["bimestre_nome"] + "/" + df_no_bim["ano"].astype(str).str[-2:]
        )

        # Criar coluna de ordenação (ano * 10 + bimestre)
        df_no_bim["ordem"] = df_no_bim["ano"] * 10 + df_no_bim["bimestre"]

        df_hist_full = df_no_bim.pivot_table(
            index="periodo",
            columns="municipio",
            values="valor_milhoes",
            aggfunc="sum",
            fill_value=0,
        )

        # Criar DataFrame auxiliar para ordenação
        ordem_map = df_no_bim.groupby("periodo")["ordem"].first().sort_values()
        df_hist_full = df_hist_full.reindex(ordem_map.index)

        # Calcular variação YoY para evolução
        # Agrupar por município e bimestre, calcular variação
        df_var_calc = df_no_bim.sort_values(["municipio", "bimestre", "ano"])
        df_var_calc["valor_ano_anterior"] = df_var_calc.groupby(
            ["municipio", "bimestre"]
        )["valor_milhoes"].shift(1)
        df_var_calc["variacao_yoy"] = np.where(
            (df_var_calc["valor_ano_anterior"].notna())
            & (df_var_calc["valor_ano_anterior"] != 0),
            (df_var_calc["valor_milhoes"] / df_var_calc["valor_ano_anterior"] - 1)
            * 100,
            np.nan,
        )

        df_hist_var_full = df_var_calc.pivot_table(
            index="periodo",
            columns="municipio",
            values="variacao_yoy",
            aggfunc="first",
            fill_value=0,
        )

        # Aplicar mesma ordenação
        df_hist_var_full = df_hist_var_full.reindex(ordem_map.index)

        # Filtrar por anos de visualização
        anos_str = tuple([str(ano)[-2:] for ano in anos_visualizacao])
        df_hist = df_hist_full[df_hist_full.index.str.endswith(anos_str)]
        df_hist_var = df_hist_var_full[df_hist_var_full.index.str.endswith(anos_str)]

    # 2. BIMESTRE (Comparar mesmo bimestre ao longo dos anos)
    df_bim_atual = df_no_bim[df_no_bim["bimestre"] == ult_bim]

    if not df_bim_atual.empty:
        df_bim_full = df_bim_atual.pivot_table(
            index="ano",
            columns="municipio",
            values="valor_milhoes",
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        # Adicionar informação do bimestre no índice
        bimestre_nome = BIMESTRE_MAP.get(ult_bim, f"{ult_bim}º Bim")
        df_bim_full.index = df_bim_full.index.astype(str) + f" ({bimestre_nome})"

        # Variação YoY
        df_bim_var_full = df_bim_full.pct_change() * 100

        # Filtrar anos (agora o índice tem o formato "2023 (Jan-Fev)")
        anos_str = [str(ano) for ano in anos_visualizacao]
        df_bim = df_bim_full[df_bim_full.index.str.startswith(tuple(anos_str))]
        df_bim_var = df_bim_var_full[
            df_bim_var_full.index.str.startswith(tuple(anos_str))
        ]

    # 3. ACUMULADO ATÉ O BIMESTRE
    df_acum_data = df_conta[df_conta["coluna"] == "Até o Bimestre (c)"]
    df_acum_bim = df_acum_data[df_acum_data["bimestre"] == ult_bim]

    if not df_acum_bim.empty:
        df_acum_full = df_acum_bim.pivot_table(
            index="ano",
            columns="municipio",
            values="valor_milhoes",
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        # Adicionar informação do bimestre no índice
        bimestre_nome = BIMESTRE_MAP.get(ult_bim, f"{ult_bim}º Bim")
        df_acum_full.index = df_acum_full.index.astype(str) + f" (até {bimestre_nome})"

        # Variação YoY
        df_acum_var_full = df_acum_full.pct_change() * 100

        # Filtrar anos (agora o índice tem o formato "2023 (até Jan-Fev)")
        anos_str = [str(ano) for ano in anos_visualizacao]
        df_acum = df_acum_full[df_acum_full.index.str.startswith(tuple(anos_str))]
        df_acum_var = df_acum_var_full[
            df_acum_var_full.index.str.startswith(tuple(anos_str))
        ]

    return (
        df_hist,
        df_hist_var,
        df_bim,
        df_bim_var,
        df_acum,
        df_acum_var,
        ult_ano,
        ult_bim,
    )


def display_siconfi_consolidado(df, expander_state_key, callback_func):
    """
    Exibe um expander consolidado para todos os indicadores do SICONFI
    com navegação por pills (Evolução Bimestral, Bimestre, Acumulado até o Bimestre).
    """
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

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

    with st.expander(
        "Indicadores Bimestrais da Execução Orçamentária",
        expanded=st.session_state[expander_state_key],
    ):
        # --- 1. SELETOR DE CONTA ---
        indicador_siconfi_selecionado = st.selectbox(
            "Selecione a Conta:",
            options=list(CONTAS_SICONFI.keys()),
            key="siconfi_selectbox_conta",
            on_change=callback_func,
        )

        cod_conta = CONTAS_SICONFI[indicador_siconfi_selecionado]

        # --- 2. NAVEGAÇÃO ENTRE "ABAS" (CONTROLADA POR ESTADO) ---
        key_main_tab = "main_tab_nav_siconfi"
        if key_main_tab not in st.session_state:
            st.session_state[key_main_tab] = "Evolução Bimestral"

        aba_selecionada = st.pills(
            "Selecione o tipo de análise temporal:",
            options=["Evolução Bimestral", "Bimestre", "Acumulado até o Bimestre"],
            selection_mode="single",
            key=key_main_tab,
        )

        # Fallback caso o usuário desmarque
        if not aba_selecionada:
            aba_selecionada = "Evolução Bimestral"

        # --- ABA 1: EVOLUÇÃO BIMESTRAL ---
        if aba_selecionada == "Evolução Bimestral":
            # Slider de anos DENTRO da aba de Evolução
            col_slider, _ = st.columns([0.7, 0.3])
            with col_slider:
                anos_selecionados_slider = st.slider(
                    "Selecione o intervalo de anos:",
                    min_value=min_ano_valido,
                    max_value=max_ano_valido,
                    value=(default_start, default_end),
                    key="siconfi_slider_anos",
                )

            start_ano_slider, end_ano_slider = anos_selecionados_slider
            anos_para_visualizar = list(range(start_ano_slider, end_ano_slider + 1))

            # Incluir ano anterior para cálculo de variação
            ano_anterior_inicio = start_ano_slider - 1
            anos_para_dados = list(range(ano_anterior_inicio, end_ano_slider + 1))
            df_filtrado_anos = df[df["ano"].isin(anos_para_dados)]

            # Preparação dos dados
            (
                hist_abs,
                hist_var,
                _,
                _,
                _,
                _,
                ult_ano,
                ult_bim,
            ) = preparar_dados_graficos_siconfi(
                df_filtrado_anos, cod_conta, anos_para_visualizar
            )

            # Chave para o segmented_control
            key_hist = "hist_mode_siconfi"

            modo_hist = st.segmented_control(
                "Visualizar:",
                options=["Valor (Milhões R$)", "Variação (%)"],
                key=key_hist,
                selection_mode="single",
                on_change=callback_func,
                default="Valor (Milhões R$)",
            )

            # Fallback: se desmarcar (None), força o padrão
            if not modo_hist:
                modo_hist = "Valor (Milhões R$)"

            if modo_hist == "Valor (Milhões R$)":
                df_plot = hist_abs
                titulo_grafico = f"{indicador_siconfi_selecionado} - Evolução Bimestral"
                label_y = "Milhões R$"
                data_label_format = ",.1f"
                hover_label_format = ",.2f"
            else:
                df_plot = hist_var
                titulo_grafico = f"{indicador_siconfi_selecionado} - Evolução Bimestral - Variação (%)"
                label_y = "Variação (%) em relação ao mesmo período do ano anterior"
                data_label_format = "+,.1f"
                hover_label_format = "+,.2f"

            titulo_centralizado(titulo_grafico, 5)

            if not df_plot.empty:
                fig = criar_grafico_barras(
                    df=df_plot,
                    titulo="",
                    label_y=label_y,
                    barmode="group",
                    height=400,
                    data_label_format=data_label_format,
                    hover_label_format=hover_label_format,
                    color_map=CORES_MUNICIPIOS,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Não há dados disponíveis para o período selecionado.")

        # --- ABA 2: BIMESTRE ---
        elif aba_selecionada == "Bimestre":
            # Preparar dados com TODOS os anos disponíveis (sem filtro)
            anos_para_visualizar_bim = anos_validos_selecao
            ano_anterior_inicio_bim = min(anos_validos_selecao) - 1
            anos_para_dados_bim = [ano_anterior_inicio_bim] + list(
                anos_para_visualizar_bim
            )
            df_filtrado_anos_bim = df[df["ano"].isin(anos_para_dados_bim)]

            (
                _,
                _,
                bim_abs,
                bim_var,
                _,
                _,
                ult_ano,
                ult_bim,
            ) = preparar_dados_graficos_siconfi(
                df_filtrado_anos_bim, cod_conta, anos_para_visualizar_bim
            )

            if ult_bim:
                # Chave para o segmented_control
                key_bim = "bim_mode_siconfi"

                modo_bim = st.segmented_control(
                    "Visualizar:",
                    options=["Valor (Milhões R$)", "Variação (%)"],
                    key=key_bim,
                    selection_mode="single",
                    on_change=callback_func,
                    default="Valor (Milhões R$)",
                )

                if not modo_bim:
                    modo_bim = "Valor (Milhões R$)"

                bimestre_txt = BIMESTRE_MAP.get(ult_bim, f"{ult_bim}º Bim")

                if modo_bim == "Variação (%)":
                    df_plot = bim_var.sort_index(ascending=True)
                    titulo_grafico = f"{indicador_siconfi_selecionado} no Bimestre de {bimestre_txt} - Variação (%)"
                    label_y = "Variação (%) em relação ao mesmo período do ano anterior"
                    data_label_format = "+,.1f"
                    hover_label_format = "+,.2f"

                    titulo_centralizado(titulo_grafico, 5)

                    if not df_plot.empty:
                        fig = criar_grafico_barras(
                            df=df_plot,
                            titulo="",
                            label_y=label_y,
                            barmode="group",
                            height=400,
                            data_label_format=data_label_format,
                            hover_label_format=hover_label_format,
                            color_map=CORES_MUNICIPIOS,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Não há dados de variação disponíveis.")

                else:  # Valor (Milhões R$)
                    df_plot = bim_abs.sort_index(ascending=True)
                    titulo_grafico = (
                        f"{indicador_siconfi_selecionado} no Bimestre de {bimestre_txt}"
                    )

                    titulo_centralizado(titulo_grafico, 5)

                    if not df_plot.empty:
                        fig_abs = criar_grafico_barras(
                            df=df_plot,
                            titulo="",
                            label_y="Milhões R$",
                            barmode="group",
                            height=400,
                            data_label_format=",.1f",
                            hover_label_format=",.2f",
                            color_map=CORES_MUNICIPIOS,
                        )
                        st.plotly_chart(fig_abs, use_container_width=True)
                    else:
                        st.info("Sem dados disponíveis.")
            else:
                st.warning("Não há dados de bimestre disponíveis.")

        # --- ABA 3: ACUMULADO ATÉ O BIMESTRE ---
        elif aba_selecionada == "Acumulado até o Bimestre":
            # Preparar dados com TODOS os anos disponíveis (sem filtro)
            anos_para_visualizar_acum = anos_validos_selecao
            ano_anterior_inicio_acum = min(anos_validos_selecao) - 1
            anos_para_dados_acum = [ano_anterior_inicio_acum] + list(
                anos_para_visualizar_acum
            )
            df_filtrado_anos_acum = df[df["ano"].isin(anos_para_dados_acum)]

            (
                _,
                _,
                _,
                _,
                acum_abs,
                acum_var,
                ult_ano,
                ult_bim,
            ) = preparar_dados_graficos_siconfi(
                df_filtrado_anos_acum, cod_conta, anos_para_visualizar_acum
            )

            if ult_bim:
                # Chave para o segmented_control
                key_acum = "acum_mode_siconfi"

                modo_acum = st.segmented_control(
                    "Visualizar:",
                    options=["Valor (Milhões R$)", "Variação (%)"],
                    key=key_acum,
                    selection_mode="single",
                    on_change=callback_func,
                    default="Valor (Milhões R$)",
                )

                if not modo_acum:
                    modo_acum = "Valor (Milhões R$)"

                bimestre_txt = BIMESTRE_MAP.get(ult_bim, f"{ult_bim}º Bim")

                if modo_acum == "Variação (%)":
                    df_plot = acum_var.sort_index(ascending=True)
                    titulo_grafico = f"{indicador_siconfi_selecionado} no Acumulado até o Bimestre de {bimestre_txt} - Variação (%)"
                    label_y = "Variação (%) em relação ao mesmo período do ano anterior"
                    data_label_format = "+,.1f"
                    hover_label_format = "+,.2f"

                    titulo_centralizado(titulo_grafico, 5)

                    if not df_plot.empty:
                        fig = criar_grafico_barras(
                            df=df_plot,
                            titulo="",
                            label_y=label_y,
                            barmode="group",
                            height=400,
                            data_label_format=data_label_format,
                            hover_label_format=hover_label_format,
                            color_map=CORES_MUNICIPIOS,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Não há dados de variação disponíveis.")

                else:  # Valor (Milhões R$)
                    df_plot = acum_abs.sort_index(ascending=True)
                    titulo_grafico = f"{indicador_siconfi_selecionado} no Acumulado até o Bimestre de {bimestre_txt}"

                    titulo_centralizado(titulo_grafico, 5)

                    st.markdown("**Valores Absolutos (Milhões R$)**")
                    if not df_plot.empty:
                        fig_abs = criar_grafico_barras(
                            df=df_plot,
                            titulo="",
                            label_y="Milhões R$",
                            barmode="group",
                            height=400,
                            data_label_format=",.1f",
                            hover_label_format=",.2f",
                            color_map=CORES_MUNICIPIOS,
                        )
                        st.plotly_chart(fig_abs, use_container_width=True)
                    else:
                        st.info("Sem dados disponíveis.")
            else:
                st.warning("Não há dados de acumulado disponíveis.")


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
    expander_state_key,
    callback_func,
):
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = False

    with st.expander(
        f"{titulo_expander}", expanded=st.session_state[expander_state_key]
    ):
        indicador_selecionado = st.selectbox(
            "Selecione um Indicador Financeiro:",
            options=list(dicionario_indicadores.keys()),
            key=f"{key_prefix}_selectbox_indicadores",
            on_change=callback_func,
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
        st.plotly_chart(fig, use_container_width=True)
        titulo_centralizado(
            "Download do relatório metodológico que detalha a construção dos indicadores fiscais dos municípios",
            6,
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

    # 1. INICIALIZAÇÃO DOS ESTADOS DOS EXPANDERS (Fechados por padrão)
    if "siconfi_expander_state" not in st.session_state:
        st.session_state.siconfi_expander_state = False
    if "indicadores_financeiros_expander_state" not in st.session_state:
        st.session_state.indicadores_financeiros_expander_state = False

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

    # 2. CHAMADAS AOS EXPANDERS COM ESTADO E CALLBACK

    display_indicadores_financeiros(
        df_filtrado=df_indicadores_financeiros,
        titulo_expander="Indicadores Financeiros",
        dicionario_indicadores=INDICADORES_FINANCEIROS,
        key_prefix="indicadores_financeiros",
        label_y="Percentual (%)",
        hover_label_format=",.2f",
        data_label_format=",.1f",
        pdf_data=pdf_indicadores,
        expander_state_key="indicadores_financeiros_expander_state",
        callback_func=indicadores_callback,
    )

    display_siconfi_consolidado(
        df=df_financas,
        expander_state_key="siconfi_expander_state",
        callback_func=siconfi_callback,
    )
