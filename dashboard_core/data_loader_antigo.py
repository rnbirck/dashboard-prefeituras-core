import streamlit as st
import pandas as pd
import requests
import io

# ID PLANILHAS GOOGLE SHEETS
ID_EMPREGO_MUNICIPIOS = "1R-ehxIUZnRZLetEL0b2SgvkK-YQdtBBl1ff_dtgAYpg"
ID_EMPREGO_CNAE = "1scPanyLdRKBLkWSwhxQiZryS1wVinfQ6vCqZakbkDmg"
ID_EMPREGO_GRAU_INSTRUCAO = "1WlBPJMbgMkAReFFeraqhHPHeIMA0oPoJ3A2d7sF52ns"
ID_EMPREGO_FAIXA_ETARIA = "18vXZaCkc8so4rO5jUN9XKzJDdumPCm7RdaVNmIBAFQ0"
ID_EMPREGO_RACA_COR = "10aStpcwC9qG8SGHIuloLxVaW_uCJR6TfGsnckPkeA5E"
ID_EMPREGO_SEXO = "1qwztnxdlIsK7DaIqbCNcFmTbFf9GR6ARJCgT00wE83o"
ID_COMEX_ANUAL = "1j4Xx0_PPHwDDvC9ybKhcbBovk3HpXUGVKnBfS5JxxEo"
ID_COMEX_MENSAL = "1I_d1n1KoU3VbHr5FVCX7oGp6VezgAgQQVvMnTFApbRU"
ID_COMEX_MUNICIPIO = "1DC89QdcB5GxuZgZamHH8xOSlp-BP_5oayKa5jsjl2c8"
ID_SEGURANCA = "1cPzaMIrHk-T5oJQKPxlFepHf63_-nQjHIFTf2xZzsog"
ID_SEGURANCA_TAXA = "1GUiqyYyXVleSNfkhdi0R36EFTAGw_hafeKylmMDRb4c"
ID_CAD = "15TiAHgFeM2gJ6NARrDfezJRRJt-TY64ksN4l7MMMrQE"
ID_BOLSA_FAMILIA = "1xuBjiv3in12U_xrdScGExMXTjfOlt3-shK_FiVT9E0o"
ID_CNPJ_TOTAL = "1S34HnK0wG4h9ifWnm066RQsubEMsrN5y6ZsHI8yvd_s"
ID_CNPJ_CNAE = "1LlGELAUNFBAg3gIKyZjJ5tE1VfQVAr5tqzGBVtvwLXg"
ID_MEI_TOTAL = "1x4gKWVJNOo13hH-2AchgrA6YIntZJphOlOjhhCDrO5s"
ID_MEI_CNAE = "1IaWCby0TmW-h9vBmqhvjZm-8CwayYAFS5xCVz_TeQLM"
ID_EDUCACAO_MATRICULAS = "1V2_LK6KmHWRS9G3dTDuvyseH4VK51V_h-WqyKo1vC2g"
ID_EDUCACAO_RENDIMENTO = "1eXvWso6qsqhAxuIp3_LJ8mxIDtuhnMhGFOgx_wB-G4E"
ID_EDUCACAO_IDEB_MUNICIPIOS = "1hRIaMp9NUkEJuv8-1B3o4tnBokPMecFlAUO_43eyEBI"
ID_EDUCACAO_IDEB_ESCOLAS = "1ckSLZvqznbCOcgNEnah3UGW5L4nraIU24RRKF79JKIg"
ID_SAUDE_MENSAL = "1zxQ37QD7zmLR-dZhsjtYG-ihpMhD9Pr1gxyX5ZDS2hA"
ID_SAUDE_DESPESAS = "1kn7dt3Ind5rZStsgP4Nu1F9FddOFpxqYxQ99gSh0--c"
ID_SAUDE_LEITOS = "1XMLERbG4Z0Dxb1EVKB5WAPFsNPxISMQt1ZaYgfIVz4s"
ID_SAUDE_MEDICOS = "1Tvie09HPgt9khclDk6QHZ1NgzlZNaOUsNpaMKrOC8ss"
ID_SAUDE_VACINAS = "1pAPjXAtBMhnii0haht54QUpr_BlDSxwrXkhjSXob0OE"
ID_VINCULOS_CNAE = "1NPsAW28DceBExTq66qkHQ13ET2m1IK29AKXJFXvUzrY"
ID_VINCULOS_FAIXA_ETARIA = "1LDwQU64dpZuuGwNlWv8N8XXoYrgkGtmvqzIB4pRGtGs"
ID_VINCULOS_GRAU_INSTRUCAO = "1Z5MKP12S0y651P0xVn7E7rJ5EVvYwfcgi5k_6Y_AVM0"
ID_VINCULOS_MUNICIPIOS = "1IG4HMcclKI4LvW8F5P8wByuPV71ZQ0gZU81o_KQpNPw"
ID_VINCULOS_RACA_COR = "1BgjfFWRD9oaK6C8_S10RUcmU98tuHGPqBGKSoCx54F0"
ID_VINCULOS_SEXO = "1uwtvR1jPyL2mmOESyBrrC-y3P0RqL1--kLQ7KQ47dJM"
ID_ESTABELECIMENTOS_CNAE = "1LQX37GOmohl9WXY137D1dP2VvwyQ1avl7hsu5WCJo14"
ID_ESTABELECIMENTOS_MUNICIPIOS = "15miIVTYwYYgHYVeWKBDCwMPtWOswnDGFtqQLp6YINPw"
ID_ESTABELECIMENTOS_TAMANHO = "1wv7WWcpp0th9Vr4qyGpXWVsgz2b7owtqq74HHzFo1bc"
ID_RENDA_CNAE = "1cCsZrK-qJaAAQtERcBzpx7cSa78_e7s5TM-g-SCNRjI"
ID_RENDA_MUNICIPIOS = "1Z2UNDFlMySv3-lhFjR0TQFTVYcm0K0kVtgLp-ozeuEk"
ID_RENDA_SEXO = "1dDOLWl081WEP5tRvWj0iIO7JoXdW-wiUXwgEB-AUsHU"
ID_PIB_MUNICIPIOS = "1AmsNK8wR5T8zJjac2APHIzsSYFwPvcDpIRaPF4ocr5A"
ID_POPULACAO_DENSIDADE = "1UDNbCgNDg-hd4gKR0TKDCO6YogyvU5KjthIIHt0mPTs"
ID_POPULACAO_SEXO_IDADE = "1RTvQxzfusbSiUKtlkIQMmpiN1a-pApYofgD6Mx4UEk4"
ID_FINANCAS = "1OehlNsW8-G-jSAgnHlSNQyebq1j_aqPcy9JMaX6BtB8"
ID_INDICADORES_FINANCEIROS = "1ItayGlEsaOAaSIzdj7ErcQadHHOtC3xqPLOd_W-bGaU"
ID_PDF_INDICADORES_FINANCEIROS = "1oyJg_JH5hlVYmXFDwSuKH7p5lqiePefl"


def construir_url_gsheet(sheet_id):
    """Constrói o URL de exportação CSV para uma planilha do Google Sheets."""
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"


def construir_url_gdrive_download(file_id):
    """Constrói o URL de download direto para um arquivo do Google Drive."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"


CACHE_TTL = 172800  # 48 horas


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_indicadores_financeiros(municipios, anos):
    url = construir_url_gsheet(ID_INDICADORES_FINANCEIROS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


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


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_financas(municipios, anos):
    url = construir_url_gsheet(ID_FINANCAS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_populacao_densidade(municipios, anos):
    url = construir_url_gsheet(ID_POPULACAO_DENSIDADE)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_populacao_sexo_idade(municipios, anos):
    url = construir_url_gsheet(ID_POPULACAO_SEXO_IDADE)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_municipios(municipios, anos):
    url = construir_url_gsheet(ID_EMPREGO_MUNICIPIOS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_municipios(municipios, anos):
    url = construir_url_gsheet(ID_VINCULOS_MUNICIPIOS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_cnae(municipio, anos):
    url = construir_url_gsheet(ID_EMPREGO_CNAE)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_cnae(municipio, anos):
    url = construir_url_gsheet(ID_VINCULOS_CNAE)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_grau_instrucao(municipio, anos):
    url = construir_url_gsheet(ID_EMPREGO_GRAU_INSTRUCAO)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_grau_instrucao(municipio, anos):
    url = construir_url_gsheet(ID_VINCULOS_GRAU_INSTRUCAO)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_faixa_etaria(municipio, anos):
    url = construir_url_gsheet(ID_EMPREGO_FAIXA_ETARIA)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_faixa_etaria(municipio, anos):
    url = construir_url_gsheet(ID_VINCULOS_FAIXA_ETARIA)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_raca_cor(municipio, anos):
    url = construir_url_gsheet(ID_EMPREGO_RACA_COR)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_raca_cor(municipio, anos):
    url = construir_url_gsheet(ID_VINCULOS_RACA_COR)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_emprego_sexo(municipio, anos):
    url = construir_url_gsheet(ID_EMPREGO_SEXO)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_vinculos_sexo(municipio, anos):
    url = construir_url_gsheet(ID_VINCULOS_SEXO)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_estabelecimentos_cnae(municipio, anos):
    url = construir_url_gsheet(ID_ESTABELECIMENTOS_CNAE)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_estabelecimentos_tamanho(municipio, anos):
    url = construir_url_gsheet(ID_ESTABELECIMENTOS_TAMANHO)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_estabelecimentos_municipios(municipios, anos):
    url = construir_url_gsheet(ID_ESTABELECIMENTOS_MUNICIPIOS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_renda_cnae(municipio, anos):
    url = construir_url_gsheet(ID_RENDA_CNAE)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_renda_sexo(municipio, anos):
    url = construir_url_gsheet(ID_RENDA_SEXO)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_renda_municipios(municipios, anos):
    url = construir_url_gsheet(ID_RENDA_MUNICIPIOS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_comex_anual(municipios, anos):
    url = construir_url_gsheet(ID_COMEX_ANUAL)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_comex_mensal(municipios, anos):
    url = construir_url_gsheet(ID_COMEX_MENSAL)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_comex_municipio(municipio, anos):
    url = construir_url_gsheet(ID_COMEX_MUNICIPIO)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_seguranca(municipios, anos):
    """Lê os dados de seguranca da planilha Google."""
    url = construir_url_gsheet(ID_SEGURANCA)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_seguranca_taxa(municipios, anos):
    """Lê os dados de taxa de seguranca da planilha Google."""
    url = construir_url_gsheet(ID_SEGURANCA_TAXA)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_CAD(municipios, anos):
    """Lê os dados do cadastro único da planilha Google."""
    url = construir_url_gsheet(ID_CAD)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_bolsa_familia(municipios, anos):
    """Lê os dados do novo bolsa família da planilha Google."""
    url = construir_url_gsheet(ID_BOLSA_FAMILIA)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_cnpj_total(municipios, anos):
    """Lê os dados de CNPJ total da planilha Google."""
    url = construir_url_gsheet(ID_CNPJ_TOTAL)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_cnpj_cnae(municipio, anos):
    """Lê os dados de CNPJ CNAE da planilha Google."""
    url = construir_url_gsheet(ID_CNPJ_CNAE)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_mei_total(municipios, anos):
    """Lê os dados de MEI total da planilha Google."""
    url = construir_url_gsheet(ID_MEI_TOTAL)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_mei_cnae(municipio, anos):
    """Lê os dados de MEI CNAE da planilha Google."""
    url = construir_url_gsheet(ID_MEI_CNAE)
    df = pd.read_csv(url)
    return df[(df["municipio"] == municipio) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_educacao_matriculas(municipios, anos):
    """Lê os dados de Educacao Matriculas da planilha Google."""
    url = construir_url_gsheet(ID_EDUCACAO_MATRICULAS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_educacao_rendimento(municipios, anos):
    """Lê os dados de Educacao Rendimento da planilha Google."""
    url = construir_url_gsheet(ID_EDUCACAO_RENDIMENTO)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_educacao_ideb_municipio(municipios):
    """Lê os dados de Educacao de IDEB Municipio da planilha Google."""
    url = construir_url_gsheet(ID_EDUCACAO_IDEB_MUNICIPIOS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_educacao_ideb_escolas(municipios):
    """Lê os dados de Educacao de IDEB Escola da planilha Google."""
    url = construir_url_gsheet(ID_EDUCACAO_IDEB_ESCOLAS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_mensal(municipios, anos):
    """Lê os dados de Saúde Mensal da planilha Google."""
    url = construir_url_gsheet(ID_SAUDE_MENSAL)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_despesas(municipios, anos):
    """Lê os dados de Saúde Despesas da planilha Google."""
    url = construir_url_gsheet(ID_SAUDE_DESPESAS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_leitos(municipios, anos):
    """Lê os dados de Saúde leitos da planilha Google."""
    url = construir_url_gsheet(ID_SAUDE_LEITOS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_medicos(municipios, anos):
    """Lê os dados de Saúde medicos da planilha Google."""
    url = construir_url_gsheet(ID_SAUDE_MEDICOS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_saude_vacinas(municipios, anos):
    """Lê os dados de Saúde vacinas da planilha Google."""
    url = construir_url_gsheet(ID_SAUDE_VACINAS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios)) & (df["ano"].isin(anos))]


@st.cache_data(ttl=CACHE_TTL)
def carregar_dados_pib_municipios(municipios):
    """Lê os dados de PIB dos municipios da planilha Google."""
    url = construir_url_gsheet(ID_PIB_MUNICIPIOS)
    df = pd.read_csv(url)
    return df[(df["municipio"].isin(municipios))]
