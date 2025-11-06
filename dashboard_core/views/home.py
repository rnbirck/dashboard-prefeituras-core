# %%
import streamlit as st
from dashboard_core.utils import MESES_DIC, BIMESTRE_DIC, titulo_centralizado


# ==============================================================================
# FUNÇÕES DA PÁGINA HOME
# ==============================================================================
def go_to_page(page_name):
    """Atualiza o estado da sessão para mudar a página selecionada."""
    st.session_state.selected_page = page_name


def show_page_home(
    df_emprego,
    df_comex,
    df_seguranca,
    df_assistencia_cad,
    df_assistencia_bolsa,
    df_financas,
    df_indicadores_financeiros,
    df_empresas,
    df_educacao_matriculas,
    df_educacao_ideb,
    df_vinculos,
    df_pib,
    df_saude_mensal,
    df_populacao_densidade,
    df_populacao_sexo_idade,
    municipio_de_interesse,
):
    """
    Renderiza a página inicial do dashboard com instruções, informações e datas de atualização.
    """

    titulo_centralizado("📊 Dashboard de Indicadores Municipais", 1)
    st.markdown("---")
    titulo_centralizado("Bem-vindo(a) ao painel de visualização de dados!", 2)
    st.markdown(
        f"""
        ##### Este dashboard foi desenvolvido para apresentar diversos indicadores socioeconômicos de **{municipio_de_interesse}**, permitindo a comparação direta com municípios vizinhos e de perfil semelhante.
        """
    )
    st.markdown("---")
    st.subheader("🧭 Como Utilizar o Dashboard")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            #### 1. Filtro Global de Municípios
            No topo da barra lateral à esquerda, você pode selecionar um ou mais municípios. Sua escolha será aplicada a **todas as páginas** do dashboard.
            """
        )

    with col2:
        st.markdown(
            """
            #### 2. Menus de Análise (Seções Expansíveis)
            Em cada página, os dados são organizados em seções recolhíveis. Clique em qualquer seção para expandir e ver as análises detalhadas.
            """
        )

    col3, col4 = st.columns(2, gap="large")

    with col3:
        st.markdown(
            """
            #### 3. Seletores de Indicadores (Caixas de Seleção)
            Dentro de alguns menus, você encontrará **caixas de seleção** que permitem escolher o indicador específico que deseja analisar.
            """
        )

    with col4:
        st.markdown(
            """
            #### 4. Alternar Visualizações (Botões de Opção)
            Em algumas seções, você encontrará botões de opção que permitem alternar a visualização dos dados (ex: "Valor" vs "Taxa de Crescimento"), oferecendo diferentes perspectivas.
            """
        )

    st.markdown("---")
    st.subheader("📂 Sobre as Páginas e Atualizações")

    try:
        ult_ano_emprego = df_emprego["ano"].max()
        ult_mes_emprego = df_emprego[df_emprego["ano"] == ult_ano_emprego]["mes"].max()
        data_emprego = f"{MESES_DIC[ult_mes_emprego]} de {ult_ano_emprego}"
    except Exception:
        data_emprego = "Não disponível"

    try:
        data_rais = str(int(df_vinculos["ano"].max()))
    except Exception:
        data_rais = "Não disponível"

    try:
        ult_ano_comex = df_comex["ano"].max()
        ult_mes_comex = df_comex[df_comex["ano"] == ult_ano_comex]["mes"].max()
        data_comex = f"{MESES_DIC[ult_mes_comex]} de {ult_ano_comex}"
    except Exception:
        data_comex = "Não disponível"

    try:
        ult_ano_seg = df_seguranca["ano"].max()
        ult_mes_seg = df_seguranca[df_seguranca["ano"] == ult_ano_seg]["mes"].max()
        data_seguranca = f"{MESES_DIC[ult_mes_seg]} de {ult_ano_seg}"
    except Exception:
        data_seguranca = "Não disponível"

    try:
        ult_ano_cad = df_assistencia_cad["ano"].max()
        ult_mes_cad = df_assistencia_cad[df_assistencia_cad["ano"] == ult_ano_cad][
            "mes"
        ].max()
        data_cad = f"{MESES_DIC[ult_mes_cad]} de {ult_ano_cad}"

        ult_ano_bolsa = df_assistencia_bolsa["ano"].max()
        ult_mes_bolsa = df_assistencia_bolsa[
            df_assistencia_bolsa["ano"] == ult_ano_bolsa
        ]["mes"].max()
        data_bolsa = f"{MESES_DIC[ult_mes_bolsa]} de {ult_ano_bolsa}"
    except Exception:
        data_cad = "Não disponível"
        data_bolsa = "Não disponível"

    try:
        ult_ano_fin_bim = df_financas["ano"].max()
        ult_bim_fin = df_financas[df_financas["ano"] == ult_ano_fin_bim][
            "bimestre"
        ].max()
        data_financas_bim = f"{BIMESTRE_DIC[ult_bim_fin]} de {ult_ano_fin_bim}"
    except Exception:
        data_financas_bim = "Não disponível"

    try:
        data_financas_anual = str(int(df_indicadores_financeiros["ano"].max()))
    except Exception:
        data_financas_anual = "Não disponível"

    try:
        ult_ano_empresas = df_empresas["ano"].max()
        ult_mes_empresas = df_empresas[df_empresas["ano"] == ult_ano_empresas][
            "mes"
        ].max()
        data_empresas = f"{MESES_DIC[ult_mes_empresas]} de {ult_ano_empresas}"
    except Exception:
        data_empresas = "Não disponível"
    try:
        data_matriculas = str(df_educacao_matriculas["ano"].max())
        data_ideb = str(df_educacao_ideb["ano"].max())
    except Exception:
        data_matriculas, data_ideb = "Não disponível", "Não disponível"

    try:
        data_pib = str(int(df_pib["ano"].max()))
    except Exception:
        data_pib = "Não disponível"

    try:
        ult_ano_saude = df_saude_mensal["ano"].max()
        ult_mes_saude = df_saude_mensal[df_saude_mensal["ano"] == ult_ano_saude][
            "mes"
        ].max()
        data_saude = f"{MESES_DIC[ult_mes_saude]} de {ult_ano_saude}"
    except Exception:
        data_saude = "Não disponível"

    try:
        data_demografia_pop = str(int(df_populacao_densidade["ano"].max()))
    except Exception:
        data_demografia_pop = "Não disponível"

    try:
        data_demografia_faixa = str(int(df_populacao_sexo_idade["ano"].max()))
    except Exception:
        data_demografia_faixa = "Não disponível"

    col_a, col_b = st.columns(2, gap="large")

    # --- COLUNA A ---
    # Ordem: Emprego, Empresas, Comércio Exterior, Segurança, Assistência Social
    with col_a:
        st.markdown(
            f"""
            #### 💼 Emprego
            Analisa o mercado de trabalho formal a partir de duas fontes principais: os dados mensais do **CAGED** (saldo de admissões/demissões) e as estatísticas anuais da **RAIS** (vínculos, remuneração e estabelecimentos).
            
            *Frequência: **Mensal (CAGED)** e **Anual (RAIS)***
            
            *Últimos dados: **CAGED:** **{data_emprego}** | **RAIS:** **{data_rais}***
            """
        )
        st.button(
            "Explorar Emprego ➔",
            on_click=go_to_page,
            args=("Emprego",),
            key="btn_home_emprego",
        )
        st.markdown("---")

        st.markdown(
            f"""
            #### 🏢 Empresas
            Apresenta o número de CNPJs e MEIs ativos (dados da **Receita Federal**) e a quantidade de estabelecimentos formais (dados da **RAIS**). Permite analisar a evolução e a concentração por setor e porte.
            
            *Frequência: **Mensal (Receita Federal)** e **Anual (RAIS)***
            
            *Últimos dados: **CNPJ/MEI:** **{data_empresas}** | **Estabelecimentos:** **{data_rais}***
            """
        )
        st.button(
            "Explorar Empresas ➔",
            on_click=go_to_page,
            args=("Empresas",),
            key="btn_home_empresas",
        )
        st.markdown("---")

        st.markdown(
            f"""
            #### ✈️ Comércio Exterior
            Apresenta os dados de exportação com base nos dados do **Comexstat**. É possível analisar os valores totais, os principais produtos exportados e os países de destino.
            
            *Frequência: **Mensal***
            
            *Últimos dados: **{data_comex}***
            """
        )
        st.button(
            "Explorar Comércio Exterior ➔",
            on_click=go_to_page,
            args=("Comércio Exterior",),
            key="btn_home_comex",
        )
        st.markdown("---")

        st.markdown(
            f"""
            #### 🛡️ Segurança Pública
            Reúne os principais indicadores de criminalidade divulgados pela **SSP/RS**, com visualização em números absolutos e taxas por 10 mil habitantes.
            
            *Frequência: **Mensal*** 
            
            *Últimos dados: **{data_seguranca}***
            """
        )
        st.button(
            "Explorar Segurança ➔",
            on_click=go_to_page,
            args=("Segurança",),
            key="btn_home_seguranca",
        )
        st.markdown("---")

        st.markdown(
            f"""
            #### ❤️ Assistência Social
            Apresenta informações sobre a população em vulnerabilidade social, com dados do **Cadastro Único (CadÚnico)** e do programa **Novo Bolsa Família**.
            
            *Frequência: **Mensal*** 
            
            *Últimos dados: **CadÚnico:** **{data_cad}** | **Novo Bolsa Família:** **{data_bolsa}***
            """
        )
        st.button(
            "Explorar Assistência Social ➔",
            on_click=go_to_page,
            args=("Assistência Social",),
            key="btn_home_assistencia",
        )
        st.markdown("---")

        st.markdown(
            """
            #### 📥 Dados 
            Página destinada ao download das bases utilizadas na construção do dashboard.
            
            *Frequência: Conforme atualização das fontes*
            """
        )
        st.button(
            "Explorar Dados ➔",
            on_click=go_to_page,
            args=("Dados",),
            key="btn_home_dados",
        )

    # --- COLUNA B ---
    # Ordem: Educação, Saúde, PIB, Demografia, Finanças
    with col_b:
        st.markdown(
            f"""
            #### 🎓 Educação
            Consolida indicadores educacionais do **Censo Escolar** e do **INEP (IDEB)**, incluindo matrículas, docentes, turmas, taxas de rendimento e notas de avaliação do SAEB.
            
            *Frequência: **Anual (Censo)** e **Bienal (IDEB)*** 
            
            *Últimos dados: **Censo:** **{data_matriculas}** | **IDEB:** **{data_ideb}***
            """
        )
        st.button(
            "Explorar Educação ➔",
            on_click=go_to_page,
            args=("Educação",),
            key="btn_home_educacao",
        )
        st.markdown("---")

        st.markdown(
            f"""
            #### 🏥 Saúde
            Indicadores de saúde pública, incluindo nascimentos, óbitos, cobertura vacinal, leitos e despesas. Dados provenientes de fontes como a Secretaria de Saúde do RS, DATASUS e CNES.
            
            *Frequência: **Mensal** e **Anual*** 
            
            *Últimos dados: **{data_saude}***
            """
        )
        st.button(
            "Explorar Saúde ➔",
            on_click=go_to_page,
            args=("Saúde",),
            key="btn_home_saude",
        )
        st.markdown("---")

        st.markdown(
            f"""
            #### 📈 PIB (Produto Interno Bruto)
            Analisa a soma de todos os bens e serviços finais produzidos por município. Explore o PIB total, o PIB per capita e a composição do Valor Adicionado Bruto (VAB) por setor disponibilizados pelo **IBGE**.
            
            *Frequência: **Anual***
            
            *Últimos dados: **{data_pib}***
            """
        )
        st.button(
            "Explorar PIB ➔",
            on_click=go_to_page,
            args=("PIB",),
            key="btn_home_pib",
        )
        st.markdown("---")

        st.markdown(
            f"""
            #### 👨‍👩‍👧‍👦 Demografia
            Análise da população estimada, densidade demográfica e estrutura etária (pirâmide etária) por sexo. Dados baseados nas estimativas populacionais do **IBGE**.
            
            *Frequência: **Anual***
            
            *Últimos dados: **População:** **{data_demografia_pop}** | **Faixa Etária/Sexo:** **{data_demografia_faixa}***
            """
        )
        st.button(
            "Explorar Demografia ➔",
            on_click=go_to_page,
            args=("Demografia",),
            key="btn_home_demografia",
        )
        st.markdown("---")

        st.markdown(
            f"""
            #### 💰 Finanças Públicas
            Apresenta dados fiscais do **SICONFI**, divididos em **Indicadores Financeiros Anuais** e **Indicadores de Execução Orçamentária Bimestrais**.
            
            *Frequência: **Anual** e **Bimestral***
            
            *Últimos dados: **Indicadores (Anual):** **{data_financas_anual}** | **Execução (Bimestral):** **{data_financas_bim}***
            """
        )
        st.button(
            "Explorar Finanças ➔",
            on_click=go_to_page,
            args=("Finanças",),
            key="btn_home_financas",
        )
