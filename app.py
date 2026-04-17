import streamlit as st
import pandas as pd
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Configuration de la page
st.set_page_config(page_title="Beatmaker CRM Pro", page_icon="🎹", layout="wide")

st.title("🎹 Beatmaker Bulk Link Sender")
st.markdown("---")

# --- RÉCUPÉRATION DES SECRETS ---
API_KEY = st.secrets.get("SENDGRID_API_KEY", "")
SENDER_EMAIL = st.secrets.get("SENDER_EMAIL", "")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("📂 Importation")
    uploaded_file = st.file_uploader("Upload ton CRM (CSV ou Excel)", type=["xlsx", "csv"])
    
    st.header("⚙️ Statut Configuration")
    if API_KEY and SENDER_EMAIL:
        st.success("✅ API SendGrid configurée")
    else:
        st.error("❌ Clé API ou Email manquant dans les Secrets")

# --- CHARGEMENT ET TRAITEMENT DES DONNÉES ---
if uploaded_file:
    try:
        # Lecture du fichier
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # Nettoyage des colonnes (enlève les espaces et uniformise)
        df.columns = [c.strip() for c in df.columns]
        
        # Vérification des colonnes obligatoires
        required_cols = ['Nom', 'Mail', 'Lien']
        missing_cols = [c for c in required_cols if c not in df.columns]
        
        if missing_cols:
            st.error(f"Il manque des colonnes dans ton fichier : {', '.join(missing_cols)}")
        else:
            st.sidebar.success(f"💎 {len(df)} contacts chargés")

            # --- FILTRES ---
            st.subheader("🚀 1. Sélectionne tes cibles")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'Style' in df.columns:
                    styles = df['Style'].unique().tolist()
                    selected_styles = st.multiselect("Filtrer par Style", styles)
                    if selected_styles:
                        df = df[df['Style'].isin(selected_styles)]

            with col2:
                selected_names = st.multiselect(
                    "Artistes à contacter", 
                    options=df['Nom'].tolist(),
                    default=df['Nom'].tolist() if len(df) < 5 else []
                )

            final_selection = df[df['Nom'].isin(selected_names)]

            if not final_selection.empty:
                st.write(f"Selection : **{len(final_selection)} artiste(s)**")
                
                st.markdown("---")
                st.subheader("📧 2. Rédige ton message personnalisé")
                
                # Interface de rédaction
                subject = st.text_input("Objet de l'email", "Pack Exclusif - [Ton Nom]")
                
                default_msg = (
                    "Salut {nom},\n\n"
                    "J'ai vu ce que tu fais sur Instagram ({instagram}), j'aime beaucoup l'énergie.\n\n"
                    "J'ai préparé un pack {style} spécifiquement pour toi.\n\n"
                    "Tu peux écouter les exclus ici : {lien}\n\n"
                    "Dis-moi ce que t'en penses !"
                )
                
                email_body = st.text_area("Message (utilise les balises entre accolades)", value=default_msg, height=250)
                
                st.info("💡 **Astuces :** Utilise `{nom}`, `{instagram}`, `{style}` ou `{lien}` pour que le code les remplace automatiquement par les infos de ton tableau.")

                # --- BOUTON D'ENVOI ---
                if st.button(f"🔥 ENVOYER À {len(final_selection)} ARTISTES"):
                    if not API_KEY or not SENDER_EMAIL:
                        st.error("Erreur : La configuration SendGrid est incomplète.")
                    else:
                        sg = SendGridAPIClient(API_KEY)
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        success_count = 0
                        error_count = 0

                        for i, (idx, row) in enumerate(final_selection.iterrows()):
                            try:
                                # Remplacement dynamique des balises
                                # On utilise .get() pour éviter les erreurs si une colonne est vide
                                formatted_msg = email_body.format(
                                    nom=str(row.get('Nom', '')),
                                    instagram=str(row.get('Instagram', '')),
                                    style=str(row.get('Style', '')),
                                    lien=str(row.get('Lien', ''))
                                )

                                message = Mail(
                                    from_email=SENDER_EMAIL,
                                    to_emails=str(row.get('Mail', '')),
                                    subject=subject,
                                    plain_text_content=formatted_msg
                                )

                                sg.send(message)
                                success_count += 1
                                
                            except Exception as e:
                                st.error(f"Erreur pour {row['Nom']} : {e}")
                                error_count += 1
                            
                            # Mise à jour barre de progression
                            progress_bar.progress((i + 1) / len(final_selection))
                            status_text.text(f"Envoi en cours : {i+1}/{len(final_selection)}")

                        st.success(f"✅ Terminé ! {success_count} mails envoyés, {error_count} erreur(s).")
                        st.balloons()
            else:
                st.warning("Choisis au moins un artiste dans la liste pour continuer.")

    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")
