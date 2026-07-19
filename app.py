import io
import json
import urllib.request
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
from google import genai
from google.genai import types

# --- CONFIGURATION ---
FOLDER_ID = "146n-HmjgJqJ1dLUBFclC2moMmztaHuc7"  
SERVICE_ACCOUNT_FILE = "credentials.json"  # Reading directly from your private locker

# Initialize Gemini Client securely from Streamlit Secrets
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="My AI Style Studio", layout="wide")

# --- WEATHER ENGINE ---
def get_local_weather():
    try:
        lat, lon = 51.5074, -0.1278 
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
        temp_c = round(data['current']['temperature_2m'])
        code = data['current']['weather_code']
        status = "Clear/Cloudy"
        if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: status = "Raining"
        elif code in [71, 73, 75, 85, 86]: status = "Snowing"
        return f"{temp_c}°C and {status}"
    except:
        return "Unknown Weather (Mild Day)"

current_weather = get_local_weather()

# --- SIDEBAR INTERFACE ---
st.sidebar.title("🎛️ Style Controls")
st.sidebar.markdown(f"**🌤️ Current Weather:**\n`{current_weather}`")
st.sidebar.markdown("---")

style_filter = st.sidebar.selectbox(
    "What is the vibe or occasion today?",
    ["Any Vibe", "Casual Comfort", "Business Casual", "Elegant/Date Night", "Athleisure/Sporty", "Edgy Streetwear"]
)

# --- SMART FOLDER-DRIVEN CLOSET PARSER ---
@st.cache_data(ttl=300)
def load_structured_closet():
    # Inserted cleanly as a direct python object to fix formatting bugs
    creds_info = {
  "type": "service_account",
  "project_id": "mystylist-502914",
  "private_key_id": "d5b8a4feb29b4d2668594c16f45839478cf468f6",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCcVZ7TyYRjTwis\nKvzqh9f3+2hDrycOETtc7bv4gu3diRzWWAE5fQrGaYrwbQ7GP9wRX9SUjnZYvI+z\nmof5lINnhJLoTLfFioy99CWGdmwmuHnpOqeqfYdOcehv8WjeUggkXMft21ba25ar\nElWTvWlet1kBa4bpfe389Baf/yQN6kov8EIdwN/yRpLi8YskZvB5s9dKjPTaZtS2\nHuDQUbMxuYNrUaNwsJbZhbZy7GV2VAUsSruI1swJ/PalN8ilDKM8+4KDWLQdMlPI\nWk4DMINwHrAS8KNYiQRPhxQxeZ05RUwaFNUsPvKd+izq0kFBIg4eAL6Ak3ddm/PU\n1r0SHTpXAgMBAAECggEAE4NMU7rvX0XaG0MyVkOmXTlwBiKyiTr1Yd/6ekY9Uk1u\n4AIUBQzqb2F1ChVSpsQJv9FqQzCU7PZ8KTq8hhZXYHBXtc79kRZ+Aqeal3Hohdy4\nurerfcg1P0FQdch4AmfSxFcgTTv3V1HZOHkNXWdi44OXBGpbaIFjVxNQT6AU6/eE\nX2P9A/jIbjUTg3Tb1XppJbRkv5uqbGn84c53O1kUXheP4p76EDwZftvVhEUoeMkJ\nbt2ZeguPjrb6DN6WYEjqFIIAJ12hgJCeQauwJ/ReSWrDewOjbQmjz1sKg7LCq9gx\nx8nqxeQLSHcraTIOM/enLDS6EtEdi0SO4Bc8p85X4QKBgQDMXP4sXtzXmDe7CEo0\n2vDOgf4s2fp2eOxnHrHgpWtmy9yDyH3QHqPoPO1WCs6FqpdUTRU5rkI2ke8QB2mL\nX27z+gzmtmaquwWwQBrMZgdhyAH45GayTs5vZrAxKGSHCs8v7djh9/YECCRYDMQ5\nY5dzuRUyldI3xPmOqQmQKc6YDQKBgQDD1fBR1b4285xfKSHJ4h1rsm9cc1A1RWye\nCz2mGp2zcyKJ5TXSmBWkIP9kCKSsaOuQs+0D7jOkS2jinYkJWytxgGUC6K4o/HWI\nS7lAp6jfoRGr3BIQkCR11Ti4w1C5luZZQ0cC27EsSOVbrbApefZps8ntEtbEx4Mo\nT8nFqT7+8wKBgARXNU7b9PTfVs+yLWFSBStdt3hcaOV7TAokrMKIwO8+BUEHUSTK\ngdC8+o2JTTmple1Edd7zxJREJT/B6Iv9Su4DsaJ03Vli/4vu0KLmx+Fbzi7rKwM+\niUP0emmQ4hG8OQpbku+5xI/xXFRCcSiG5QCgPcMFS6HDnUlabcmSGcFBAoGAXxYo\nqsN6qVndqkLhehHFMT6hXaVL46HC3HYex+ESg0g7E/NsD8XydA/lkV+0/VWwU0FZ\nqtfk0TggRDAzkoxm6qRp52Cs94+lTbleyKrfjz24w9aGGu6yFVijQurq7kH7tIm7\nGAMt4o++daY+69ShNa+rMuY7y64H2/HpyYSk5ssCgYEAiYRjXZyj63+MDa8+0fxw\nnqZl51Z8s9K9o1X7NoubT8C2ndVhlhwuUs3+BsFP7pHiVZEMfG709sHCVgW359DA\no7tFpZdMaO9hzV8OjPwE4WWtMlTRlDj9NMWZ9VScStSYwNBNFhWi+jKTQDJWBPXj\nF1IPIXUkTa5Fxi4mwfB/Qlc=\n-----END PRIVATE KEY-----\n",
  "client_email": "wardrobe-robot@mystylist-502914.iam.gserviceaccount.com",
  "client_id": "105695350513960125784",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/wardrobe-robot%40mystylist-502914.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

    
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    drive_service = build('drive', 'v3', credentials=creds)
        
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        
    creds = service_account.Credentials.from_service_account_info(
        creds_info, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    drive_service = build('drive', 'v3', credentials=creds)
    
    folder_query = f"'{FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder'"
    folder_results = drive_service.files().list(q=folder_query, fields="files(id, name)").execute()
    subfolders = folder_results.get('files', [])
    
    closet_by_category = {}
    all_items_flat = []
    
    if subfolders:
        for folder in subfolders:
            cat_name = folder['name']
            query = f"'{folder['id']}' in parents and (mimeType = 'image/jpeg' or mimeType = 'image/png')"
            results = drive_service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])
            
            cat_items = []
            for f in files:
                request = drive_service.files().get_media(fileId=f['id'])
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done: _, done = downloader.next_chunk()
                fh.seek(0)
                img = Image.open(fh)
                
                item_data = {"id": f['id'], "name": f['name'], "image": img, "category": cat_name}
                cat_items.append(item_data)
                all_items_flat.append(item_data)
                
            if cat_items:
                closet_by_category[cat_name] = cat_items
    
    root_query = f"'{FOLDER_ID}' in parents and (mimeType = 'image/jpeg' or mimeType = 'image/png')"
    root_results = drive_service.files().list(q=root_query, fields="files(id, name)").execute()
    root_files = root_results.get('files', [])
    
    if root_files:
        root_items = []
        for f in root_files:
            request = drive_service.files().get_media(fileId=f['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done: _, done = downloader.next_chunk()
            fh.seek(0)
            img = Image.open(fh)
            
            item_data = {"id": f['id'], "name": f['name'], "image": img, "category": "Uncategorized"}
            root_items.append(item_data)
            all_items_flat.append(item_data)
        if root_items:
            closet_by_category["Other/Loose Items"] = root_items

    return closet_by_category, all_items_flat

try:
    closet_categories, my_clothes = load_structured_closet()
except Exception as e:
    st.error(f"Error loading images from folders: {e}")
    closet_categories, my_clothes = {}, []

if "custom_saved_looks" not in st.session_state:
    st.session_state.custom_saved_looks = []
if "canvas_items" not in st.session_state:
    st.session_state.canvas_items = []

st.title("👗 My Personal AI Style Studio")
tab1, tab2, tab3 = st.tabs(["📌 Infinite Lookbook Boards", "📊 Smart Wardrobe Audit", "🎨 Click & Build Outfit Canvas"])

# --- TAB 1 & 2 ---
with tab1:
    if my_clothes:
        num_outfits = st.slider("How many unique outfits do you want to generate?", min_value=3, max_value=12, value=6)
        if st.button("🔄 Generate Style Feed", type="primary"):
            with st.spinner("Curating lookbook..."):
                closet_manifest = ", ".join([f"'{item['name']}'" for item in my_clothes])
                contents = [
                    f"You are an expert personal stylist. Create {num_outfits} distinct combinations using ONLY filenames: [{closet_manifest}]. Dress for {current_weather} and aesthetic '{style_filter}'. Ensure Formula 1 or Formula 2 structure rules apply strictly.",
                ]
                for item in my_clothes[:25]:
                    contents.extend([f"Filename: {item['name']}", item['image']])
                try:
                    response = client.models.generate_content(
                        model='gemini-3.5-flash', contents=contents,
                        config=types.GenerateContentConfig(response_mime_type="application/json"),
                    )
                    outfits_data = json.loads(response.text)
                    for outfit in outfits_data:
                        st.subheader(f"✨ {outfit['outfit_name']}")
                        st.caption(outfit['reasoning'])
                        matched = [c for filename in outfit['items'] for c in my_clothes if c['name'].strip().lower() == filename.strip().lower()]
                        if matched:
                            cols = st.columns(len(matched))
                            for idx, img_item in enumerate(matched):
                                with cols[idx]: st.image(img_item['image'], use_container_width=True, caption=img_item['name'])
                        st.markdown("---")
                except Exception as e: st.error(f"AI Generation Error: {e}")

with tab2:
    st.subheader("📊 Full Closet Analytics Report")
    if my_clothes and st.button("🔍 Run Wardrobe Audit"):
        with st.spinner("Analyzing colors and item styles..."):
            audit_contents = ["Analyze my dominant palette, wardrobe structural missing pieces, and capsule mixability score based on these photos."]
            for item in my_clothes[:25]: audit_contents.extend([f"Filename: {item['name']}", item['image']])
            try:
                audit_response = client.models.generate_content(model='gemini-3.5-flash', contents=audit_contents)
                st.markdown("### 📋 Executive Wardrobe Analysis")
                st.write(audit_response.text)
            except Exception as e: st.error(f"Audit Error: {e}")

# --- TAB 3: CLICK-TO-ADD WORKSPACE ---
with tab3:
    st.subheader("🎨 Visual Outfit Builder Canvas")
    st.write("Open any folder category bar below and click directly on a piece of clothing to place it onto your moodboard.")
    
    if my_clothes:
        for cat_name, items_list in closet_categories.items():
            with st.expander(f"📁 OPEN {cat_name.upper()} GALLERY", expanded=False):
                cols = st.columns(len(items_list) if len(items_list) < 8 else 8)
                for idx, c_item in enumerate(items_list):
                    with cols[idx % 8]:
                        st.image(c_item['image'], width=110)
                        if st.button(f"➕ Add {c_item['name']}", key=f"add_{c_item['id']}"):
                            if c_item['name'] not in st.session_state.canvas_items:
                                st.session_state.canvas_items.append(c_item['name'])
                                st.rerun()
                                
        st.markdown("---")
        st.markdown("### 🖼️ My Current Outfit Canvas Layout")
        
        if st.session_state.canvas_items:
            clear_cols = st.columns([1, 10])
            with clear_cols[0]:
                if st.button("🗑️ Clear Canvas", type="secondary"):
                    st.session_state.canvas_items = []
                    st.rerun()
            
            canvas_cols = st.columns(len(st.session_state.canvas_items))
            for idx, filename in enumerate(st.session_state.canvas_items):
                for c_item in my_clothes:
                    if c_item['name'] == filename:
                        with canvas_cols[idx]:
                            st.image(c_item['image'], width=130, caption=filename)
                            if st.button("❌ Remove", key=f"rem_{idx}"):
                                st.session_state.canvas_items.remove(filename)
                                st.rerun()
            
            st.markdown("---")
            outfit_title = st.text_input("Name this lookbook creation:", placeholder="e.g., Sophisticated Sunday Dinner")
            if st.button("💾 Save Custom Layout Combo", type="primary"):
                if outfit_title:
                    st.session_state.custom_saved_looks.append({"name": outfit_title, "items": list(st.session_state.canvas_items)})
                    st.success(f"Pinned '{outfit_title}' directly into your personal portfolio database!")
                else:
                    st.warning("Please type a style title name before committing.")
        else:
            st.info("Your canvas moodboard is currently empty. Open a category strip above and select items to build a look.")
        
        if st.session_state.custom_saved_looks:
            st.markdown("---")
            st.subheader("📁 My Custom Curated Gallery Lookbook")
            for look in st.session_state.custom_saved_looks:
                with st.expander(f"⭐ Style Board: {look['name']}", expanded=False):
                    saved_cols = st.columns(len(look['items']))
                    for idx, filename in enumerate(look['items']):
                        for c_item in my_clothes:
                            if c_item['name'] == filename:
                                with saved_cols[idx]:
                                    st.image(c_item['image'], width=140, caption=filename)
