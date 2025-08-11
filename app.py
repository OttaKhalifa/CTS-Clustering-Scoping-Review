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
            st.markdown("**Implementation**: Not publicly available")

        if 'Comments' in row and pd.notna(row['Comments']):
            st.markdown(f"**Comments**: {row['Comments']}")

    st.markdown("---")

# =========================
# App
# =========================
data, success, error_message = load_data()

with st.sidebar:
    st.header("Filters")

    if not success:
        st.error(error_message)
    else:
        

        st.subheader("Select Your Data Properties")

        criteria = {
            "Continuous time": "Is the temporal scale **continuous**?",
            "Covariates": "Are there time-invariant covariates?",
            "Various lengths": "Are your sequences from various lengths?",
            "Missing data": "Do you have missing data?",
            "Multivariate": "Are your time series multivariate?",
            "Public Implementation Available": "Do you need a public implementation?",
            "Scalability index": "Do you have a big volume of data? $N \\times T_{max} \\times S > 10^7$"
        }

        condition = pd.Series([True] * len(data))
        selected_filters = {}

        for col, question in criteria.items():
            if col in data.columns:
                selected = st.checkbox(question)
                selected_filters[col] = selected
                if selected:
                    if col == "Scalability index":
                        condition &= data[col].apply(
                            lambda x: pd.notna(x) and str(x).replace('.', '', 1).isdigit() and int(float(x)) >= 7
                        )
                    else:
                        condition &= (data[col] == "Yes")

        if "Data type (standardized)" in data.columns:
            st.subheader("Data Type")
            all_data_types = set(
                word.strip()
                for types in data["Data type (standardized)"].dropna()
                for word in str(types).split(',')
            )
            data_type_options = ["No preference"] + sorted(all_data_types)

            selected_data_type = st.selectbox(
                "Select data type for your sequences:",
                data_type_options
            )

            if selected_data_type != "No preference":
                condition &= data["Data type (standardized)"].apply(
                    lambda x: selected_data_type in x if pd.notna(x) else False
                )

# Initialiser l'état
if 'in_family_expander' not in st.session_state:
    st.session_state.in_family_expander = False

if success:
    filtered_data = data[condition]

    tab1, tab2 = st.tabs(["📋 Methods", "📊 Sankey Plot"])

    with tab1:
        results_col1, results_col2 = st.columns([2, 1])
        with results_col1:
            st.subheader(f"{len(filtered_data)} methods found based on your criteria")

        with results_col2:
            if not filtered_data.empty:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    filtered_data.to_excel(writer, index=False, sheet_name="Filtered Data")
                output.seek(0)
                st.download_button(
                    label="📥 Download Results as Excel",
                    data=output,
                    file_name="filtered_methods.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        if filtered_data.empty:
            st.info("No methods match your selected criteria. Try changing your filters.")
        else:
            if "Method Family" in filtered_data.columns:
                method_families = filtered_data["Method Family"].dropna().unique()
                for family in method_families:
                    family_data = filtered_data[filtered_data["Method Family"] == family]
                    with st.expander(f"🔹 {family} Methods ({len(family_data)})", expanded=False):
                        st.session_state.in_family_expander = True
                        for index, row in family_data.iterrows():
                            display_method(row, index)
                        st.session_state.in_family_expander = False
            else:
                st.warning("La colonne 'Method Family' n'existe pas dans les données.")
                st.subheader("Methods")
                for index, row in filtered_data.iterrows():
                    display_method(row, index)

    with tab2:
        st.subheader("📊 Data Flow Visualization")

        if filtered_data.empty:
            st.info("No data to visualize. Please adjust your filters.")
        else:
            st.markdown(f"**Sankey diagram based on {len(filtered_data)} filtered methods**")

            try:
                sankey_html = generate_sankey_html(
                    filtered_data,
                    width=SANKEY_WIDTH,
                    height=SANKEY_HEIGHT,
                    pad=SANKEY_PAD,
                    thickness=SANKEY_THICKNESS
                )

                # Affichage : largeur & hauteur alignées avec le HTML généré
                components.html(
                    sankey_html,
                    height=SANKEY_HEIGHT,
                    width=SANKEY_WIDTH,
                    scrolling=True
                )

            except Exception as e:
                st.error(f"Error generating Sankey plot: {str(e)}")
                st.info("Please check that your Sankey function is properly imported and configured.")
