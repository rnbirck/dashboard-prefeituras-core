import streamlit as st
from dashboard_core.utils import to_excel, titulo_centralizado


def show_page_dados(
    # --- DataFrames da Página Emprego ---
    df_caged,
    df_caged_cnae,
    df_caged_faixa_etaria,
    df_caged_raca_cor,
    df_caged_grau_instrucao,
    df_caged_sexo,
    df_vinculos,
    df_vinculos_cnae,
    df_vinculos_faixa_etaria,
    df_vinculos_grau_instrucao,
    df_vinculos_raca_cor,
    df_vinculos_sexo,
    df_renda_mun,
    df_renda_sexo,
    df_renda_cnae,
    municipio_de_interesse,
    # --- DataFrames da Página Empresas ---
    df_cnpj_mun,
    df_cnpj_cnae,
    df_cnpj_cnae_saldo,
    df_mei_mun,
    df_mei_cnae,
    df_mei_cnae_saldo,
    df_estabelecimentos_mun,
    df_estabelecimentos_cnae,
    df_estabelecimentos_tamanho,
    # --- DataFrames da Página Comércio Exterior ---
    df_comex_anual_mun,
    df_comex_mensal_mun,
    df_comex_raw_municipio_foco,
    # --- DataFrames da Página Segurança ---
    df_seguranca_mun,
    df_seguranca_taxa_mun,
    # --- DataFrames da Página Assistência Social ---
    df_cad,
    df_bolsa,
    # --- DataFrames da Página Educação ---
    df_educacao_matriculas,
    df_educacao_rendimento,
    df_educacao_ideb_municipio,
    df_educacao_ideb_escolas,
    # --- DataFrames da Página Saúde ---
    df_saude_mensal,
    df_saude_vacinas,
    df_saude_despesas,
    df_saude_leitos,
    df_saude_medicos,
    # --- DataFrame da Página PIB ---
    df_pib_municipios,
    # --- DataFrames da Página Demografia ---
    df_populacao_densidade,
    df_populacao_sexo_idade,
    # --- DataFrames da Página Finanças ---
    df_financas,
    df_indicadores_financeiros,
    pdf_indicadores,
):
    """
    Renderiza a página de Download (Dados), com expanders para cada seção
    e botões para baixar os DataFrames em Excel.
    """
    titulo_centralizado("Página de Dados", 1)
    st.info(
        "Utilize os menus expansíveis abaixo para baixar os arquivos excel com os dados brutos do dashboard."
    )

    # --- EXPANDER DA PÁGINA DE EMPREGO ---
    with st.expander("Dados da Página: Emprego"):
        st.subheader("Dados de Saldo de Emprego (CAGED)")
        st.markdown(
            "Dados mensais de admissões e demissões (saldo) por município e categorias."
        )

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Saldo por Município (CAGED)",
                data=to_excel(df_caged),
                file_name="caged_saldo_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Saldo por CNAE em {municipio_de_interesse}",
                data=to_excel(df_caged_cnae),
                file_name="caged_saldo_cnae.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Saldo por Raça/Cor em {municipio_de_interesse}",
                data=to_excel(df_caged_raca_cor),
                file_name="caged_saldo_raca_cor.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label=f"📥 Saldo por Sexo em {municipio_de_interesse}",
                data=to_excel(df_caged_sexo),
                file_name="caged_saldo_sexo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Saldo por Faixa Etária em {municipio_de_interesse}",
                data=to_excel(df_caged_faixa_etaria),
                file_name="caged_saldo_faixa_etaria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Saldo por Grau de Instrução em {municipio_de_interesse}",
                data=to_excel(df_caged_grau_instrucao),
                file_name="caged_saldo_grau_instrucao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.divider()

        st.subheader("Dados de Vínculos Ativos (RAIS)")
        st.markdown("Dados anuais de vínculos formais por município e categorias.")

        col3, col4 = st.columns(2)
        with col3:
            st.download_button(
                label="📥 Vínculos por Município (RAIS)",
                data=to_excel(df_vinculos),
                file_name="rais_vinculos_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Vínculos por CNAE em {municipio_de_interesse}",
                data=to_excel(df_vinculos_cnae),
                file_name="rais_vinculos_cnae.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Vínculos por Raça/Cor em {municipio_de_interesse}",
                data=to_excel(df_vinculos_raca_cor),
                file_name="rais_vinculos_raca_cor.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col4:
            st.download_button(
                label=f"📥 Vínculos por Sexo em {municipio_de_interesse}",
                data=to_excel(df_vinculos_sexo),
                file_name="rais_vinculos_sexo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Vínculos por Faixa Etária em {municipio_de_interesse}",
                data=to_excel(df_vinculos_faixa_etaria),
                file_name="rais_vinculos_faixa_etaria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Vínculos por Grau de Instrução em {municipio_de_interesse}",
                data=to_excel(df_vinculos_grau_instrucao),
                file_name="rais_vinculos_grau_instrucao.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.divider()

        st.subheader("Dados de Remuneração Média (RAIS)")
        st.markdown(
            "Dados anuais de remuneração média (nominal e em salários mínimos) por município e categorias."
        )

        col5, col6 = st.columns(2)
        with col5:
            st.download_button(
                label="📥 Renda por Município (RAIS)",
                data=to_excel(df_renda_mun),
                file_name="rais_renda_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Renda por Sexo em {municipio_de_interesse}",
                data=to_excel(df_renda_sexo),
                file_name="rais_renda_sexo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col6:
            st.download_button(
                label=f"📥 Renda por CNAE em {municipio_de_interesse}",
                data=to_excel(df_renda_cnae),
                file_name="rais_renda_cnae.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        # --- EXPANDER DA PÁGINA DE EMPRESAS ---
    with st.expander("Dados da Página: Empresas"):
        st.subheader("Dados de CNPJ Ativos")
        st.markdown("Dados mensais de CNPJs ativos por município e categorias.")
        col7, col8 = st.columns(2)
        with col7:
            st.download_button(
                label="📥 CNPJs Ativos por Município",
                data=to_excel(df_cnpj_mun),
                file_name="cnpj_ativos_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 CNPJs Ativos por CNAE em {municipio_de_interesse}",
                data=to_excel(df_cnpj_cnae),
                file_name="cnpj_ativos_cnae.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col8:
            st.download_button(
                label=f"📥 Saldo de CNPJs por CNAE em {municipio_de_interesse}",
                data=to_excel(df_cnpj_cnae_saldo),
                file_name="cnpj_saldo_cnae.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.divider()
        st.subheader("Dados de MEI Ativos")
        st.markdown("Dados mensais de MEIs ativos por município e categorias.")
        col9, col10 = st.columns(2)
        with col9:
            st.download_button(
                label="📥 MEIs Ativos por Município",
                data=to_excel(df_mei_mun),
                file_name="mei_ativos_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 MEIs Ativos por CNAE em {municipio_de_interesse}",
                data=to_excel(df_mei_cnae),
                file_name="mei_ativos_cnae.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col10:
            st.download_button(
                label=f"📥 Saldo de MEIs por CNAE em {municipio_de_interesse}",
                data=to_excel(df_mei_cnae_saldo),
                file_name="mei_saldo_cnae.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.divider()
        st.subheader("Dados de Estabelecimentos (RAIS)")
        st.markdown(
            "Dados anuais de estabelecimentos formais por município e categorias."
        )
        col11, col12 = st.columns(2)
        with col11:
            st.download_button(
                label="📥 Estabelecimentos por Município",
                data=to_excel(df_estabelecimentos_mun),
                file_name="rais_estabelecimentos_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label=f"📥 Estabelecimentos por CNAE em {municipio_de_interesse}",
                data=to_excel(df_estabelecimentos_cnae),
                file_name="rais_estabelecimentos_cnae.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col12:
            st.download_button(
                label=f"📥 Estabelecimentos por Tamanho em {municipio_de_interesse}",
                data=to_excel(df_estabelecimentos_tamanho),
                file_name="rais_estabelecimentos_tamanho.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        # --- EXPANDER DA PÁGINA DE COMÉRCIO EXTERIOR ---
    with st.expander("Dados da Página: Comércio Exterior"):
        st.subheader("Dados de Exportação")
        st.markdown(
            "Dados anuais e mensais de exportação (US$) por município e dados brutos do município principal."
        )

        col13, col14 = st.columns(2)
        with col13:
            st.download_button(
                label="📥 Exportações Anuais por Município",
                data=to_excel(
                    df_comex_anual_mun[["ano", "municipio", "total_exp_anual"]]
                ),
                file_name="comex_exp_anual_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label="📥 Exportações Mensais por Município",
                data=to_excel(
                    df_comex_mensal_mun[
                        [
                            "ano",
                            "mes",
                            "municipio",
                            "total_exp_mensal",
                            "total_exp_acumulado",
                        ]
                    ]
                ),
                file_name="comex_exp_mensal_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col14:
            st.download_button(
                label=f"📥 Exportações Mensais (Produto/País) em {municipio_de_interesse}",
                data=to_excel(
                    df_comex_raw_municipio_foco[
                        [
                            "ano",
                            "mes",
                            "municipio",
                            "pais",
                            "produto",
                            "valor_exp_mensal",
                            "valor_acumulado_ano",
                        ]
                    ]
                ),
                file_name="comex_exp_produto_pais.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    # --- EXPANDER DA PÁGINA DE SEGURANÇA ---
    with st.expander("Dados da Página: Segurança"):
        st.subheader("Dados da Secretaria da Segurança Pública")
        st.markdown(
            "Dados mensais de ocorrências (números absolutos) e taxas (por 10 mil hab. ou 10 mil mulheres) por município."
        )

        col15, col16 = st.columns(2)
        with col15:
            st.download_button(
                label="📥 Segurança (Números Absolutos)",
                data=to_excel(df_seguranca_mun),
                file_name="seguranca_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col16:
            st.download_button(
                label="📥 Segurança (Taxas)",
                data=to_excel(df_seguranca_taxa_mun),
                file_name="seguranca_taxas_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    # --- EXPANDER DA PÁGINA: ASSISTÊNCIA SOCIAL ---
    with st.expander("Dados da Página: Assistência Social"):
        st.subheader("Dados da Assistência Social")
        st.markdown(
            "Dados mensais do Cadastro Único (CAD) e do Novo Bolsa Família por município."
        )

        col17, col18 = st.columns(2)
        with col17:
            st.download_button(
                label="📥 Cadastro Único (CAD)",
                data=to_excel(df_cad),
                file_name="cad_unico_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col18:
            st.download_button(
                label="📥 Novo Bolsa Família",
                data=to_excel(df_bolsa),
                file_name="bolsa_familia_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    # --- EXPANDER DA PÁGINA: EDUCAÇÃO ---
    with st.expander("Dados da Página: Educação"):
        st.subheader("Dados da Educação")
        st.markdown(
            "Dados mensais e anuais de matrículas, rendimento escolar e IDEB por município."
        )

        col_ed_1, col_ed_2 = st.columns(2)
        with col_ed_1:
            st.download_button(
                label="📥 Matrículas por Município",
                data=to_excel(df_educacao_matriculas),
                file_name="educacao_matriculas_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label="📥 Rendimento Escolar (por Município)",
                data=to_excel(df_educacao_rendimento),
                file_name="educacao_rendimento_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with col_ed_2:
            st.download_button(
                label="📥 IDEB por Município",
                data=to_excel(df_educacao_ideb_municipio),
                file_name="educacao_ideb_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label="📥 IDEB por Escola",
                data=to_excel(df_educacao_ideb_escolas),
                file_name="educacao_ideb_escolas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    # --- EXPANDER DA PÁGINA: SAÚDE ---
    with st.expander("Dados da Página: Saúde"):
        st.subheader("Dados da Saúde")
        st.markdown(
            "Dados mensais e anuais de mortalidade, nascimentos, atenção básica, vacinação, médicos e leitos por município."
        )

        # --- DADOS MENSAIS (equivalente ao CAGED) ---
        st.subheader("Dados Mensais")
        st.markdown(
            "Indicadores atualizados mensalmente (ex.: óbitos, nascimentos, atenção básica, internações)."
        )
        col_sd_a, col_sd_b = st.columns(2)

        with col_sd_a:
            st.download_button(
                label="📥 Indicadores Mensais de Saúde",
                data=to_excel(df_saude_mensal),
                file_name=f"saude_indicadores_mensais_{municipio_de_interesse}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_sd_b:
            st.write("")

        st.divider()

        # --- DADOS ANUAIS ---
        st.subheader("Dados Anuais")
        st.markdown(
            "Indicadores com atualização anual (ex.: despesas, imunização agregada, médicos e leitos)."
        )
        col_sd_c, col_sd_d = st.columns(2)

        with col_sd_c:
            st.download_button(
                label="📥 Despesas com Saúde",
                data=to_excel(df_saude_despesas),
                file_name=f"saude_despesas_{municipio_de_interesse}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label="📥 Imunização (Vacinação)",
                data=to_excel(df_saude_vacinas),
                file_name=f"saude_vacinacao_{municipio_de_interesse}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_sd_d:
            st.download_button(
                label="📥 Leitos do SUS",
                data=to_excel(df_saude_leitos),
                file_name=f"saude_leitos_{municipio_de_interesse}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label="📥 Médicos do SUS",
                data=to_excel(df_saude_medicos),
                file_name=f"saude_medicos_{municipio_de_interesse}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.divider()

    # --- EXPANDER DA PÁGINA: PIB ---
    with st.expander("Dados da Página: PIB"):
        st.subheader("Dados do PIB")
        st.markdown("Dados anuais do Produto Interno Bruto municipal (PIB).")

        col_pib_1, col_pib_2 = st.columns(2)

        with col_pib_1:
            st.download_button(
                label="📥 Dados do PIB dos Municípios",
                data=to_excel(df_pib_municipios),
                file_name="pib_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_pib_2:
            st.write("")

        st.divider()

    # --- EXPANDER DA PÁGINA: DEMOGRAFIA ---
    with st.expander("Dados da Página: Demografia"):
        st.subheader("Dados Demográficos")
        st.markdown(
            "Dados anuais de população estimada, proporção por sexo e densidade demográfica por município."
        )

        col_dem_1, col_dem_2 = st.columns(2)

        with col_dem_1:
            st.download_button(
                label="📥 População Estimada por Município",
                data=to_excel(df_populacao_densidade),
                file_name="demografia_populacao_estimada_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.download_button(
                label="📥 Densidade Demográfica por Município",
                data=to_excel(
                    df_populacao_densidade[
                        ["ano", "municipio", "densidade_demografica"]
                    ]
                ),
                file_name="demografia_densidade_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_dem_2:
            st.download_button(
                label="📥 População por Sexo e Faixa Etária",
                data=to_excel(df_populacao_sexo_idade),
                file_name="demografia_sexo_idade_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            st.write("")

        st.divider()

    # --- EXPANDER DA PÁGINA: FINANÇAS ---
    with st.expander("Dados da Página: Finanças"):
        st.subheader("Dados de Finanças Públicas")
        st.markdown(
            "Dados bimestrais e anuais sobre execução orçamentária e indicadores financeiros dos municípios."
        )

        col_fin_1, col_fin_2 = st.columns(2)

        with col_fin_1:
            st.download_button(
                label="📥 Dados Bimestrais de Execução Orçamentária por Município",
                data=to_excel(df_financas),
                file_name="financas_siconfi_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with col_fin_2:
            st.download_button(
                label="📥 Indicadores Financeiros por Município",
                data=to_excel(df_indicadores_financeiros),
                file_name="indicadores_fiscais_municipios.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            if pdf_indicadores:
                try:
                    pdf_indicadores.seek(0)
                except Exception:
                    pass
                st.download_button(
                    label="📥 Relatório Metodológico dos Indicadores Fiscais (PDF)",
                    data=pdf_indicadores,
                    file_name="relatorio_metodologico_financas.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.write("")

        st.divider()
