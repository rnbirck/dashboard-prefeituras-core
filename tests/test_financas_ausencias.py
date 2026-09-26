import pandas as pd
from dashboard_core.views.financas import (
    preparar_dados_grafico_indicador_financeiros, preparar_dados_graficos_siconfi,
)


def test_indicador_indefinido_nao_vira_zero_na_comparacao_municipal():
    df=pd.DataFrame({'ano':[2024,2024,2025,2025],'municipio':['A','B']*2,
                     'indicador':[1,0,None,5]})
    r=preparar_dados_grafico_indicador_financeiros(df,'indicador')
    assert pd.isna(r.loc[2025,'A'])
    assert r.loc[2024,'B']==0


def test_bimestre_nao_entregue_nao_vira_receita_zero():
    df=pd.DataFrame({'ano':[2026]*3,'bimestre':[3,3,4],'municipio':['A','B','B'],
                     'cod_conta':['X']*3,'coluna':['No Bimestre (b)']*3,
                     'valor':[1000000,0,2000000]})
    historico,*_=preparar_dados_graficos_siconfi(df,'X',[2026])
    assert pd.isna(historico.iloc[-1]['A'])
    assert historico.iloc[-1]['B']==2
    assert historico.iloc[0]['B']==0
