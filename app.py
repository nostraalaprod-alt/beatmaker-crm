import streamlit as st
import pandas as pd
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64

st.set_page_config(page_title="Beatmaker CRM Pro", page_icon="🔥")

st.title("🚀 Beatmaker Bulk Sender")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("1. Setup")
    api_key = st.text_input("Clé API SendGrid", type="password")
    sender_email = st.text_input("Votre Email")
    
    st.header("2. Base de Données")
    uploaded_excel = st.file_uploader("Upload ton fichier Excel (.xlsx)", type=["xlsx"])

# --- CHARGEMENT DES CONTACTS ---
contacts_df = None
if uploaded_excel:
    contacts_df = pd.read_excel(uploaded_excel)
    st.sidebar.success(f"{len(contacts_df)} contacts chargés !")

# --- INTERFACE PRINCIPALE ---
if contacts_df is not None:
    st.subheader("Sélection des destinataires")
    
    # Filtre par style si la colonne existe
    if 'Style' in contacts_df.columns:
        styles = contacts_df['Style'].unique()
        selected_style = st.multiselect("Filtrer par style", styles)
        if selected_style:
            contacts_df = contacts_df[contacts_df['Style'].isin(selected_style)]

    # Affichage de la liste avec des cases à cocher
    selected_indices = st.multiselect(
        "Choisir les rappeurs à contacter",
        options=contacts_df.index,
        format_func=lambda x: f"{contacts_df.loc[x, 'Nom']} ({contacts_df.loc[x, 'Email']})"
    )
    
    selected_contacts = contacts_df.loc[selected_indices]

    st.divider()

    # Configuration du mail
    subject = st.text_input("Objet du mail", "Pack Exclu - [Ton Nom]")
    message_template = st.text_area("Ton Message (Utilise {nom} pour personnaliser)", 
                                  "Salut {nom},\n\nJ'ai vu tes dernières sorties, j'ai préparé des mélo qui collent à ton univers. Dis-moi ce que t'en penses !")
    
    uploaded_files = st.file_uploader("Ajouter tes prods (ZIP/MP3)", accept_multiple_files=True)

    # --- BOUTON D'ENVOI ---
    if st.button(f"🔥 Envoyer à {len(selected_contacts)} rappeurs"):
        if not api_key or not sender_email:
            st.error("Configure ton API Key et ton email dans la barre latérale.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, (idx, row) in enumerate(selected_contacts.iterrows()):
                try:
                    sg = SendGridAPIClient(api_key)
                    # Personnalisation dynamique du message
                    custom_message = message_template.replace("{nom}", str(row['Nom']))
                    
                    message = Mail(
                        from_email=sender_email,
                        to_emails=row['Email'],
                        subject=subject,
                        plain_text_content=custom_message
                    )

                    # Pièces jointes (réinitialisées à chaque itération)
                    for uploaded_file in uploaded_files:
                        uploaded_file.seek(0) # Revenir au début du fichier pour chaque envoi
                        encoded_file = base64.b64encode(uploaded_file.read()).decode()
                        attachment = Attachment(
                            FileContent(encoded_file),
                            FileName(uploaded_file.name),
                            FileType(uploaded_file.type),
                            Disposition('attachment')
                        )
                        message.add_attachment(attachment)

                    sg.send(message)
                    
                    # Update progression
                    percent_complete = (i + 1) / len(selected_contacts)
                    progress_bar.progress(percent_complete)
                    status_text.text(f"Envoi à {row['Nom']} terminé...")

                except Exception as e:
                    st.error(f"Erreur pour {row['Nom']}: {e}")
            
            st.success("Tous les mails ont été envoyés !")
            st.balloons()
else:
    st.info("Veuillez uploader un fichier Excel dans la barre latérale pour commencer.")

import plotly.express as px

# --- SECTION DASHBOARD (À placer avant la partie envoi) ---
st.divider()
st.header("📊 Dashboard de ton Activité")

if contacts_df is not None:
    col_stat1, col_stat2 = st.columns(2)
    
    with col_stat1:
        # Graphique : Répartition par Style
        if 'Style' in contacts_df.columns:
            fig_style = px.pie(contacts_df, names='Style', title="Répartition de tes Contacts par Style")
            st.plotly_chart(fig_style, use_container_width=True)
    
    with col_stat2:
        # Simulation de Stats d'envois (à connecter à une DB pour du réel)
        st.metric(label="Total Contacts", value=len(contacts_df))
        st.metric(label="Taux de personnalisation", value="100%", help="Basé sur l'utilisation de la balise {nom}")

st.divider()