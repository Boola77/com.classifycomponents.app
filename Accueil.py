import streamlit as st
import pandas as pd
import base64
import chardet


# -----------------------------------
# CONFIGURATION
# -----------------------------------
st.set_page_config(
    page_title="Data Loading",
    page_icon=r"C:\Users\atarnagda\Desktop\Downtime\mAX\data\icons\load data icon.png",
    layout="wide"
)

st.title("Load Downtime data For Analysis")
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)


# ============================================
#          @@@@@@@@ PACKAGES @@@@@@@
# ============================================

# ======= Read CSV files ========
def read_csv_file(file):
    # Detect file encoding
    raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result["encoding"]
    file.seek(0)

    try:
        df = pd.read_csv(
            file,
            encoding= encoding,
            sep= None,
            engine= "python",
        )
        return df
    except Exception as e:
        st.error(f"Error reading CSV file : {e}")
        return None

# ======= Read EXCEL files ======
def read_excel_file(file):
    try:
        excel_file = pd.ExcelFile(file)
        sheets = excel_file.sheet_names
        return excel_file, sheets
    except Exception as e:
        st.error(f"Error reading Excel file : {e}")
        return None, None


# ============================================
#          @@@@@@@@ PAGE ELEMENTS @@@@@@@
# ============================================
# ======= Clear states ==========
def clear_states():
    keys_to_clear = [
        # Dataframes
        'df_key', 'columns_key',

        # Files
        "file_name", "excel_file", "sheets",

        # Messages
        "success_message",

        # Sheet selection
        "selected_sheet", "saved_sheet",
    ]

    for key in keys_to_clear:
        st.session_state.pop(key, None)

# ======= Initialize states ==========
def init_states():
    default_states = {
        'df_key': None,
        'columns_key': None,
        "file_name": None,
        "excel_file": None,
        "sheets": None,
        "success_message": None,
        "saved_sheet": None,
    }

    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ======= CACHE (PERF ONLY)========
@st.cache_data
def load_browser(path):
    for enc in ["utf-8", "cp1252", "latin1"]:
        try:
            return pd.read_csv(path, sep=None, engine="python", encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Unable to read the CSV file (Unknown encoding)")

# =========== Load the data file ==============
uploaded_file = st.file_uploader(
    "Load Excel or CSV file",
    type=["xlsx", "csv", "xls", "xlsm"],
    width=600
)

# ================== RUN UPLOADING ==================
if uploaded_file and uploaded_file.name != st.session_state.get("file_name"):

    # Cleaning & Initialization
    clear_states()
    init_states()

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):

        df = read_csv_file(uploaded_file)

        st.session_state.df_key = df.copy()
        st.session_state.success_message = (
            "CSV file successfully loaded ✅"
        )

    else:
        try:
            excel_file, sheets = read_excel_file(uploaded_file)

            st.session_state.excel_file = excel_file
            st.session_state.sheets = sheets

            st.session_state.success_message = (
                "Excel file successfully loaded ✅"
            )

        except Exception as e:
            st.error(f"Wrong file extension: {e}")

    st.session_state.file_name = uploaded_file.name

# ================= Display Success Message =================
# Initialiser la valeur par défaut
if "success_message" not in st.session_state:
    st.session_state["success_message"] = None
    st.session_state["sheets"] = None

if st.session_state.success_message:
    st.success(st.session_state.success_message)

# ==========================================================
# EXCEL SHEET READING
# ==========================================================
def save_selected_sheet():
    st.session_state.saved_sheet = (
        st.session_state.selected_sheet
    )

if st.session_state.sheets:

    left, right = st.columns(2)

    left.header(
        f"Sheets available = {len(st.session_state.sheets)}"
    )

    # Vérifier que la feuille sauvegardée existe toujours
    if st.session_state.saved_sheet not in st.session_state.sheets:
        st.session_state.saved_sheet = None

    # Retrouver l'index de la dernière feuille sélectionnée
    default_index = (
        st.session_state.sheets.index(st.session_state.saved_sheet)
        if st.session_state.saved_sheet is not None
        else None
    )

    select_sheet = right.selectbox(
        "Choose a sheet",
        options=st.session_state.sheets,
        index=default_index,
        placeholder="Please, make sure to select the correct sheet.",
        key="selected_sheet",
        on_change=save_selected_sheet
    )

    # Lire la feuille sélectionnée
    if st.session_state.saved_sheet:

        df = pd.read_excel(
            st.session_state.excel_file,
            sheet_name=st.session_state.saved_sheet
        )

        st.session_state.df_key = df.copy()


# Initialiser la valeur par défaut
if "df_key" not in st.session_state:
    st.session_state["df_key"] = pd.DataFrame()

if (
    st.session_state.df_key is not None
    and not st.session_state.df_key.empty
):

    # Data visualization
    with st.expander("Voir les données à analyser."):
        st.dataframe(
            st.session_state.df_key,
            width='content'
        )


    # KPI's Visualization
    col_pareto, col_classifier = st.columns([9, 1])
    with col_pareto:
        if st.button(
            "PARETO",
        ):
            # Initialiser la valeur par défaut
            if "df_pareto" not in st.session_state:
                st.session_state["df_pareto"] = pd.DataFrame()

            st.session_state.df_pareto = st.session_state.df_key.copy()
            st.switch_page("pages/pareto.py")

    with col_classifier:
        if st.button(
            "CLASSIFY",
        ):
            st.session_state.df_key = st.session_state.df_key.copy()
            st.switch_page("pages/classifier.py")