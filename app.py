import streamlit as st
import pandas as pd
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

st.set_page_config(page_title="Beatmaker CRM", page_icon="🎹", layout="wide")
st.title("🎹 Beatmaker Bulk Sender")

# 1. Secrets
API_KEY = st.secrets.get("SENDGRID_API_KEY", "")
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "")

# 2. Upload
uploaded_file = st.sidebar.file_uploader("Fichier CRM", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Lecture et nettoyage
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df.columns = [c.strip() for c in df.columns]
        
        # Mapping des colonnes
        rename_map = {c: 'Mail' for c in df.columns if c.lower() in ['mail', 'email']}
        rename_map.update({c: 'Nom' for c in df.columns if c.lower() in ['nom', 'name', 'artiste']})
        rename_map.update({c: 'Lien' for c in df.columns if c.lower() in ['lien', 'link', 'mega']})
        df.rename(columns=rename_map, inplace=True)

        if 'Mail' not in df.columns or 'Nom' not in df.columns:
            st.error("Il manque les colonnes Nom ou Mail.")
        else:
            # Sélection
            st.subheader("🚀 1. Sélection")
            selected_names = st.multiselect("Artistes", options=df['Nom'].tolist())
            final_df = df[df['Nom'].isin(selected_names)]

            if not final_df.empty:
                # Message
              # --- NOUVEAU BLOC DE MESSAGES ---
                st.subheader("📧 2. Configuration du Message")

                # Bibliothèque de templates
                styles_mail = {
                    "🎯 Approche Pro": {
                        "sujet": "Pack Exclu - [Ton Nom] x {nom}",
                        "corps": "Salut {nom},\n\nJ'aime beaucoup ton énergie, j'ai préparé des prods qui colleraient parfaitement à ton univers.\n\nTu peux écouter les exclus ici : {lien}\n\nDis-moi si une vibe te parle !"
                    },
                    "🔥 Approche Directe": {
                        "sujet": "Prods pour {nom} (Lien MEGA)",
                        "corps": "Yo {nom},\n\nGros pack de prods préparé pour toi. Écoute ça quand t'as un moment : {lien}\n\nSi tu poses sur un truc, préviens-moi pour les pistes séparées."
                    },
                    "⚠️ Approche Studio": {
                        "sujet": "Exclus pour ta session ({nom})",
                        "corps": "Salut {nom},\n\nJe t'envoie ça en direct du studio, je viens de les finir et j'ai direct entendu ta voix dessus : {lien}\n\nFais-moi signe si tu bloques une prod !"
                    }
                }

                # Menu de choix
                choix_mood = st.selectbox("Choisir l'ambiance du mail", list(styles_mail.keys()))
                
                # Champs de saisie (ils se mettent à jour selon le menu)
                subject = st.text_input("Objet du mail", value=styles_mail[choix_mood]["sujet"])
                body = st.text_area("Message", value=styles_mail[choix_mood]["corps"], height=200)
                
                if st.button(f"🔥 ENVOYER À {len(final_df)} ARTISTES"):
                    sg = SendGridAPIClient(API_KEY)
                    for _, row in final_df.iterrows():
                        try:
                            # Personnalisation
                            m_subj = subject.replace("{nom}", str(row['Nom']))
                            m_body = body.replace("{nom}", str(row['Nom'])).replace("{lien}", str(row.get('Lien', '')))
                            
                            message = Mail(from_email=SENDER_EMAIL, to_emails=str(row['Mail']), subject=m_subj, plain_text_content=m_body)
                            sg.send(message)
                            st.write(f"✅ Envoyé à {row['Nom']}")
                        except Exception:
                            st.error(f"❌ Échec pour {row['Nom']}")
                    st.balloons()
                    st.success("Terminé !")
            else:
                st.info("Choisis au moins un artiste.")

    except Exception as e:
        st.error(f"Erreur de fichier : {e}")
else:
    st.info("Upload ton fichier pour commencer.")
