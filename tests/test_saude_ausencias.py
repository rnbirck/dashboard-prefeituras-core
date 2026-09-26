import pandas as pd
from dashboard_core.views.saude import preparar_dados_graficos_saude_mensal


def test_taxa_preserva_zero_e_nao_imputa_parcela_ausente():
    df=pd.DataFrame({'ano':[2026]*3,'mes':[1,2,3],'municipio':['A']*3,
                     'taxa':[10,0,None],'num':[1,0,None],'den':[10,10,100]})
    hist,acum,_,_,_,ano,mes=preparar_dados_graficos_saude_mensal(
        df,'taxa','ratio',col_numerador='num',col_denominador='den',fator_multiplicacao=100)
    assert (ano,mes)==(2026,2)
    assert hist.loc[pd.Timestamp('2026-02-01'),'A']==0
    assert acum.loc[2026,'A']==5  # 1/20; o denominador sem numerador não entra.
