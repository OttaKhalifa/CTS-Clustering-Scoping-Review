import streamlit as st
import pandas as pd
import numpy as np
import io  # Pour créer un fichier temporaire en mémoire

# Configuration de la page
st.set_page_config(
    page_title="Categorical Sequence Clustering Methods",
    page_icon="📊",
    layout="wide"
)

# Titre principal dans la zone principale
st.title("Categorical Sequence Clustering Methods : a scoping review")
st.markdown("An interactive tool to find the best method for your categorical sequence clustering needs.")

# Fonction pour formater l'année sans décimale
def format_year(year_value):
    if pd.isna(year_value):
        return "N/A"
    try:
        # Essayer de convertir en nombre et formater sans décimale
        return f"{float(year_value):.0f}"
    except:
        # Si échec, retourner la valeur originale
        return str(year_value)

# Fonction pour charger les données
@st.cache_data
def load_data():
    try:
        data = pd.read_excel('data.xlsx')
        # Prétraitement de la colonne "Public Implementation"
        if 'Public Implementation' in data.columns:
            # Séparer "Yes (lien)" en "Yes" et le lien, et "No" reste tel quel
            data[['Public Implementation Available', 'Implementation Link']] = data['Public Implementation'].str.extract(r'(Yes|No)(?: \((.*)\))?')
            data['Implementation Link'] = data['Implementation Link'].fillna("None")
            data['Implementation Link'] = data['Implementation Link'].apply(lambda x: np.nan if x == '' else x)
        return data, True, None
    except FileNotFoundError:
        return pd.DataFrame(), False, "Le fichier 'Data.xlsx' n'a pas été trouvé. Veuillez vérifier le chemin."
    except Exception as e:
        return pd.DataFrame(), False, f"Erreur lors du chargement des données : {e}"

# Charger les données
data, success, error_message = load_data()

# SIDEBAR: Contrôles de filtrage
with st.sidebar:
    st.header("Filters")
    
    # Afficher un message d'erreur si le chargement a échoué
    if not success:
        st.error(error_message)
    else:
        st.success("Data are loaded !")
        
        st.subheader("Select Your Data Properties")
        
        # Définir les critères de sélection et les questions correspondantes
        criteria = {
            "Continuous time": "Is the temporal scale **continuous**?",
            "Covariates": "Are there time-invariant covariates?",
            "Various lengths": "Are your sequences from various lengths?",
            "Missing data": "Do you have missing data?",
            "Multivariate": "Are your time series multivariate?",
            "Public Implementation Available": "Do you need a public implementation?"
        }

        # Initialiser la condition à True pour inclure toutes les données au départ
        condition = pd.Series([True] * len(data))
        selected_filters = {}

        # Créer un filtre pour chaque critère
        for col, question in criteria.items():
            if col in data.columns:
                # Ajouter une case à cocher
                selected_filters[col] = st.checkbox(question)
                if selected_filters[col]:
                    # Si la case est cochée, appliquer le filtre pour "Yes"
                    condition &= (data[col] == "Yes")

        # Ajouter le filtre pour "Data type (standardized)"
        if "Data type (standardized)" in data.columns:
            st.subheader("Data Type")
            # Extraire tous les types uniques en les décomposant par virgule
            all_data_types = set(
                word.strip() 
                for types in data["Data type (standardized)"].dropna() 
                for word in types.split(',')
            )
            data_type_options = ["No preference"] + sorted(all_data_types)
            
            selected_data_type = st.selectbox(
                "Select data type for your sequences:", 
                data_type_options
            )

            # Filtrer les données pour inclure les articles correspondant au type sélectionné
            if selected_data_type != "No preference":
                condition &= data["Data type (standardized)"].apply(
                    lambda x: selected_data_type in x if pd.notna(x) else False
                )

# MAIN CONTENT AREA
# Filtrer les données selon les critères
if success:
    filtered_data = data[condition]
    
    # Créer des onglets pour différentes vues
    tab1, tab2 = st.tabs(["📋 Methods", "📊 Raw Data"])
    
    with tab1:
        # Entête résumant les résultats
        results_col1, results_col2 = st.columns([2, 1])
        with results_col1:
            st.subheader(f"{len(filtered_data)} methods found based on your criteria")
        
        with results_col2:
            # Ajouter un bouton de téléchargement pour le sous-fichier filtré
            if not filtered_data.empty:
                # Créer un fichier Excel en mémoire
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    filtered_data.to_excel(writer, index=False, sheet_name="Filtered Data")
                output.seek(0)

                # Ajouter le bouton de téléchargement
                st.download_button(
                    label="📥 Download Results as Excel",
                    data=output,
                    file_name="filtered_methods.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        
        # Si aucun résultat ne correspond aux critères
        if filtered_data.empty:
            st.info("No methods match your selected criteria. Try changing your filters.")
        else:
            # Grouper les données par "Method Family"
            if "Method Family" in filtered_data.columns:
                # Obtenir les familles de méthodes uniques
                method_families = filtered_data["Method Family"].dropna().unique()
                
                # Afficher les articles regroupés par famille de méthode
                for family in method_families:
                    # Créer un sous-ensemble pour la famille actuelle
                    family_data = filtered_data[filtered_data["Method Family"] == family]
                    
                    # Utiliser un expander pour chaque famille de méthode, fermé par défaut
                    with st.expander(f"🔹 {family} Methods ({len(family_data)})", expanded=False):
                        # Afficher les articles de cette famille
                        for index, row in family_data.iterrows():
                            # Diviser l'affichage en deux colonnes
                            col1, col2 = st.columns([1, 3])
                            
                            with col1:
                                # Utiliser Method Name comme en-tête au lieu de Original Article
                                if 'Method Name' in row and pd.notna(row['Method Name']):
                                    method_title = row['Method Name']
                                else:
                                    # Fallback sur Original Article si Method Name n'existe pas ou est vide
                                    method_title = row['Original Article'] if 'Original Article' in row else f"Method {index}"
                                
                                st.markdown(f"📄 **{method_title}**")
                                
                                # Ajouter année et communauté comme texte avec année formatée
                                year_display = format_year(row['Year']) if 'Year' in row else "N/A"
                                community = row['Community (standardized)'] if 'Community (standardized)' in row and pd.notna(row['Community (standardized)']) else "Other"
                                
                                st.markdown(f"Year: **{year_display}** | Community: **{community}**")
                                
                                # Ajouter des indicateurs pour les propriétés clés
                                properties = []
                                for prop in ["Continuous time", "Covariates", "Various lengths", "Missing data", "Multivariate"]:
                                    if prop in row and row[prop] == "Yes":
                                        properties.append(prop)
                                
                                if properties:
                                    st.markdown("**Key properties**: " + ", ".join(properties))

                            with col2:
                                # Afficher les détails de l'article directement
                                st.markdown("#### Method Details")
                                st.markdown(f"**Original Article**: {row['Original Article']}")
                                st.markdown(f"**Published in**: {row['Publication name']}")
                                st.markdown(f"**Applied in**: {row['Article found']}")
                                
                                # Rendre les liens cliquables
                                if 'Link' in row and pd.notna(row['Link']):
                                    st.markdown(f"**Article link**: [{row['Link']}]({row['Link']})")
                                
                                if 'Implementation Link' in row and pd.notna(row['Implementation Link']) and row['Implementation Link'] != "None":
                                    st.markdown(f"**Implementation link**: [{row['Implementation Link']}]({row['Implementation Link']})")
                                elif 'Public Implementation Available' in row and row['Public Implementation Available'] == "No":
                                    st.markdown("**Implementation**: Not publicly available")
                                
                                if 'Comments' in row and pd.notna(row['Comments']):
                                    st.markdown(f"**Comments**: {row['Comments']}")
                            
                            # Ligne séparatrice entre les méthodes
                            st.markdown("---")
            else:
                # Si la colonne Method Family n'existe pas
                st.warning("La colonne 'Method Family' n'existe pas dans les données.")
                # Afficher les résultats sans regroupement
                st.subheader("Methods")
                
                for index, row in filtered_data.iterrows():
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        # Utiliser Method Name comme en-tête au lieu de Original Article
                        if 'Method Name' in row and pd.notna(row['Method Name']):
                            method_title = row['Method Name']
                        else:
                            # Fallback sur Original Article si Method Name n'existe pas ou est vide
                            method_title = row['Original Article'] if 'Original Article' in row else f"Method {index}"
                        
                        st.markdown(f"📄 **{method_title}**")
                        
                        # Ajouter année et communauté comme texte avec année formatée
                        year_display = format_year(row['Year']) if 'Year' in row else "N/A"
                        community = row['Community (standardized)'] if 'Community (standardized)' in row and pd.notna(row['Community (standardized)']) else "Other"
                        
                        st.markdown(f"Year: **{year_display}** | Community: **{community}**")

                    with col2:
                        # Afficher les détails de l'article directement
                        st.markdown("#### Method Details")
                        st.markdown(f"**Original Article**: {row['Original Article']}")
                        st.markdown(f"**Published in**: {row['Publication name'] if 'Publication name' in row else 'N/A'}")
                        if 'Method Family' in row:
                            st.markdown(f"**Family Method**: {row['Method Family']}")
                        st.markdown(f"**Applied in**: {row['Article found'] if 'Article found' in row else 'N/A'}")
                        st.markdown(f"**Data Type**: {row['Data type (standardized)'] if 'Data type (standardized)' in row else 'N/A'}")
                        
                        # Rendre les liens cliquables
                        if 'Link' in row and pd.notna(row['Link']):
                            st.markdown(f"**Article link**: [{row['Link']}]({row['Link']})")
                        
                        if 'Implementation Link' in row and pd.notna(row['Implementation Link']) and row['Implementation Link'] != "None":
                            st.markdown(f"**Implementation link**: [{row['Implementation Link']}]({row['Implementation Link']})")
                        
                        if 'Comments' in row and pd.notna(row['Comments']):
                            st.markdown(f"**Comments**: {row['Comments']}")
                    
                    # Ligne séparatrice entre les méthodes
                    st.markdown("---")
    
    with tab2:
        # Afficher le tableau de données brutes avec des options de tri
        st.subheader("Raw Data Table")
        st.write("Full dataset with all columns. Use the column headers to sort.")
        st.dataframe(data)
