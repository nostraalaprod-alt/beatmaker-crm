import streamlit as st
import pandas as pd
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

st.set_page_config(page_title="Beatmaker CRM", page_icon="🎹", layout="wide")
st.title("🎹 Beatmaker Bulk Sender")

# 1. Récupération des secrets (Configurés dans le dashboard Streamlit)
API_KEY = st.secrets.get("SENDGRID_API_KEY", "")
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "")

# 2. Upload du fichier
uploaded_file = st.sidebar.file_uploader("Fichier CRM (Excel ou CSV)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Lecture propre du fichier
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        df.columns = [c.strip() for c in df.columns]
        
        # Mapping intelligent pour trouver les bonnes colonnes
        rename_map = {}
        for c in df.columns:
            low_c = c.lower()
            if low_c in ['mail', 'email', 'e-mail']: rename_map[c] = 'Mail'
            if low_c in ['nom', 'name', 'artiste']: rename_map[c] = 'Nom'
            if low_c in ['lien', 'link', 'mega']: rename_map[c] = 'Lien'
        df.rename(columns=rename_map, inplace=True)

        if 'Mail' not in df.columns or 'Nom' not in df.columns:
            st.error("⚠️ Erreur : Ton fichier doit avoir une colonne 'Nom' et une colonne 'Mail'.")
        else:
            # --- ÉTAPE 1 : SÉLECTION ---
            st.subheader("🚀 1. Sélectionne tes cibles")
            selected_names = st.multiselect("Artistes à contacter", options=df['Nom'].tolist())
            final_df = df[df['Nom'].isin(selected_names)]

            if not final_df.empty:
                st.divider()
                st.subheader("📧 2. Message")

                # Bibliothèque de styles
                styles_mail = {
                    "🔥 Style Direct": {
                        "sujet": "Pour {nom} 🎹",
                        "corps": "Yo boss,\n\nJ'espère que ça va t'inspirer !!\n\nLien : {lien}\n\nGrosse Force !!"
                    },
                    "🎤 Style Studio": {
                        "sujet": "Pack Exclu - {nom}",
                        "corps": "Yo,\n\nPetit pack de pépites pour tes prochaines sessions.\n\nÉcoute ça : {lien}\n\nGrosse Force !!"
                    }
                }

                # Menu de choix avec une "key" unique pour éviter les bugs Streamlit
                choix_mood = st.selectbox("Choisir l'ambiance", list(styles_mail.keys()), key="menu_vibe")
                
                subject = st.text_input("Objet", value=styles_mail[choix_mood]["sujet"])
                body = st.text_area("Message", value=styles_mail[choix_mood]["corps"], height=200)
                
                # --- ÉTAPE 3 : ENVOI ---
                if st.button(f"🔥 ENVOYER À {len(final_df)} ARTISTES"):
                    if not API_KEY or not SENDER_EMAIL:
                        st.error("❌ Erreur : Les secrets (API Key ou Email) ne sont pas configurés dans Streamlit.")
                    else:
                        sg = SendGridAPIClient(API_KEY)
                        progress_bar = st.progress(0)
                        
                        for i, (idx, row) in enumerate(final_df.iterrows()):
                            try:
                                # Préparation du contenu personnalisé
                                m_subj = subject.replace("{nom}", str(row['Nom']))
                                m_body = body.replace("{nom}", str(row['Nom'])).replace("{lien}", str(row.get('Lien', '')))
                                
                                message = Mail(
                                    from_email=SENDER_EMAIL,
                                    to_emails=str(row['Mail']),
                                    subject=m_subj,
                                    plain_text_content=m_body
                                )
                                
                                # Tentative d'envoi
                                response = sg.send(message)
                                st.write(f"✅ Envoyé à {row['Nom']}")
                                
                            except Exception as e:
                                # Affichage de l'erreur détaillée pour comprendre le blocage
                                st.error(f"❌ Échec pour {row['Nom']} : {str(e)}")
                            
                            progress_bar.progress((i + 1) / len(final_df))
                        
                        st.balloons()
                        st.success("Opération terminée !")
            else:
                st.info("Sélectionne au moins un artiste pour commencer.")

    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")
else:
    st.info("👋 Upload ton fichier Excel ou CSV dans la barre latérale.")
