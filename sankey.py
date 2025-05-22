import pandas as pd
import plotly
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
from matplotlib.patches import Patch
import kaleido
import plotly.io as pio
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import seaborn as sns
import numpy as np

pio.kaleido.scope.default_format = "svg"

def unique(list1):
 
    # initialize a null list
    unique_list = []
 
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

def plot_sankey(df, pad=10, thickness=20, height = 500, width = 1000):
    df_temp = df[['Community (standardized)', 'Data type (standardized)', 'Method Family', 'Subfamily (standardized)']].copy()

    df_temp['Data type (standardized)'] = df_temp['Data type (standardized)'].str.replace(' ', '')
    df_temp['Data type (standardized)'] = df_temp['Data type (standardized)'].str.replace("Caretrajectories", 'Care trajectories')
    df_temp['Data type (standardized)'] = df_temp['Data type (standardized)'].str.split(',')
    df_temp = df_temp.explode('Data type (standardized)')

    valid_methods = ["Model-based", "Feature-based", "Distance-based"]
    df_temp = df_temp[df_temp["Method Family"].isin(valid_methods)]
    df_temp['Subfamily (standardized)'] = df_temp['Subfamily (standardized)'].str.strip()

    ct_1 = df_temp[['Data type (standardized)', 'Method Family']].value_counts().reset_index()
    ct_1.columns = ['Source', 'Target', 'Value']
    ct_2 = df_temp[['Method Family', 'Subfamily (standardized)']].value_counts().reset_index()
    ct_2.columns = ['Source', 'Target', 'Value']
    ct_1 = ct_1[~ct_1['Source'].isin(valid_methods)]
    ct_2 = ct_2[~ct_2['Target'].isin(valid_methods)]
    ct_all = pd.concat([ct_1, ct_2], axis=0)

    # Nettoyage logique
    ct_all = ct_all[~(
        ct_all['Source'].isin(valid_methods) &
        ct_all['Target'].isin(df_temp['Data type (standardized)'].unique())
    )]

    labels_ct = unique(list(ct_all['Source']) + list(ct_all['Target']))
    labels_dict = {j: i for i, j in enumerate(labels_ct)}

    ct_all_coded = ct_all.copy()
    ct_all_coded['Source'] = ct_all_coded['Source'].map(labels_dict)
    ct_all_coded['Target'] = ct_all_coded['Target'].map(labels_dict)

    # Définition des couleurs
    dico_famille = {
        "Feature-based": [227, 109, 109],
        "Model-based": [80, 185, 112],
        "Distance-based": [92, 147, 205]
    }
    color_method_family = {k: f'rgb({v[0]},{v[1]},{v[2]})' for k, v in dico_famille.items()}

    # Color map par label
    color_map = {}
    for item in df_temp['Data type (standardized)'].unique():
        line = ct_1[ct_1['Source'] == item]
        scores = [(int(line[line['Target'] == fam]['Value']) if fam in line['Target'].values else 0, fam) for fam in valid_methods]
        dominant_family = max(scores)[1]
        color_map[item] = color_method_family[dominant_family]

    for item in df_temp['Subfamily (standardized)'].unique():
        line = ct_2[ct_2['Target'] == item]
        scores = [(int(line[line['Source'] == fam]['Value']) if fam in line['Source'].values else 0, fam) for fam in valid_methods]
        dominant_family = max(scores)[1]
        color_map[item] = color_method_family[dominant_family]

    for fam in valid_methods:
        color_map[fam] = color_method_family[fam]

    label = list(labels_dict.keys())
    color_all = [color_map.get(lbl, 'rgb(200,200,200)') for lbl in label]

    # Debug éventuel
    wrong_links = ct_all_coded[ct_all_coded['Source'] > ct_all_coded['Target']]
    if not wrong_links.empty:
        print("Lien(s) problématique(s) détecté(s) (source > target) :")
        print(
            wrong_links
            .merge(pd.DataFrame({'id': list(labels_dict.values()), 'label': list(labels_dict.keys())}),
                   left_on='Source', right_on='id')
            .merge(pd.DataFrame({'id': list(labels_dict.values()), 'label': list(labels_dict.keys())}),
                   left_on='Target', right_on='id', suffixes=('_source', '_target'))
        )

    # Construction Sankey
    source = ct_all_coded['Source']
    target = ct_all_coded['Target']
    value = ct_all_coded['Value']

    links = dict(source=source, target=target, value=value)
    nodes = dict(label=label, pad=pad, thickness=thickness, color=color_all)
    data = go.Sankey(link=links, node=nodes, textfont={'size': 25, 'color': '#2A4B9B'})

    fig = go.Figure(data, layout=dict(height=height, width=width))
    return fig.to_html(include_plotlyjs='cdn')
