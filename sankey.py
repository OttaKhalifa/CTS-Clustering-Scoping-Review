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

def plot_sankey(df, pad, thickness):
    df_temp = df[
        ['Community (standardized)', 'Data type (standardized)', 'Method Family', 'Subfamily (standardized)']
    ].copy()

    df_temp['Data type (standardized)'] = df_temp['Data type (standardized)'].str.replace(' ', '')
    df_temp['Data type (standardized)'] = df_temp['Data type (standardized)'].str.replace("Caretrajectories", 'Care trajectories')
    df_temp['Data type (standardized)'] = df_temp['Data type (standardized)'].str.split(',')
    df_temp = df_temp.explode('Data type (standardized)')

    valid_methods = ["Model-based", "Feature-based", "Distance-based"]
    df_temp = df_temp[df_temp["Method Family"].isin(valid_methods)]
    df_temp['Subfamily (standardized)'] = df_temp['Subfamily (standardized)'].str.strip()

    ct_1 = pd.DataFrame(df_temp[['Data type (standardized)', 'Method Family']].value_counts()).reset_index()
    ct_1.columns = ['Source', 'Target', 'Value']
    ct_2 = pd.DataFrame(df_temp[['Method Family', 'Subfamily (standardized)']].value_counts()).reset_index()
    ct_2.columns = ['Source', 'Target', 'Value']

    ct_1 = ct_1[~ct_1['Source'].isin(valid_methods)]
    ct_2 = ct_2[~ct_2['Target'].isin(valid_methods)]
    ct_all = pd.concat([ct_1, ct_2], axis=0)

    # Suppression des liens inversés (méthode > data type)
    invalid_links = ct_all[
        ct_all['Source'].isin(valid_methods) &
        ct_all['Target'].isin(df_temp['Data type (standardized)'].unique())
    ]
    ct_all = ct_all.drop(index=invalid_links.index)

    # Construction dynamique des labels
    labels_ct = (
        list(df_temp['Data type (standardized)'].unique()) +
        list(df_temp['Method Family'].unique()) +
        list(df_temp['Subfamily (standardized)'].unique())
    )
    labels_ct = unique(labels_ct)
    labels_dict = {j: i for i, j in enumerate(labels_ct)}
    label = list(labels_dict.keys())

    ct_all_coded = ct_all.copy()
    ct_all_coded['Source'] = ct_all_coded['Source'].map(labels_dict)
    ct_all_coded['Target'] = ct_all_coded['Target'].map(labels_dict)

    # Couleurs
    couleur_fb = [227, 109, 109]     # Rouge
    couleur_db = [92, 147, 205]      # Bleu
    couleur_mb = [80, 185, 112]      # Vert

    dico_famille = {
        "Feature-based": couleur_fb,
        "Model-based": couleur_mb,
        "Distance-based": couleur_db
    }

    # Détection des méthodes présentes
    order = [m for m in valid_methods if m in label]
    couleur = [dico_famille[m] for m in order]
    color_method_family = [f'rgb({c[0]},{c[1]},{c[2]})' for c in couleur]

    # Détection des sous-ensembles
    dt_unique = df_temp['Data type (standardized)'].unique()
    sf_unique = df_temp['Subfamily (standardized)'].unique()

    lc = [l for l in label if l in dt_unique]
    rc = [l for l in label if l in sf_unique]

    # Couleurs pour les data types
    color_community = []
    for item in lc:
        line = ct_1[ct_1['Source'] == item]
        color = []
        for fam in order:
            a = line[line['Target'] == fam]["Value"]
            color.append(int(a) if not a.empty else 0)
        if any(color):
            i = color.index(max(color))
            col = color_method_family[i]
        else:
            col = "rgb(150,150,150)"
        color_community.append(col)

    # Couleurs pour les subfamilies
    color_subfamily = []
    for item in rc:
        line = ct_2[ct_2['Target'] == item]
        color = []
        for fam in order:
            a = line[line['Source'] == fam]["Value"]
            color.append(int(a) if not a.empty else 0)
        if any(color):
            i = color.index(max(color))
            col = color_method_family[i]
        else:
            col = "rgb(150,150,150)"
        color_subfamily.append(col)

    # Couleurs finales
    color_all = color_community + color_method_family + color_subfamily

    # Sankey data
    source = ct_all_coded['Source']
    target = ct_all_coded['Target']
    value = ct_all_coded['Value']

    # Sanity check liens inversés
    wrong_links = ct_all_coded[ct_all_coded['Source'] > ct_all_coded['Target']]
    if not wrong_links.empty:
        print("Lien(s) problématique(s) détecté(s) (source > target) :")
        print(wrong_links.merge(pd.DataFrame({'id': list(labels_dict.values()), 'label': list(labels_dict.keys())}), left_on='Source', right_on='id')
                        .merge(pd.DataFrame({'id': list(labels_dict.values()), 'label': list(labels_dict.keys())}), left_on='Target', right_on='id', suffixes=('_source', '_target')))
    else:
        print("✅ Aucun lien source > target détecté.")

    links = dict(source=source, target=target, value=value)
    nodes = dict(label=label, pad=pad, thickness=thickness, color=color_all)

    data = go.Sankey(link=links, node=nodes, textfont={'size': 25, 'color': '#2A4B9B'})
    fig = go.Figure(data, layout=dict(height=1000, width=1600))
    return fig.to_html(include_plotlyjs='cdn')
