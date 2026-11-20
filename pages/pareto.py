
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------
# CONFIGURATION
# -----------------------------------
pareto_icon = r"C:\Users\atarnagda\Desktop\Downtime\mAX\data\icons\pareto icon.png"
st.set_page_config(
    page_title="Pareto Analysis",
    page_icon=pareto_icon,
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Analyse de Pareto")
multi ='''
    :blue[Analyse des Compartements ayant le plus d'intervention sur une periode donnée.
    Les filtres sont définis sur le -- *Model* -- et la -- *Category* -- :+1:]
    '''
st.markdown(
    multi,
    width=550,
    text_alignment="center"
)

# -----------------------------------
# Data analysis based on Pareto
# -----------------------------------

if (
    st.session_state.get("df_key") is not None
    and not st.session_state.df_key.empty
):

    df = st.session_state.df_key

    required_columns = ["Model", "Category", "Compartment"]

    if not all(col in df.columns for col in required_columns):
        st.error("Le fichier doit contenir les colonnes Model, Category et Compartment.")
        st.stop()

    st.badge(f"{len(df)} lignes chargées.", icon=":material/check:", color="green")

    # Tableau récapitulatif des données
    with st.expander("Voir les données à analyser."):
        st.dataframe(
            df,
            width='stretch'
        )
    st.divider()

    # -----------------------------------
    # FILTRES
    # -----------------------------------
    st.sidebar.header("Filtres")

    filter_A = st.sidebar.multiselect(
        "Filtrer Model",
        options=sorted(df["Model"].dropna().unique().tolist()),
        default=[]
    )

    filter_B = st.sidebar.multiselect(
        "Filtrer Category",
        options=sorted(df["Category"].dropna().unique().tolist()),
        default=[]
    )

    filtered_df = df.copy()

    if filter_A:
        filtered_df = filtered_df[
            filtered_df["Model"].isin(filter_A)
        ]

    if filter_B:
        filtered_df = filtered_df[
            filtered_df["Category"].isin(filter_B)
        ]

    # -----------------------------------
    # PARAMETRES DU GRAPHIQUE
    # -----------------------------------
    st.sidebar.header("Paramètres du Pareto")

    group_columns = st.sidebar.multiselect(
        "Regroupement (GroupBy)",
        options=["Model", "Category"],
        default=["Model", "Category"]
    )

    top_n = st.sidebar.number_input(
        "Nombre maximum d'éléments Compartment",
        min_value=1,
        max_value=1000,
        value=30
    )

    show_values = st.sidebar.checkbox(
        "Afficher les valeurs sur les barres",
        value=True
    )

    # -----------------------------------
    # CALCUL DU PARETO
    # -----------------------------------
    if filtered_df.empty:
        st.warning("Aucune donnée disponible après filtrage.")

    else:

        # Regroupement éventuel
        if group_columns:
            groups = filtered_df.groupby(
                group_columns,
                dropna=False
            )
        else:
            groups = [( "Toutes les données", filtered_df )]

        for group_name, group_df in groups:

            # st.subheader(f"Groupe : {group_name[0]}")

            # Comptage des occurrences de C
            pareto = (
                group_df["Compartment"]
                .value_counts(dropna=False)
                .reset_index()
            )

            pareto.columns = ["Element", "Occurrences"]

            # Tri décroissant
            pareto = pareto.sort_values(
                "Occurrences",
                ascending=False
            )

            # Limitation Top N
            pareto = pareto.head(top_n).copy()

            # Pourcentage cumulé
            total = group_df["Compartment"].value_counts(
                dropna=False
            ).sum()

            pareto["Pourcentage"] = (
                pareto["Occurrences"] / total * 100
            )

            pareto["Pourcentage cumulé"] = (
                pareto["Pourcentage"].cumsum()
            )

            # -----------------------------------
            # GRAPHIQUE PARETO
            # -----------------------------------
            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Histogramme
            fig.add_trace(
                go.Bar(
                    x=pareto["Element"].astype(str),
                    y=pareto["Occurrences"],
                    name="Occurrences",
                    marker_color="#f7d417",
                    text=pareto["Occurrences"] if show_values else None,
                    textposition="outside"
                ),
                secondary_y=False
            )

            # Courbe cumulée
            fig.add_trace(
                go.Scatter(
                    x=pareto["Element"].astype(str),
                    y=pareto["Pourcentage cumulé"],
                    name="% cumulé",
                    mode="lines+markers",
                    line=dict(
                        color="#e70000",
                        width=3
                    ),
                    marker=dict(size=7)
                ),
                secondary_y=True
            )

            # Mise en forme
            fig.update_layout(
                title=f"Model {group_name[0]} - {group_name[1]} (Total: {total})",
                template="plotly_white",
                height=550,
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    y=1.12
                ),
                xaxis_title="Éléments de Compartment"
            )

            fig.update_yaxes(
                title_text="Nombre d'occurrences",
                secondary_y=False,
                rangemode="tozero"
            )

            fig.update_yaxes(
                title_text="Pourcentage cumulé (%)",
                secondary_y=True,
                range=[0, 105],
                ticksuffix="%"
            )

            st.plotly_chart(
                fig,
                width='stretch'
            )

            # Tableau récapitulatif
            with st.expander("Voir les données du Pareto"):
                st.dataframe(
                    pareto,
                    width='stretch'
                )

            st.divider()

else:
    st.info("Veuillez importer un fichier pour commencer.")
