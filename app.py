import streamlit as st
import pandas as pd
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# 1. Configuration de la page
st.set_page_config(page_title="Beatmaker CRM Pro", page_icon="🎹", layout="wide")

st.title("🎹 Beatmaker Bulk Link Sender")
st.markdown("---")

# 2. Récupération des secrets
API_KEY = st.secrets.get("SENDGRID_API_KEY", "")
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "")

# 3. Barre latérale
with st.sidebar:
    st.header("📂 Importation")
    uploaded_file = st.file_uploader("Upload ton CRM (CSV ou Excel)", type=["xlsx", "csv"])
    if API_KEY and SENDER_EMAIL:
        st.success("✅ Config OK")
    else:
        st.error("❌ Config incomplète dans Secrets")

# 4. Traitement des données
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Nettoyage des colonnes (enlève les espaces invisibles)
        df.columns = [c.strip() for c in df.columns]
        
        # Mapping intelligent des colonnes
        rename_dict = {}
        for col in df.columns:
            c_low = col.lower()
            if c_low in ['mail', 'email', 'e-mail']: rename_dict[col] = 'Mail'
            if c_low in ['lien', 'link', 'mega', 'lien mega']: rename_dict[col] = 'Lien'
            if c_low in ['nom', 'name', 'artiste']: rename_dict[col] = 'Nom'
            if c_low in ['instagram', 'insta']: rename_dict[col] = 'Instagram'
            if c_low in ['style', 'vibe']: rename_dict[col] = 'Style'
        df.rename(columns=rename_dict, inplace=True)

        # Vérification des colonnes critiques
        if 'Mail' not in df.columns or 'Lien' not in df.columns or 'Nom' not in df.columns:
            st.error("⚠️ Ton fichier doit contenir les colonnes : Nom, Mail et Lien.")
            st.write("Colonnes trouvées :", list(df.columns))
        else:
            st.sidebar.success(f"💎 {len(df)} contacts chargés")

            # --- SÉLECTION DES CIBLES ---
            st.subheader("🚀 1. Sélectionne tes cibles")
            col1, col2 = st.columns(2)
            
            with col1:
                styles = df['Style'].unique().tolist() if 'Style' in df.columns else ["Tous"]
                sel_styles = st.multiselect("Filtrer par Style", styles)
                if sel_styles:
                    df = df[df['Style'].isin(sel_styles)]

            with col2:
                selected_names = st.multiselect("Artistes à contacter", options=df['Nom'].tolist())

            final_selection = df[df['Nom'].isin(selected_names)]

            if not final_selection.empty:
                # --- TEMPLATES ---
                templates = {
                    "🎯 Premier Contact": {
                        "sujet": "Pack Exclu - [Ton Nom] x {nom}",
                        "corps": "Salut {nom},\n\nJ'ai vu ce que tu fais sur Instagram ({instagram}), j'aime beaucoup l'énergie.\n\nJ'ai préparé un pack {style} spécifiquement pour toi.\n\nTu peux écouter les exclus ici : {lien}\n\nDis-moi si quelque chose te parle !"
                    },
                    "🔥 Relance": {
                        "sujet": "Petit rappel / Pack {style}",
                        "corps": "Yo {nom},\n\nJe te relance juste pour savoir si tu avais eu le temps de jeter une oreille au pack.\n\nLe lien est ici : {lien}"
                    }
                }

                st.divider()
                st.subheader("📧 2. Rédige ton message")
                
                choix_t = st.selectbox("Choisir un modèle", list(templates.keys()))
                sel_t = templates
