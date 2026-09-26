import numpy as np
import pandas as pd

from dashboard_core.views.pib import preparar_dados_graficos_pib


def test_serie_nao_converte_ausencia_ou_variacao_indefinida_em_zero():
    fonte = pd.DataFrame({'ano':[2021,2021,2022,2022], 'municipio':['A','B','A','B'],
                          'pib':[0,10,np.nan,20]})
    resultado = preparar_dados_graficos_pib(fonte,'municipio','pib')
    assert resultado.loc['2021','A'] == 0
    assert pd.isna(resultado.loc['2022','A'])
    assert resultado.loc['2022','B'] == 20
