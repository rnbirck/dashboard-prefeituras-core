import pandas as pd
import streamlit as st
import plotly.express as px

from dashboard_core.utils import (
    titulo_centralizado,
)

# --- CONFIGURAÇÕES GLOBAIS ---
municipio_de_interesse = None
CORES_MUNICIPIOS = {}
anos_de_interesse = []

CORES_VINCULOS = {
    "Estatutários": "#1f77b4",  # Azul
    "Celetistas": "#ff7f0e",  # Laranja
    "Comissionados": "#2ca02c",  # Verde
    "Estagiários": "#9467bd",  # Roxo
    "Sem Vínculo Permanente": "#d62728",  # Vermelho
    "Outros": "#7f7f7f",  # Cinza
}

ORDEM_VINCULOS = [
    "Estatutários",
    "Celetistas",
    "Comissionados",
    "Sem Vínculo Permanente",
    "Estagiários",
]


def set_adm_publica_config(municipio, cores_municipios, anos_interesse):
    """
    Configura valores específicos do município e do dashboard.
    Deve ser chamado pelo app.py antes de renderizar a página.
    """
    global municipio_de_interesse, CORES_MUNICIPIOS, anos_de_interesse
    municipio_de_interesse = municipio
    CORES_MUNICIPIOS = cores_municipios or {}
    anos_de_interesse = anos_interesse or []


# --- FUNÇÕES DE CALLBACK ---


def set_expander_open(key):
    """Define o estado de um expander específico como True (aberto)."""
    st.session_state[key] = True


def adm_vinculos_callback():
    set_expander_open("adm_vinculos_expander_state")


# --- PREPARAÇÃO DE DADOS ---


@st.cache_data
def preparar_dados_adm_stacked(df, tipo_adm):
    """
    Transforma as colunas wide do CSV em formato long para gráfico empilhado.
    Trata: Direta, Indireta e Total (soma das duas).
    """
    if df.empty:
        return pd.DataFrame()

    # Filtrar Municípios
    df_filt = df.copy()

    if df_filt.empty:
        return pd.DataFrame()

    categorias = [
        "estatutarios",
        "celetistas",
        "comissionados",
        "estagiarios",
        "sem_vinculo_permanente",
    ]
    labels_map = {
        "estatutarios": "Estatutários",
        "celetistas": "Celetistas",
        "comissionados": "Comissionados",
        "estagiarios": "Estagiários",
        "sem_vinculo_permanente": "Sem Vínculo Permanente",
    }

    df_long = pd.DataFrame()

    if tipo_adm == "Total (Direta + Indireta)":
        df_calc = df_filt[["ano", "municipio"]].copy()

        for cat in categorias:
            col_direto = f"{cat}_direto"
            col_indireta = f"{cat}_indireta"

            # Garante que as colunas existem (preenche com 0 se não existirem)
            val_direto = df_filt[col_direto] if col_direto in df_filt.columns else 0
            val_indireta = (
                df_filt[col_indireta] if col_indireta in df_filt.columns else 0
            )

            df_calc[labels_map[cat]] = val_direto + val_indireta

        df_long = df_calc.melt(
            id_vars=["ano", "municipio"],
            value_vars=list(labels_map.values()),
            var_name="vinculo",
            value_name="quantidade",
        )

    else:
        # Define sufixo
        sufixo = "_direto" if tipo_adm == "Administração Direta" else "_indireta"

        # Cria dicionário de renomeação
        cols_rename = {f"{cat}{sufixo}": labels_map[cat] for cat in categorias}

        cols_presentes = [c for c in cols_rename.keys() if c in df_filt.columns]

        df_long = df_filt.melt(
            id_vars=["ano", "municipio"],
            value_vars=cols_presentes,
            var_name="coluna_origem",
            value_name="quantidade",
        )

        # Mapeia o nome da coluna para o nome do vínculo
        df_long["vinculo"] = df_long["coluna_origem"].map(cols_rename)
        df_long = df_long.drop(columns=["coluna_origem"])

    # Ordenação categórica para o gráfico
    df_long["vinculo"] = pd.Categorical(
        df_long["vinculo"], categories=ORDEM_VINCULOS, ordered=True
    )

    return df_long.sort_values(["municipio", "ano", "vinculo"])


# --- DISPLAY E VISUALIZAÇÃO ---


def display_adm_publica_expander(df, expander_state_key, callback_func):
    if expander_state_key not in st.session_state:
        st.session_state[expander_state_key] = True

    with st.expander(
        "Vínculos Empregatícios na Administração Pública",
        expanded=st.session_state[expander_state_key],
    ):
        titulo_centralizado("Quantidade de Servidores por Tipo de Vínculo", 5)

        key_tipo = "adm_tipo_selecao"
        if key_tipo not in st.session_state:
            st.session_state[key_tipo] = "Administração Direta"

        tipo_adm = st.pills(
            "Selecione o âmbito:",
            options=[
                "Administração Direta",
                "Administração Indireta",
                "Total (Direta + Indireta)",
            ],
            selection_mode="single",
            key=key_tipo,
            on_change=callback_func,
        )

        if not tipo_adm:
            tipo_adm = "Administração Direta"

        key_modo = "adm_modo_visualizacao"
        if key_modo not in st.session_state:
            st.session_state[key_modo] = "Vínculos Totais"

        modo_view = st.segmented_control(
            "Visualização:",
            options=["Vínculos Totais", "Percentual (%)"],
            selection_mode="single",
            key=key_modo,
            on_change=callback_func,
        )

        if not modo_view:
            modo_view = "Vínculos Totais"

        df_plot = preparar_dados_adm_stacked(df, tipo_adm)

        if not df_plot.empty and df_plot["quantidade"].sum() > 0:
            modo_label = (
                "Vínculos Totais"
                if modo_view == "Vínculos Totais"
                else "em Percentual (%)"
            )
            titulo_graf = f"Distribuição de Vínculos - {tipo_adm} - {modo_label}"
            titulo_centralizado(titulo_graf, 6)

            # --- CÁLCULOS E FORMATAÇÃO MANUAL ---

            # 1. Calcular totais por ano/município para obter a porcentagem
            df_totais = df_plot.groupby(["ano", "municipio"])["quantidade"].transform(
                "sum"
            )
            df_plot["percentual"] = (df_plot["quantidade"] / df_totais) * 100

            # 2. Definição do limiar para esconder textos pequenos
            #    Isso limpa o gráfico visualmente
            df_plot["mostrar_texto"] = df_plot["percentual"] > 1

            # 3. Funções de formatação
            def formatar_absoluto(valor):
                # Formata como 1.234 (ponto como separador de milhar)
                return f"{valor:,.0f}".replace(",", ".")

            def formatar_percentual(valor):
                return f"{valor:.0f}%"

            # 4. Criar colunas de texto formatadas
            df_plot["texto_abs"] = df_plot.apply(
                lambda row: formatar_absoluto(row["quantidade"])
                if row["mostrar_texto"]
                else "",
                axis=1,
            )
            df_plot["texto_pct"] = df_plot.apply(
                lambda row: formatar_percentual(row["percentual"])
                if row["mostrar_texto"]
                else "",
                axis=1,
            )

            # 5. Configurar variáveis baseadas no modo selecionado
            if modo_view == "Absoluto":
                coluna_texto = "texto_abs"
                barnorm_param = ""
                y_title = "Quantidade de Servidores"
                # Formata tooltip
                hover_template = (
                    "<b>%{data.name}</b><br>"
                    "Quantidade: %{customdata[0]}<br>"  # Usa o valor formatado
                    "Proporção: %{customdata[1]:.1f}%<extra></extra>"
                )
            else:
                coluna_texto = "texto_pct"
                barnorm_param = "percent"
                y_title = "Distribuição (%)"
                hover_template = (
                    "<b>%{data.name}</b><br>"
                    "Distribuição: %{customdata[1]:.1f}%<br>"
                    "Quantidade: %{customdata[0]}<extra></extra>"
                )

            # Criar coluna formatada para o tooltip
            df_plot["tooltip_qtd"] = df_plot["quantidade"].apply(formatar_absoluto)

            # --- PLOTAGEM ---
            fig = px.bar(
                df_plot,
                x="municipio",
                y="quantidade",
                color="vinculo",
                barmode="relative",
                facet_col="ano",
                category_orders={"vinculo": ORDEM_VINCULOS},
                color_discrete_map=CORES_VINCULOS,
                text=coluna_texto,
                height=500,
                custom_data=["tooltip_qtd", "percentual"],
            )

            # --- AJUSTES FINAIS DE LAYOUT ---

            fig.for_each_annotation(
                lambda a: a.update(text=a.text.split("=")[-1], y=-0.15)
            )

            fig.update_layout(
                title="",
                xaxis_title="",
                yaxis_title=y_title,
                legend_title="",
                hovermode="x unified",
                showlegend=True,
                margin=dict(l=20, r=20, t=30, b=80),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.00, xanchor="center", x=0.5
                ),
                barnorm=barnorm_param,
            )

            fig.update_xaxes(title_text="")

            fig.update_traces(
                textfont_size=12,
                textangle=0,
                textposition="inside",
                hovertemplate=hover_template,
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning(f"Não há dados disponíveis para {tipo_adm}.")


# --- FUNÇÃO PRINCIPAL DA PÁGINA ---


def show_page_adm_publica(df_adm_publica):
    """
    Renderiza a página de Administração Pública.
    """

    # Inicializa estado do expander
    if "adm_vinculos_expander_state" not in st.session_state:
        st.session_state.adm_vinculos_expander_state = True

    titulo_centralizado("Dashboard de Administração Pública", 1)

    display_adm_publica_expander(
        df=df_adm_publica,
        expander_state_key="adm_vinculos_expander_state",
        callback_func=adm_vinculos_callback,
    )
