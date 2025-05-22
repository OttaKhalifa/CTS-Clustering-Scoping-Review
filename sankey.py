

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

def plot_sankey(df, pad, thickness) : 
    df_temp = df[
    ['Community (standardized)', 'Data type (standardized)', 'Method Family', 'Subfamily (standardized)']]

    
    df_temp['Data type (standardized)'] = df_temp['Data type (standardized)'].str.replace(' ', '')
    df_temp['Data type (standardized)'] = df_temp['Data type (standardized)'].str.replace("Caretrajectories", 'Care trajectories')
    df_temp['Data type (standardized)'] = df_temp['Data type (standardized)'].str.split(',')
    df_temp = df_temp.explode('Data type (standardized)')

    valid_methods = ["Model-based", "Feature-based", "Distance-based"]
    df_temp = df_temp[df_temp["Method Family"].isin(valid_methods)]
    df_temp.loc[:,'Subfamily (standardized)'] = df_temp.loc[:,'Subfamily (standardized)'].str.strip()
    ct_1 = pd.DataFrame(df_temp[['Data type (standardized)','Method Family']].value_counts()).reset_index()
    ct_1.columns = ['Source', 'Target', 'Value']
    ct_2 = pd.DataFrame(df_temp[['Method Family','Subfamily (standardized)']].value_counts()).reset_index()
    ct_2.columns = ['Source', 'Target', 'Value']
    ct_1 = ct_1[~ct_1['Source'].isin(valid_methods)]
    ct_2 = ct_2[~ct_2['Target'].isin(valid_methods)]
    ct_all = pd.concat([ct_1, ct_2],axis=0)

    # Suppression des liens où une méthode pointe vers un data type (erreur logique)
    invalid_links = ct_all[
        ct_all['Source'].isin(valid_methods) &
        ct_all['Target'].isin(df_temp['Data type (standardized)'].unique())
    ]

    if not invalid_links.empty:
        print("⚠️ Lien(s) invalides supprimés (méthode pointant vers un data type) :")
        print(invalid_links)

    # Filtrage effectif
    ct_all = ct_all.drop(index=invalid_links.index)
    
    labels_ct = (
    list(df_temp['Data type (standardized)'].unique()) +
    list(df_temp['Method Family'].unique()) +
    list(df_temp['Subfamily (standardized)'].unique())
    )
    labels_ct = unique(labels_ct)
    labels_dict = {j:i for i,j in enumerate(labels_ct)}
    ct_all_coded = ct_all.copy()
    ct_all_coded['Source'] = ct_all_coded['Source'].map(labels_dict)
    ct_all_coded['Target'] = ct_all_coded['Target'].map(labels_dict)

    couleur_fb = [   227, 109, 109   ] #Rouge
    couleur_db = [ 92, 147, 205 ]#Bleu
    couleur_mb = [   80, 185, 112   ] #Jaune

    dico_famille = {"Feature-based" : couleur_fb, "Model-based" : couleur_mb, "Distance-based" : couleur_db}
    label = list(labels_dict.keys())
    for i in range(len(label)) : 
        if label[i] in ["Model-based", "Feature-based", "Distance-based"] : 
            break
            
    couleur = [dico_famille[label[i]], dico_famille[label[i+1]], dico_famille[label[i+2]]]
    order = [label[i], label[i+1], label[i+2]]

    dico_couleurs = {'rgb(27,133,184)' : "Bleu", 'rgb(255,139,148)' : 'Rouge', 'rgb(223,175,44)' : 'Jaune'}

    color_method_family = [f'rgb({couleur[0][0]},{couleur[0][1]},{couleur[0][2]})', f'rgb({couleur[1][0]},{couleur[1][1]},{couleur[1][2]})', f'rgb({couleur[2][0]},{couleur[2][1]},{couleur[2][2]})' ]



    lc = label[0:df_temp['Data type (standardized)'].nunique()]

    color_community = []
    for item in lc:
        line = ct_1[ct_1['Source'] == item]

        color = []
        for family in order : 
            if family in line['Target'].values:
                a = line[line['Target'] == family]["Value"]
                color.append(int(a))
            else : 
                color.append(0)
        i = color.index(max(color))
        col = color_method_family[i]

        color_community.append(col)

    color_subfamily =  []
    rc = label[df_temp['Data type (standardized)'].nunique() + df_temp['Method Family'].nunique():]

    for item in rc:
        line = ct_2[ct_2['Target'] == item]

        db = 0
        fb = 0
        mb = 0
        
        color = []
        for family in order : 
            if family in line['Source'].values:
                a = line[line['Source'] == family]["Value"]
                color.append(int(a))
            else : 
                color.append(0)
        i = color.index(max(color))
        col = color_method_family[i]
        color_subfamily.append(col)

    color_all = color_community + color_method_family + color_subfamily

    source = ct_all_coded['Source']



    target = ct_all_coded['Target']
    value = ct_all_coded['Value']

    # Détection des liens anormaux (droite -> gauche)
    wrong_links = ct_all_coded[ct_all_coded['Source'] > ct_all_coded['Target']]
    if not wrong_links.empty:
        print("Lien(s) problématique(s) détecté(s) (source > target) :")
        print(wrong_links.merge(pd.DataFrame({'id': list(labels_dict.values()), 'label': list(labels_dict.keys())}), left_on='Source', right_on='id')
                        .merge(pd.DataFrame({'id': list(labels_dict.values()), 'label': list(labels_dict.keys())}), left_on='Target', right_on='id', suffixes=('_source', '_target')))
    else:
        print("Aucun lien source > target détecté.")
    links = dict(source = source, target = target, value = value)
    nodes = dict(label = label, pad=pad, thickness=thickness, color=color_all)

    data = go.Sankey(link = links, node=nodes,textfont={'size':25, 'color': '#2A4B9B'})

    # plot
    height= 1000
    width = 1600
    #fig = go.Figure(data, layout = dict(height=500, width=1000))
    fig = go.Figure(data, layout = dict(height=height, width=width))
    return(fig.to_html(include_plotlyjs='cdn'))
    #fig.show()

    
    
    #fig = go.Figure(data, layout = dict(height=1000, width=2500))
