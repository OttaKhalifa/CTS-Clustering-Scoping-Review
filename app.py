import streamlit as st
import pandas as pd
import numpy as np
import io
import streamlit.components.v1 as components
from sankey import plot_sankey

# =========================
# Config & constantes
# =========================
st.set_page_config(
    page_title="Categorical Sequence Clustering Methods",
    page_icon="📊",
    layout="wide"
)

SANKEY_WIDTH = 1200   # doit matcher la largeur de sortie HTML
SANKEY_HEIGHT = 900   # doit matcher la hauteur de sortie HTML
SANKEY_PAD = 20
SANKEY_THICKNESS = 20

# =========================
# Titre
# =========================
st.title("Clustering Methods for Categorical Time Series : a scoping review")
st.markdown("An interactive tool to find the best method for your Categorical Time Series clustering needs.")

# =========================
# Utils
# =========================
def format_year(year_value):
    if pd.isna(year_value):
        return "N/A"
    try:
        return f"{float(year_value):.0f}"
    except Exception:
        return str(year_value)

def process_dependency_order(value):
    if isinstance(value, str) and value.isdigit():
        return f"${value}$"
    elif isinstance(value, int):
        return f"${value}$"
    elif isinstance(value, float) and value.is_integer():
        return f"${int(value)}$"
    elif value == "All":
        return "$\\infty$"
    elif value == "Fixed":
        return "User"
    else:
        return value

# =========================
# Data
# =========================
@st.cache_data
def load_data():
    try:
        data = pd.read_excel('data.xlsx')
        # Prétraitement de "Public Implementation"
        if 'Public Implementation' in data.columns:
            extracted = data['Public Implementation'].astype(str).str.extract(r'(Yes|No)(?: \((.*)\))?')
            extracted.columns = ['Public Implementation Available', 'Implementation Link']
            data[['Public Implementation Available', 'Implementation Link']] = extracted
            data['Implementation Link'] = data['Implementation Link'].replace({"": np.nan, "None": np.nan})
        return data, True, None
    except FileNotFoundError:
        return pd.DataFrame(), False, "Le fichier 'data.xlsx' n'a pas été trouvé. Veuillez vérifier le chemin."
    except Exception as e:
        return pd.DataFrame(), False, f"Erreur lors du chargement des données : {e}"

# =========================
# Sankey (HTML) — clé de cache dépend des dimensions
# =========================
@st.cache_data
def generate_sankey_html(data, width, height, pad, thickness):
    """
    Génère le HTML du Sankey plot à partir des données filtrées.
    IMPORTANT : width/height/pad/thickness inclus dans la clé de cache.
    """
    return plot_sankey(
        data,
        pad=pad,
        thickness=thickness,
        height=height,
        width=width
    )

# =========================
# Affichage d'une méthode
# =========================
def display_method(row, index):
    method_name = (
        row['Method Name'] if 'Method Name' in row and pd.notna(row['Method Name'])
        else (row['Original Article'] if 'Original Article' in row else f"Method {index}")
    )

    icons = {
        "Engineering": "⚙️",
        "Biology": "🧬",
        "Social Science": "👥",
        "Statistics": "📊",
        "Artificial Intelligence": "🤖",
        "Healthcare": "🩺",
        "Computer Science": "💻",
        "Mathematics": "🔢",
        "Other": "📋"
    }

    community = row['Community (standardized)'] if 'Community (standardized)' in row and pd.notna(row['Community (standardized)']) else "Other"

    icon = icons["Other"]
    for key in icons:
        if isinstance(community, str) and key in community:
            icon = icons[key]
            break

    st.markdown(f"## {icon} {method_name}")

    col1, col2 = st.columns([1, 3])

    with col1:
        year_display = format_year(row['Year']) if 'Year' in row else "N/A"
        subfamily = row['Subfamily (standardized)'] if 'Subfamily (standardized)' in row and pd.notna(row['Subfamily (standardized)']) else "None"
        main_algorithm = row['Main Algorithm (standardized)'] if 'Main Algorithm (standardized)' in row and pd.notna(row['Main Algorithm (standardized)']) else "None"

        st.markdown(f"**Year**: {year_display}")
        st.markdown(f"**Community**: {community}")
        st.markdown(f"**Subfamily**: {subfamily}")
        st.markdown(f"**Main Algorithm**: {main_algorithm}")

        if 'Dependency order' in row and pd.notna(row['Dependency order']):
            formatted_dependency = process_dependency_order(row['Dependency order'])
            st.markdown(f"**Dependency order**: {formatted_dependency}")
        else:
            st.markdown("**Dependency order**: N/A")

        properties = []
        for prop in ["Continuous time", "Covariates", "Various lengths", "Missing data", "Multivariate"]:
            if prop in row and row[prop] == "Yes":
                properties.append(prop)

        if properties:
            st.markdown("**Key properties**: " + ", ".join(properties))
        else:
            st.markdown("**Key properties**: None")

        if 'Data type (standardized)' in row and pd.notna(row['Data type (standardized)']):
            st.markdown(f"**Data Type**: {row['Data type (standardized)']}")

    with col2:
        st.markdown(f"**Original Article**: {row.get('Original Article', 'N/A')}")
        st.markdown(f"**Published in**: {row.get('Publication name', 'N/A')}")

        if 'Method Family' in row and not st.session_state.get('in_family_expander', False):
            st.markdown(f"**Family Method**: {row['Method Family']}")

        st.markdown(f"**Applied in**: {row.get('Article found', 'N/A')}")

        if 'Link' in row and pd.notna(row['Link']):
            st.markdown(f"**Article link**: [{row['Link']}]({row['Link']})")

        if 'Implementation Link' in row and pd.notna(row['Implementation Link']):
            st.markdown(f"**Implementation link**: [{row['Implementation Link']}]({row['Implementation Link']})")
        elif row.get('Public Implementation Available') == "No":
