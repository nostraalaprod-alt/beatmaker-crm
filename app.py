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
    uploaded_file = st.file_uploader("Upload ton fichier (CSV ou XLSX)", type=["xlsx", "csv"])

# --- CHARGEMENT INTELLIGENT ---
contacts_df = None
if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            contacts_df = pd.read_csv(uploaded_file)
        else:
            contacts_df = pd.read_excel(uploaded_file)
        
        # Normalisation des colonnes (pour accepter Mail ou Email)
        contacts_df.columns = [c.strip().capitalize() for c in contacts_df.columns]
        if 'Mail' in contacts_df.columns and 'Email' not in contacts_df.columns:
            contacts_df.rename(columns={'Mail': 'Email'}, inplace=True)
            
        st.sidebar.success(f"{len(contacts_df)} contacts chargés !")
    except Exception as e:
        st.sidebar.error(f"Erreur de lecture : {e}")

# --- INTERFACE PRINCIPALE ---
if contacts_df is not None:
    st.subheader("Sélection des destinataires")
    
    if 'Style' in contacts_df.columns:
        styles = contacts_df['Style'].unique()
        selected_style = st.multiselect("Filtrer par style", styles)
        if selected_style:
            contacts_df = contacts_df[contacts_df['Style'].isin(selected_style)]

    selected_indices = st.multiselect(
        "Choisir les rappeurs",
        options=contacts_df.index,
        format_func=lambda x: f"{contacts_df.loc[x, 'Nom']} - {contacts_df.loc[x, 'Email']}"
    )
    
    selected_contacts = contacts_df.loc[selected_indices]
    st.divider()

    subject = st.text_input("Objet du mail", "Pack Exclu - [Ton Nom]")
    message_template = st.text_area("Message ({nom} pour personnaliser)", 
                                  "Salut {nom},\n\nJ'ai bossé sur des prods qui collent à ton univers. Dis-moi ce que t'en penses !")
    
    uploaded_prods = st.file_uploader("Ajouter tes prods (ZIP/MP3)", accept_multiple_files=True)

    if st.button(f"🔥 Envoyer à {len(selected_contacts)} rappeurs"):
        if not api_key or not sender_email:
            st.error("Configure ton API Key et ton email.")
        else:
            progress_bar = st.progress(0)
            for i, (idx, row) in enumerate(selected_contacts.iterrows()):
                try:
                    sg = SendGridAPIClient(api_key)
                    custom_msg = message_template.replace("{nom}", str(row['Nom']))
                    
                    message = Mail(
                        from_email=sender_email,
                        to_emails=str(row['Email']),
                        subject=subject,
                        plain_text_content=custom_msg
                    )

                    for p in uploaded_prods:
                        p.seek(0)
                        encoded = base64.b64encode(p.read()).decode()
                        message.add_attachment(Attachment(FileContent(encoded), FileName(p.name), FileType(p.type), Disposition('attachment')))

                    sg.send(message)
                    progress_bar.progress((i + 1) / len(selected_contacts))
                except Exception as e:
                    st.error(f"Erreur pour {row['Nom']}: {e}")
            st.success("Terminé !")
            st.balloons()
else:
    st.info("Upload ton fichier CRM pour commencer.")
