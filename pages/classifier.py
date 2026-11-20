import streamlit as st
import pandas as pd

import predict.predictor as model


# -----------------------------------
# CONFIGURATION
# -----------------------------------
st.set_page_config(
    page_title="Data Processing",
    page_icon=r"C:\Users\atarnagda\Desktop\Downtime\mAX\data\icons\data analysis.png",
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

st.title("Downtime Classifier")

# ============================================
#          @@@@@@@@ PACKAGES @@@@@@@
# ============================================
# ====================================
# Read CSV files
# ====================================
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
 
# ====================================
# Read EXCEL files
# ====================================
def read_excel_file(file):
    try:
        excel_file = pd.ExcelFile(file)
        sheets = excel_file.sheet_names
        return excel_file, sheets
    except Exception as e:
        st.error(f"Error reading Excel file : {e}")
        return None, None


@st.cache_data
def convert_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, sep=";").encode("utf-8-sig")


# ====================================
# Classification models variables
# ====================================
@st.dialog("📝 Required informations for classifacation")
def show_modal_for_predict_entry(df_value):

    predict_variables = st.multiselect(
        "Model entry variables",
        df_value.columns,
        placeholder="You should select columns for models classifications."
    )

    if st.button("Run"):

        if not predict_variables:
            st.warning("Please select at least one variable.")
            return

        # Run classification        
        df_model = model.fill_description_cat(
            df_value,
            predict_variables
        )

        # Save the result
        st.session_state.df_model_key = df_model

        # Navigate to main.py
        st.switch_page("pages/classifier.py")
    

@st.dialog("📝 Required informations to download File")
def download_modal(df_value):

    file_name = st.text_input(
        "File name", width=200,
        placeholder="Enter file exportation name."
    )
    file_name = file_name.strip().replace(" ", "_")
    if file_name:
        st.download_button(
            label="Validate",
            data=convert_csv(df_value),
            file_name=f"{file_name}.csv",
            mime="text/csv"
        )


# ============================================
#          @@@@@@@@ PAGE ELEMENTS @@@@@@@
# ============================================
# ======= Clear states ==========
def clear_states():
    keys_to_clear = [
        # Dataframes
        'df_key', 'columns_key', 'df_model_key',
        # Files
        "file_name", "excel_file", "sheets",
        "selected_sheet", "success_message",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)

# ======= Initialize states ==========
def init_states():
    default_states = {
        'df_key' : None,
        'df_model_key' : None,
        'columns_key' : None,
        "file_name" : None,
        "excel_file" : None,
        "sheets" : None,
        "selected_sheet" : None,
        "success_message" : None,
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


# Initialiser la valeur par défaut
if "df_key" not in st.session_state:
    st.session_state["df_key"] = pd.DataFrame()

if "df_model_key" not in st.session_state:
    st.session_state["df_model_key"] = pd.DataFrame()

if (
    st.session_state.df_key is not None
    and not st.session_state.df_key.empty
):
    # Data visualization
    st.subheader("🗳️Raw data Landscape")
    st.dataframe(st.session_state.df_key)

    # ======== Models prediction running ==========
    predict_button = st.button('Classifier')

    if predict_button:
        # Pop widget for models classification
        show_modal_for_predict_entry(st.session_state.df_key) 
            
        
if (
    st.session_state.df_model_key is not None
    and not st.session_state.df_model_key.empty
):
    # Data visualization
    st.subheader("🗳️ Classified data Landscape")
    st.dataframe(st.session_state.df_model_key) 

    # Download or Pareto
    # KPI's Visualization
    col_pareto, col_download = st.columns([9, 1])
    with col_pareto:
        if st.button(
            "PARETO",
        ):
            # Initialiser la valeur par défaut
            if "df_pareto" not in st.session_state:
                st.session_state["df_pareto"] = pd.DataFrame()

            st.session_state.df_pareto = st.session_state.df_model_key.copy()
            st.switch_page("pages/test.py")

    with col_download:
        # ========= Download processed file ===========
        download_button = st.button('⬇️ Download')
        if download_button:
            download_modal(st.session_state.df_model_key)


