from importlib import resources
from pathlib import Path
import plotly.express as px
import streamlit as st
import pandas as pd
import numpy as np
import io


# --- DICIONÁRIOS E CONSTANTES ---

# Dicionário para tradução de meses
MESES_DIC = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

BIMESTRE_DIC = {
    1: "Fevereiro",
    2: "Abril",
    3: "Junho",
    4: "Agosto",
    5: "Outubro",
    6: "Dezembro",
}

BIMESTRE_MAP = {
    1: "Jan-Fev",
    2: "Mar-Abr",
    3: "Mai-Jun",
    4: "Jul-Ago",
    5: "Set-Out",
    6: "Nov-Dez",
}


def manter_posicao_scroll():
    """
    Esta função injeta JavaScript para salvar a posição do scroll no sessionStorage
    do navegador e restaurá-la após a re-execução do script pelo Streamlit.
    """
    # O JavaScript para salvar e restaurar a posição do scroll.
    # A função debounce evita que o evento de scroll seja disparado muitas vezes,
    # o que poderia causar problemas de performance.
    js_code = """
    <script>
        const scrollKey = "streamlit-scroll-position";

        function debounce(func, wait) {
            let timeout;
            return function(...args) {
                clearTimeout(timeout);
                timeout = setTimeout(() => func.apply(this, args), wait);
            };
        }

        const saveScrollPosition = debounce(() => {
            sessionStorage.setItem(scrollKey, window.scrollY);
        }, 100);

        window.addEventListener("scroll", saveScrollPosition);

        window.addEventListener("DOMContentLoaded", () => {
            const scrollY = sessionStorage.getItem(scrollKey);
            if (scrollY) {
                window.scrollTo(0, parseInt(scrollY, 10));
            }
        });
    </script>
    """
    # Usa st.components.v1.html para injetar o script na página
    st.components.v1.html(js_code, height=0)


# -- FUNCOES DE VISUALIZACAO ---
def carregar_css(caminho_arquivo: str = "assets/style.css"):
    """
    Carrega um arquivo CSS.
    - Primeiro tenta encontrar dentro do pacote `dashboard_core` (via importlib.resources)
    - Se não encontrar, tenta o caminho local (útil para desenvolvimento).
    """
    css_text = None

    # 1) tenta dentro do pacote dashboard_core
    try:
        pkg_files = resources.files("dashboard_core")
        css_res = pkg_files.joinpath(caminho_arquivo)
        if css_res.exists():
            css_text = css_res.read_text(encoding="utf-8")
    except Exception:
        css_text = None

    # 2) fallback: tenta caminho local relativo (ex: ./assets/style.css)
    if not css_text:
        local_path = Path(caminho_arquivo)
        if local_path.exists():
            css_text = local_path.read_text(encoding="utf-8")

    # 3) aplica o CSS ou mostra aviso discreto
    if css_text:
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ Arquivo CSS não encontrado: {caminho_arquivo}")


def titulo_centralizado(texto: str, level: int, cor: str = None):
    """
    Cria um título Markdown centralizado com um nível de heading específico (h1, h2, ...).

    Args:
        texto (str): O texto do título.
        level (int): O nível do heading (1 para <h1>, 2 para <h2>, etc.).
        cor (str, optional): A cor do texto (ex: 'gray', '#FF4B4B'). Defaults to None.
    """
    style = "text-align: center;"
    if cor:
        style += f" color: {cor};"

    st.markdown(f"<h{level} style='{style}'>{texto}</h{level}>", unsafe_allow_html=True)


def checar_ult_ano_completo(df):
    """
    Verifica se o último ano no DataFrame está completo (ou seja, se contém dados até dezembro).
    Se não estiver completo, retorna o ano anterior.

    Args:
        df (pd.DataFrame): DataFrame contendo uma coluna 'ano'.

    Returns:
        int: O último ano completo.
    """
    ult_ano = df["ano"].max()
    meses_no_ult_ano = df[df["ano"] == ult_ano]["mes"].nunique()
    if meses_no_ult_ano < 12:
        return ult_ano - 1
    return ult_ano


def filtrar_municipio_ult_mes_ano(df, municipio):
    """
    Filtra o DataFrame para manter apenas os dados do último mês do último ano disponível.

    Args:
        df (pd.DataFrame): DataFrame contendo colunas 'ano' e 'mes'.

    Returns:
        pd.DataFrame: DataFrame filtrado com dados do último mês do último ano.
    """
    ult_ano = df["ano"].max()
    ult_mes = df[df["ano"] == ult_ano]["mes"].max()
    return df[
        (df["municipio"] == municipio) & (df["ano"] == ult_ano) & (df["mes"] == ult_mes)
    ]


@st.cache_data
def calcular_yoy(df, municipio, ultimo_mes, ultimo_ano, coluna, round):
    """
    Calcula a variação ano-a-ano (YoY) para um indicador específico,
    filtrando por município, mês e ano.
    """
    # Filtra o DF para o MUNICÍPIO e o MÊS de interesse
    df_filtrado = df[
        (df["municipio"] == municipio) & (df["mes"] == ultimo_mes)
    ].sort_values(by="ano")

    # Cria a coluna "ano_anterior" usando shift()
    df_filtrado[f"{coluna}_ano_anterior"] = df_filtrado[f"{coluna}"].shift(1)

    # Filtra apenas a linha do último ano
    dados_recentes = df_filtrado[df_filtrado["ano"] == ultimo_ano]

    # Verifica se temos a linha do ult ano e se ela tem um valor
    if not dados_recentes.empty:
        valor_atual = dados_recentes[f"{coluna}"].iloc[0]
        valor_anterior = dados_recentes[f"{coluna}_ano_anterior"].iloc[0]

        # 4. Calcula a variação percentual
        if pd.notna(valor_anterior) and valor_anterior > 0:
            variacao = ((valor_atual / valor_anterior) - 1) * 100
            return variacao.round(round)

    return None


def criar_grafico_barras(
    df,
    titulo,
    label_y,
    barmode="group",
    height=400,
    data_label_format=",.2f",
    hover_label_format=",.2f",
    color_map=None,
):
    """
    Cria um gráfico de barras customizado e reutilizável com Plotly Express.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" - ".join(map(str, col)).strip() for col in df.columns.values]

    index_name = df.index.name if df.index.name is not None else "index"
    df_reset = df.reset_index()
    index_name = df_reset.columns[0]

    df_long = df_reset.melt(id_vars=index_name, var_name="series", value_name="value")

    df_long["hover_value_formatted"] = df_long["value"].apply(
        lambda x: f"{x:{hover_label_format}}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    df_long["data_label_formatted"] = df_long["value"].apply(
        lambda x: f"{x:{data_label_format}}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    fig = px.bar(
        df_long,
        x=index_name,
        y="value",
        color="series",
        labels={"value": label_y, index_name: "", "series": ""},
        barmode=barmode,
        height=height,
        custom_data=["hover_value_formatted", "data_label_formatted"],
        color_discrete_map=color_map,
    )

    xaxis_config = {}
    if pd.api.types.is_numeric_dtype(df.index):
        xaxis_config = dict(tickmode="linear", dtick=1)

    fig.update_layout(
        margin=dict(t=50),
        title_text=titulo,
        title_font_size=20,
        xaxis_title="",
        xaxis=xaxis_config,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.1,
            xanchor="left",
            x=0,
            title="",
            font=dict(size=15),
        ),
    )

    fig.update_traces(
        texttemplate="%{customdata[1]}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            f"<b>{index_name.title()}</b>: %{{x}}<br>"
            "<b>Valor</b>: %{customdata[0]}"
            "<extra></extra>"
        ),
    )

    return fig


def criar_grafico_linhas(
    df,
    titulo,
    label_y,
    height=500,
    data_label_format=",.2f",
    hover_label_format=",.2f",
    color_map=None,
    reverse_y: bool = False,  # <-- MUDANÇA 1: Novo parâmetro
):
    """
    Cria um gráfico de linhas customizado e reutilizável com Plotly Express.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" - ".join(map(str, col)).strip() for col in df.columns.values]

    index_name = df.index.name if df.index.name is not None else "index"
    df_reset = df.reset_index()
    index_name = df_reset.columns[0]

    df_long = df_reset.melt(id_vars=index_name, var_name="series", value_name="value")

    df_long["hover_value_formatted"] = df_long["value"].apply(
        lambda x: f"{x:{hover_label_format}}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )
    df_long["data_label_formatted"] = df_long["value"].apply(
        lambda x: f"{x:{data_label_format}}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    fig = px.line(
        df_long,
        x=index_name,
        y="value",
        color="series",
        text=df_long["data_label_formatted"],
        labels={"value": label_y, index_name: "", "series": ""},
        height=height,
        custom_data=["hover_value_formatted", "data_label_formatted"],
        color_discrete_map=color_map,
        markers=True,
    )

    xaxis_config = {"type": "category"}

    yaxis_config = {}
    if reverse_y:
        yaxis_config["autorange"] = "reversed"

    fig.update_layout(
        margin=dict(t=50),
        title_text=titulo,
        title_font_size=20,
        xaxis_title="",
        xaxis=xaxis_config,
        yaxis=yaxis_config,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="left",
            x=0,
            title="",
            font=dict(size=15),
        ),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )

    fig.update_traces(
        texttemplate="%{text}",
        textposition="top center",
        textfont=dict(size=10, color="white"),
        hovertemplate=(
            "<b>%{fullData.name}</b><br>"
            f"<b>{index_name.title()}</b>: %{{x}}<br>"
            "<b>Valor</b>: %{customdata[0]}"
            "<extra></extra>"
        ),
    )

    return fig


@st.cache_data
def criar_tabela_formatada(df, index_col, ult_ano, ult_mes, coluna_agregacao):
    """Cria uma tabela formatada para exibição no Streamlit."""
    df_filtrado = df[df["mes"] <= ult_mes]
    df_pivot = df_filtrado.pivot_table(
        index=index_col,
        columns="ano",
        values=coluna_agregacao,
        aggfunc="sum",
        fill_value=0,
    ).sort_values(by=ult_ano, ascending=False)

    df_pivot.columns = (
        f"Jan-{MESES_DIC[ult_mes][:3]}"
        + "/"
        + df_pivot.columns.astype(str).str.slice(-2)
    )
    df_pivot.index.name = index_col.replace("_", " ").title()

    return df_pivot


@st.cache_data
def criar_tabela_formatada_mes(df, index_col, ult_ano, ult_mes, coluna_agregacao):
    """Cria uma tabela formatada para exibição no Streamlit."""
    df_filtrado = df[df["mes"] == ult_mes]
    df_pivot = df_filtrado.pivot_table(
        index=index_col,
        columns="ano",
        values=coluna_agregacao,
        aggfunc="sum",
        fill_value=0,
    ).sort_values(by=ult_ano, ascending=False)

    df_pivot.columns = (
        f"{MESES_DIC[ult_mes][:3]}" + "/" + df_pivot.columns.astype(str).str.slice(-2)
    )
    df_pivot.index.name = index_col.replace("_", " ").title()

    return df_pivot


@st.cache_data
def criar_tabela_formatada_ano(df, index_col, coluna_agregacao):
    """Cria uma tabela formatada para exibição no Streamlit."""
    ult_ano = checar_ult_ano_completo(df)
    df_filtrado = df[df["ano"] <= ult_ano]
    df_pivot = df_filtrado.pivot_table(
        index=index_col,
        columns="ano",
        values=coluna_agregacao,
        aggfunc="sum",
        fill_value=0,
    ).sort_values(by=ult_ano, ascending=False)

    df_pivot.index.name = index_col.replace("_", " ").title()

    return df_pivot


@st.cache_data
def criar_tabela_formatada_ano_estoque(df, index_col, coluna_agregacao):
    """Cria uma tabela formatada para exibição no Streamlit."""
    ult_ano = checar_ult_ano_completo(df)
    df_filtrado = df[df["ano"] <= ult_ano]
    df_filtrado = df_filtrado.query("mes == 12")
    df_pivot = df_filtrado.pivot_table(
        index=index_col,
        columns="ano",
        values=coluna_agregacao,
        aggfunc="sum",
        fill_value=0,
    ).sort_values(by=ult_ano, ascending=False)

    df_pivot.index.name = index_col.replace("_", " ").title()

    return df_pivot


def destacar_percentuais(val):
    if pd.isna(val) or val == 0:
        return ""
    color = "green" if val > 0 else "red"
    return f"color: {color}"


@st.cache_data
def criar_tabela_comex(df, colunas_agg, colunas_finais, anos_selecionados):
    """
    Cria uma tabela de dados de comércio exterior, agrupando por uma ou mais colunas.

    Args:
        df (pd.DataFrame): O DataFrame de entrada.
        colunas_agg (list): Lista de nomes de colunas para agrupar (ex: ["pais", "desc_sh4"]).
        colunas_finais (list): Lista de nomes para as colunas agrupadas no resultado final (ex: ["País", "Produto"]).
        anos_selecionados (list): Lista de anos para filtrar no .query().
    """

    df_sorted = df.sort_values(by=["ano", "mes"])

    df_agregado = df_sorted.groupby(["ano", "mes"] + colunas_agg, as_index=False).agg(
        {
            "valor_exp_mensal": "sum",
            "valor_exp_mensal_ano_anterior": "sum",
        }
    )

    grouping_cols = ["ano"] + colunas_agg
    df_agregado["valor_acumulado_ano"] = df_agregado.groupby(grouping_cols)[
        "valor_exp_mensal"
    ].cumsum()
    df_agregado["valor_acumulado_ano_anterior"] = df_agregado.groupby(grouping_cols)[
        "valor_exp_mensal_ano_anterior"
    ].cumsum()

    colunas_resultado = (
        ["Ano", "Mês"]
        + colunas_finais
        + [
            "Valor Exportado no Mês (US$)",
            "Variação Mês (vs Ano Ant.) (%)",
            "Valor Acumulado no Ano (US$)",
            "Variação Acum. (vs Ano Ant.) (%)",
        ]
    )

    colunas_originais = (
        ["ano", "mes"]
        + colunas_agg
        + [
            "valor_exp_mensal",
            "yoy_mensal",
            "valor_acumulado_ano",
            "yoy_acumulado",
        ]
    )
    return (
        df_agregado.assign(
            yoy_mensal=lambda x: (
                (x["valor_exp_mensal"] / x["valor_exp_mensal_ano_anterior"]) - 1
            )
            * 100,
            yoy_acumulado=lambda x: (
                (x["valor_acumulado_ano"] / x["valor_acumulado_ano_anterior"]) - 1
            )
            * 100,
        )
        .sort_values(
            by=["ano", "mes", "valor_exp_mensal"], ascending=[False, False, False]
        )
        .query("ano in @anos_selecionados")
        .replace([np.inf, -np.inf], np.nan)[colunas_originais]
        .set_axis(colunas_resultado, axis=1)
    )


def formatador_pt_br(valor):
    """Formata um número para o padrão brasileiro (ex: 1.234,56)."""
    try:
        # Especificador de formato para duas casas decimais com separador de milhar
        formato_spec = ",.1f"
        s = f"{float(valor):{formato_spec}}"
        # Inverte os separadores para o padrão brasileiro
        return s.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    except (ValueError, TypeError):
        return valor  # Retorna o valor original se não for numérico


def criar_formatador_final(tipo, formatador_base):
    """
    Cria a função de formatação final, adicionando o prefixo 'R$'
    quando necessário.
    """
    if tipo == "Remuneração Nominal (R$)":
        # Define uma função aninhada para o formato com prefixo
        def formatador_nominal(x):
            return f"R$ {formatador_base(x)}"

        return formatador_nominal
    else:
        # Retorna a função base se não precisar de prefixo
        return formatador_base


@st.cache_data
def preparar_dados_graficos_anuais(df_filtrado, coluna_agregacao, coluna_valores):
    df = df_filtrado.pivot_table(
        index="ano",
        columns=coluna_agregacao,
        values=coluna_valores,
        aggfunc="sum",
        fill_value=0,
    ).sort_index()
    return df


# ... (outras funções do seu utils.py) ...
@st.cache_data
def to_excel(df: pd.DataFrame) -> bytes:
    """
    Converte um DataFrame do Pandas para um arquivo Excel em memória (bytes).

    Args:
        df (pd.DataFrame): O DataFrame a ser convertido.

    Returns:
        bytes: Os dados do arquivo Excel em bytes.
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dados")

    # Pega o valor dos bytes do buffer de memória
    processed_data = output.getvalue()
    return processed_data
