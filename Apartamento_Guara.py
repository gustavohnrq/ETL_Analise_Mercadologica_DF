import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

def remover_outliers_iqr(df, coluna):
    Q1 = df[coluna].quantile(0.25)
    Q3 = df[coluna].quantile(0.75)
    IQR = Q3 - Q1
    filtro = (df[coluna] >= (Q1 - 1.5 * IQR)) & (df[coluna] <= (Q3 + 1.5 * IQR))
    return df[filtro]

def selecionar_clusters(df_filtrado, valor_coluna, cluster_means, ordered_clusters):
    semi_reformado_idx = len(ordered_clusters) // 2
    semi_reformado_cluster = ordered_clusters[semi_reformado_idx]
    semi_reformado_value = cluster_means[semi_reformado_cluster]

    original_cluster = None
    reformado_cluster = None

    for cluster in ordered_clusters:
        if cluster_means[cluster] <= semi_reformado_value * 0.90:
            original_cluster = cluster
        if cluster_means[cluster] >= semi_reformado_value * 1.10 and reformado_cluster is None:
            reformado_cluster = cluster

    if original_cluster is None:
        original_cluster = ordered_clusters[0]
    if reformado_cluster is None:
        reformado_cluster = ordered_clusters[-1]

    return {
        original_cluster: 'Original',
        semi_reformado_cluster: 'Semi-Reformado',
        reformado_cluster: 'Reformado'
    }

def grupos_metragem_quartos(df, tipo_imovel):
    if tipo_imovel == "Apartamento":
        metragem_bins = [0, 50, 75, 90, 130, 160, 200, np.inf]
        metragem_labels = ["<50", "50-75", "75-90", "90-130", "130-160", "160-200", ">200"]
        quartos_bins = [0, 1, 2, 3, 4, np.inf]
        quartos_labels = ["1", "2", "3", "4", "+5"]
    else:
        metragem_bins = [0, 400, 600, 800, 1000, np.inf]
        metragem_labels = ["<400", "400-600", "600-800", "800-1000", ">1000"]
        quartos_bins = [0, 4, np.inf]
        quartos_labels = ["Até 4", "5 ou mais"]

    df["grupo_metragem"] = pd.cut(df["area_util"], bins=metragem_bins, labels=metragem_labels)
    df["quartos_group"] = pd.cut(df["quartos"], bins=quartos_bins, labels=quartos_labels)

def analisar_imovel_detalhado(df, oferta, tipo_imovel=None, bairro=None, cidade=None, cep=None, quadra=None):
    resultados_finais = []

    for vaga_status, df_vaga in df.groupby(df["vagas"].notnull()):
        vaga_status_str = "Com Vaga" if vaga_status else "Sem Vaga"
        
        filtro = (df_vaga["oferta"] == oferta)
        if tipo_imovel:
            filtro &= (df_vaga["tipo"] == tipo_imovel)
        if bairro:
            filtro &= (df_vaga["bairro"] == bairro)
        if cidade:
            filtro &= (df_vaga["cidade"] == cidade)
        if cep:
            filtro &= (df_vaga["cep"] == cep)
        if quadra:
            filtro &= (df_vaga["quadra"] == quadra)

        df_filtrado = df_vaga[filtro]

        valor_coluna = "valor_m2" if tipo_imovel == "Apartamento" else "preco"

        if valor_coluna in df_filtrado.columns:
            df_filtrado = remover_outliers_iqr(df_filtrado, valor_coluna)

        if not df_filtrado.empty and valor_coluna in df_filtrado.columns and len(df_filtrado) >= 9:
            X = df_filtrado[[valor_coluna]].values
            kmeans = KMeans(n_clusters=9, random_state=42, n_init=10)
            df_filtrado["cluster"] = kmeans.fit_predict(X)
            df_filtrado['cluster'] = df_filtrado['cluster'].astype('category')

            cluster_means = df_filtrado.groupby('cluster')[valor_coluna].mean().sort_values()
            ordered_clusters = cluster_means.index.tolist()

            cluster_labels = selecionar_clusters(df_filtrado, valor_coluna, cluster_means, ordered_clusters)
            df_filtrado['cluster_nomeado'] = df_filtrado['cluster'].map(cluster_labels).dropna()

            media_clusters = df_filtrado.groupby('cluster_nomeado').agg(
                Valor=(valor_coluna, 'mean'),
                AmostraAnalisada=('cluster_nomeado', 'size')
            ).reset_index().assign(NomeMedia=lambda x: x['cluster_nomeado'])
        else:
            media_clusters = pd.DataFrame(columns=['NomeMedia', 'Valor', 'AmostraAnalisada'])

        grupos_metragem_quartos(df_filtrado, tipo_imovel)

        media_metragem = df_filtrado.groupby('grupo_metragem').agg(
            Valor=(valor_coluna, 'mean'),
            AmostraAnalisada=('grupo_metragem', 'size')
        ).reset_index().assign(NomeMedia=lambda x: x['grupo_metragem'].apply(lambda y: f'Metragem {y}'))
        media_quartos = df_filtrado.groupby('quartos_group').agg(
            Valor=(valor_coluna, 'mean'),
            AmostraAnalisada=('quartos_group', 'size')
        ).reset_index().assign(NomeMedia=lambda x: x['quartos_group'].apply(lambda y: f'Quartos {y}'))

        if 'bairro' in df_filtrado.columns:
            media_bairros = df_filtrado.groupby('bairro').agg(
                Valor=(valor_coluna, 'mean'),
                AmostraAnalisada=('bairro', 'size')
            ).reset_index().assign(NomeMedia=lambda x: x['bairro'].apply(lambda y: f'Bairro {y}'))
        else:
            media_bairros = pd.DataFrame(columns=['NomeMedia', 'Valor', 'AmostraAnalisada'])

        if 'quadra' in df_filtrado.columns:
            media_quadras = df_filtrado.groupby('quadra').agg(
                Valor=(valor_coluna, 'mean'),
                AmostraAnalisada=('quadra', 'size')
            ).reset_index().assign(NomeMedia=lambda x: x['quadra'].apply(lambda y: f'Quadra {y}'))
        else:
            media_quadras = pd.DataFrame(columns=['NomeMedia', 'Valor', 'AmostraAnalisada'])

        if 'cep' in df_filtrado.columns:
            media_ceps = df_filtrado.groupby('cep').agg(
                Valor=(valor_coluna, 'mean'),
                AmostraAnalisada=('cep', 'size')
            ).reset_index().assign(NomeMedia=lambda x: x['cep'].apply(lambda y: f'CEP {y}'))
        else:
            media_ceps = pd.DataFrame(columns=['NomeMedia', 'Valor', 'AmostraAnalisada'])

        resultados = pd.concat([media_clusters, media_metragem, media_quartos, media_bairros, media_quadras, media_ceps], ignore_index=True)
        resultados['Vaga'] = vaga_status_str

        resultados_finais.append(resultados)

    resultados_final = pd.concat(resultados_finais, ignore_index=True)
    return resultados_final[['NomeMedia', 'Vaga', 'Valor', 'AmostraAnalisada']]

def salvar_no_google_sheets(resultados, spreadsheet_id, range_name, credentials_json):
    credentials = service_account.Credentials.from_service_account_info(json.loads(credentials_json))
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    resultados = resultados.fillna(0)

    if 'Data' in resultados.columns:
        resultados['Data'] = resultados['Data'].astype(str)

    valores = resultados.values.tolist()
    cabecalho = resultados.columns.tolist()

    corpo_requisicao = {
        'values': [cabecalho] + valores
    }

    request = sheet.values().update(spreadsheetId=spreadsheet_id, range=range_name, valueInputOption='RAW', body=corpo_requisicao)
    response = request.execute()
    print(f"{response.get('updatedCells')} células atualizadas.")

input_file = "/Users/macbook/Downloads/BaseEstudos.csv"
credentials_json = '/Users/macbook/Documents/Cod_ETL_estudos/credentiasl_machome.json'
spreadsheet_id = '1oyKvXEcOe5jJITxH4EHe4xOmVp-uT_5XIRvuXQe-Esw'
range_name = 'Apartamento_Guara!A1'

df = pd.read_csv(input_file, sep=",", thousands=".", decimal=",")
df['Data'] = pd.to_datetime(df['Data'], format='%Y-%m-%d')

resultados_por_data = []

for data in df['Data'].unique():
    df_filtrado_por_data = df[df['Data'] == data]
    resultados_detalhados = analisar_imovel_detalhado(
        df=df_filtrado_por_data,
        oferta="Venda",
        tipo_imovel="Apartamento",
        bairro=None,
        cidade="GUARA",
        cep=None,
        quadra=None)
    resultados_detalhados['Data'] = data
    resultados_por_data.append(resultados_detalhados)

resultados_finais = pd.concat(resultados_por_data, ignore_index=True)

with open(credentials_json) as f:
    credentials_info = f.read()
salvar_no_google_sheets(resultados_finais, spreadsheet_id, range_name, credentials_info)

