import streamlit as st
import pandas as pd
import requests
import io
import os
from supabase import create_client, Client

# CONFIGURAÇÃO DA CONEXÃO SUPABASE ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ID do PDF no Google Drive
ID_PDF_INDICADORES_FINANCEIROS = "1oyJg_JH5hlVYmXFDwSuKH7p5lqiePefl"

supabase_client: Client = None

# Validação das variáveis de ambiente
if not SUPABASE_URL or not SUPABASE_KEY:
    print("Erro fatal: SUPABASE_URL or SUPABASE_KEY não estão definidas no ambiente.")
    st.error(
        "Erro de Configuração: As variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não foram encontradas."
    )
else:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Conexão com Supabase estabelecida para o data_loader.")
    except Exception as e:
        print(f"Erro ao conectar ao Supabase no data_loader: {e}")
        st.error(
            f"Falha ao conectar ao Supabase: {e}. Verifique as variáveis de ambiente SUPABASE_URL e SUPABASE_KEY."
        )


# FUNÇÕES AUXILIARES E CACHE

CACHE_TTL = 172800  # 48 horas


def construir_url_gdrive_download(file_id):
    """Constrói o URL de download direto para um arquivo do Google Drive."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"


@st.cache_data(ttl=CACHE_TTL)
def carregar_pdf_indicadores_financeiros():
    """Baixa o PDF de indicadores financeiros do Google Drive."""
    try:
        url = construir_url_gdrive_download(ID_PDF_INDICADORES_FINANCEIROS)
        response = requests.get(url)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao baixar o PDF de referência: {e}")
        st.error("Verifique o ID do PDF e se as permissões de partilha estão corretas.")
        return None


# --- FUNÇÕES DE CARREGAMENTO DE DADOS (SUPABASE) ---


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_indicadores_financeiros(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_indicadores_financeiros")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_financas(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_financas")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_populacao_densidade(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_populacao_densidade")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_populacao_sexo_idade(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_populacao_sexo_idade")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_municipios(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_emprego_municipios")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_municipios(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_vinculos_municipios")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_cnae(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_emprego_cnae")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_cnae(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_vinculos_cnae")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_grau_instrucao(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_emprego_grau_instrucao")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_grau_instrucao(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_vinculos_grau_instrucao")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_faixa_etaria(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_emprego_faixa_etaria")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_faixa_etaria(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_vinculos_faixa_etaria")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_raca_cor(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_emprego_raca_cor")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_raca_cor(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_vinculos_raca_cor")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_sexo(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_emprego_sexo")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_sexo(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_vinculos_sexo")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_estabelecimentos_cnae(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_estabelecimentos_cnae")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_estabelecimentos_tamanho(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_estabelecimentos_tamanho")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_estabelecimentos_municipios(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_estabelecimentos_municipios")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_renda_cnae(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_renda_cnae")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_renda_sexo(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_renda_sexo")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_renda_municipios(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_renda_municipios")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_comex_anual(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_comex_anual")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_comex_mensal(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_comex_mensal")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_comex_municipio(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_comex_municipio")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_seguranca(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_seguranca")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_seguranca_taxa(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_seguranca_taxa")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_CAD(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_cadastro_unico")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_bolsa_familia(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_bolsa_familia")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_cnpj_total(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_cnpj_total")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_cnpj_cnae(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_cnpj_cnae")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_cnpj_cnae_saldo(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_cnpj_cnae_saldo")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_mei_total(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_mei_total")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_mei_cnae(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_mei_cnae")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_mei_cnae_saldo(municipio, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_mei_cnae_saldo")
        .select("*")
        .eq("municipio", municipio)
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_educacao_matriculas(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_educacao_matriculas")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_educacao_rendimento(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_educacao_rendimento")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_educacao_ideb_municipio(municipios):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_educacao_ideb_municipios")
        .select("*")
        .in_("municipio", list(municipios))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_educacao_ideb_escolas(municipios):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_educacao_ideb_escolas")
        .select("*")
        .in_("municipio", list(municipios))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_mensal(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_saude_mensal")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_despesas(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_saude_despesas")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_leitos(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_saude_leitos")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_medicos(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_saude_medicos")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_vacinas(municipios, anos):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_saude_vacinas")
        .select("*")
        .in_("municipio", list(municipios))
        .in_("ano", list(anos))
        .execute()
    )
    return pd.DataFrame(response.data)


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_pib_municipios(municipios):
    if not supabase_client:
        st.error("Conexão com Supabase não estabelecida.")
        return pd.DataFrame()
    response = (
        supabase_client.table("dados_pib_municipios")
        .select("*")
        .in_("municipio", list(municipios))
        .execute()
    )
    return pd.DataFrame(response.data)
