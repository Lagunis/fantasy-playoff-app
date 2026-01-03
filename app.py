import streamlit as st
import pandas as pd
import gspread
import hashlib
import os
import base64 # Required for the background image

st.set_page_config(layout="wide", page_title="Playoff Fantasy")

# --- 1. SECURITY & DATABASE SETUP ---
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

def get_connection():
    if "gcp_service_account" not in st.secrets:
        st.error("Secrets not found!")
        return None
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    return gc

# --- 2. CSS & BACKGROUND HELPERS ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_bg_hack(main_bg):
    '''
    A function to unpack an image from disk and set as the full background.
    '''
    # set bg name
    main_bg_ext = "png"
    
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
             background-size: cover;
             background-repeat: no-repeat;
             background-attachment: fixed;
             background-position: center;
         }}
         /* Make the header transparent */
         header {{visibility: hidden;}}
         
         /* Create a 'Glass' effect for the login container */
         div[data-testid="stExpander"] {{
             background-color: rgba(255, 255, 255, 0.9); /* White with 10% transparency */
             border-radius: 15px;
             padding: 20px;
             box-shadow: 0 4px 6px rgba(0,0,0,0.3);
         }}
         
         /* Improve tab visibility */
         .stTabs [data-baseweb="tab-list"] {{
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 10px;
         }}
         
         /* Make titles pop against background */
         h1, h2, h3 {{
             text-shadow: 2px 2px 4px #000000;
             color: white !important;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

def clear_bg():
    # Resets the background for the main app so it's readable
    st.markdown(
        """
        <style>
        .stApp {
            background: none;
            background-color: #0e1117; /* Default dark mode color */
        }
        h1, h2, h3 {
             text-shadow: none;
             color: inherit !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 3. AUTHENTICATION FUNCTIONS ---
def create_user(email, password, manager_name):
    gc = get_connection()
    sh = gc.open("fantasy_league_db")
    worksheet = sh.worksheet("users")
    
    df = pd.DataFrame(worksheet.get_all_records())
    if not df.empty and email in df['email'].values:
        return False, "Email already registered."
    
    new_user = [email, make_hashes(password), manager_name]
    worksheet.append_row(new_user)
    return True, "Account created! Please log in."

def verify_login(email, password):
    gc = get_connection()
    sh = gc.open("fantasy_league_db")
    worksheet = sh.worksheet("users")
    
    df = pd.DataFrame(worksheet.get_all_records())
    if df.empty: return False, "No users found."
    
    if email in df['email'].values:
        user_row = df[df['email'] == email].iloc[0]
        if check_hashes(password, user_row['password']):
            return True, user_row['manager_name']
            
    return False, "Incorrect email or password."

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'manager_name' not in st.session_state:
    st.session_state['manager_name'] = ""
if 'my_roster' not in st.session_state:
    st.session_state['my_roster'] = []

# --- 5. LANDING PAGE ---
def login_page():
    # 1. APPLY BACKGROUND
    # Check for your local file
    if os.path.exists("football_intro.jpg"):
        set_bg_hack("football_intro.jpg")
    elif os.path.exists("football_intro.png"):
        set_bg_hack("football_intro.png")
    else:
        # Fallback if file missing (optional: remove if you always have the file)
        st.warning("Upload 'football_intro.jpg' to see the background!")

    # 2. LAYOUT: Center the content
    # We use columns to create a centered 'card'
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c2:
        st.title("🏆 Playoff Fantasy League")
        st.write("### Welcome to the Arena")
        
        # DETAILS DROPDOWN (Styled by CSS above to look like a card)
        with st.expander("📖 READ ME: League Rules & Scoring", expanded=False):
            st.markdown("""
            **The Mission:** Draft the highest-scoring team across all 4 rounds of the playoffs.
            
            **The Roster:** 10 Players (1 QB, 2 RB, 2 WR, 1 TE, 2 FLEX, 1 K, 1 DEF).
            
            **The Multipliers 🚀:**
            * **Week 1:** 100% Points
            * **Week 2 Streak:** 110% Bonus
            * **Week 3 Streak:** 125% Bonus
            * **Week 4 Streak:** 150% Bonus
            *(Must play the same player consecutively to earn bonuses)*
            """)
        
        st.divider()
        
        # LOGIN TABS
        # We put these inside a container to benefit from the CSS styling if possible
        # but Streamlit tabs are tricky. The CSS above targets them specifically.
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type='password', key="login_pass")
            st.write("")
            if st.button("Enter League", use_container_width=True, type="primary"):
                is_valid, name = verify_login(email, password)
                if is_valid:
                    st.session_state['logged_in'] = True
                    st.session_state['manager_name'] = name
                    st.rerun()
                else:
                    st.error(name)
                    
        with tab2:
            new_email = st.text_input("Enter Email", key="signup_email")
            new_user_name = st.text_input("Manager Name", placeholder="e.g. Coach Lasso", key="signup_name")
            new_password = st.text_input("Create Password", type='password', key="signup_pass")
            st.write("")
            
            if st.button("Join the League", use_container_width=True):
                if new_email and new_password and new_user_name:
                    success, msg = create_user(new_email, new_password, new_user_name)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill out all fields.")

# --- 6. MAIN APP ---
def main_game_app():
    # RESET BACKGROUND to clean dark mode for readability
    clear_bg()
    
    owner_name = st.session_state['manager_name']

    def get_sheet():
        gc = get_connection()
        return gc.open("fantasy_league_db").sheet1

    @st.cache_data
    def load_players():
        df = pd.read_csv('players.csv')
        df['display_name'] = df['name'] + " (" + df['team'] + ")"
        return df

    try:
        all_players = load_players()
    except:
        st.error("CRITICAL ERROR: Could not find players.csv")
        st.stop()

    # TOP BAR
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title(f"🏈 {owner_name}'s War Room")
    with c2:
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.rerun()

    with st.expander("League Controls", expanded=True):
        col_week, col_load = st.columns([1, 1])
        with col_week:
            current_week = st.selectbox("Current Week", [1, 2, 3, 4])
        with col_load:
             st.write("") 
             if st.button("📂 Reload My Roster"):
                try:
                    sheet = get_sheet()
                    records = sheet.get_all_records()
                    df_cloud = pd.DataFrame(records)
                    if not df_cloud.empty and owner_name in df_cloud['Manager'].values:
                        target_col = f"Roster_{current_week}"
                        user_row = df_cloud[df_cloud['Manager'] == owner_name].iloc[0]
                        if target_col in user_row and user_row[target_col]:
                            saved_str = user_row[target_col]
                            saved_raw_names = saved_str.split(", ")
                            restored_roster = all_players[all_players['name'].isin(saved_raw_names)]['name'].tolist()
                            st.session_state['my_roster'] = restored_roster
                            st.toast(f"Week {current_week} Roster Loaded!", icon="✅")
                            st.rerun()
                        else:
                            st.toast(f"No roster found for Week {current_week}.", icon="ℹ️")
                            st.session_state['my_roster'] = []
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # MULTIPLIER LOGIC
    def calculate_multipliers(manager, week_num):
        multipliers = {}
        for name in all_players['name']: multipliers[name] = 1.0
        if week_num == 1: return multipliers

        try:
            sheet = get_sheet()
            records = sheet.get_all_records()
            df = pd.DataFrame(records)
            if df.empty or manager not in df['Manager'].values: return multipliers
            
            user_row = df[df['Manager'] == manager].iloc[0]
            
            def was_in_week(p_name, w):
                col = f"Roster_{w}"
                if col in user_row and user_row[col]:
                    return p_name in user_row[col].split(", ")
                return False

            for name in all_players['name']:
                streak = 0
                if was_in_week(name, week_num - 1):
                    streak = 1
                    if week_num > 2 and was_in_week(name, week_num - 2):
                        streak = 2
                        if week_num > 3 and was_in_week(name, week_num - 3):
                            streak = 3
                
                if streak == 1: multipliers[name] = 1.10
                elif streak == 2: multipliers[name] = 1.25
                elif streak == 3: multipliers[name] = 1.50
        except: pass
        return multipliers

    player_multipliers = calculate_multipliers(owner_name, current_week)

    dashboard_placeholder = st.container()
    st.divider()

    # RENDER TABLES
    def render_position_table(position_name, header_text):
        pos_df = all_players[all_players['position'] == position_name].copy()
        
        if 'my_roster' not in st.session_state: st.session_state['my_roster'] = []
        pos_df['Draft'] = pos_df['name'].isin(st.session_state['my_roster'])
        pos_df['mult'] = pos_df['name'].map(player_multipliers)
        
        def format_name(row):
            base = row['display_name']
            m = row['mult']
            if m == 1.10: return f"{base} ⚡ 1.1x"
            elif m == 1.25: return f"{base} 🔥 1.25x"
            elif m == 1.50: return f"{base} 🚀 1.5x"
            else: return base

        pos_df['ui_name'] = pos_df.apply(format_name, axis=1)
        pos_df['boosted_points'] = pos_df['projected_points'] * pos_df['mult']
        pos_df = pos_df.sort_values(by=['boosted_points'], ascending=False)
        
        st.subheader(header_text)
        edited_df = st.data_editor(
            pos_df[['Draft', 'ui_name', 'boosted_points']], 
            key=f"editor_{position_name}", hide_index=True,
            column_config={
                "Draft": st.column_config.CheckboxColumn("Pick", width="small", default=False),
                "ui_name": st.column_config.TextColumn("Player", width="large"),
                "boosted_points": st.column_config.NumberColumn("Pts", format="%.1f", width="small")
            },
            disabled=["ui_name", "boosted_points"], height=450
        )
        
        selected_ui_names = edited_df[edited_df['Draft'] == True]['ui_name'].tolist()
        return pos_df[pos_df['ui_name'].isin(selected_ui_names)]['name'].tolist()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: sel_qb = render_position_table("QB", "QB (Pick 1)")
    with c2: sel_rb = render_position_table("RB", "RB (Pick 2-4)")
    with c3: sel_wr = render_position_table("WR", "WR (Pick 2-4)")
    with c4: sel_te = render_position_table("TE", "TE (Pick 1-3)")
    with c5: sel_k = render_position_table("K", "K (Pick 1)")
    with c6: sel_def = render_position_table("DEF", "DEF (Pick 1)")

    current_selection = sel_qb + sel_rb + sel_wr + sel_te + sel_k + sel_def
    st.session_state['my_roster'] = current_selection

    with dashboard_placeholder:
        my_team_data = all_players[all_players['name'].isin(current_selection)].copy()
        my_team_data['mult'] = my_team_data['name'].map(player_multipliers)
        my_team_data['boosted_points'] = my_team_data['projected_points'] * my_team_data['mult']
        total_pts = my_team_data['boosted_points'].sum()
        
        counts = my_team_data['position'].value_counts().to_dict()
        def get_count(pos): return counts.get(pos, 0)
        qb, rb, wr, te = get_count("QB"), get_count("RB"), get_count("WR"), get_count("TE")
        k, def_ = get_count("K"), get_count("DEF")
        flex = max(0, rb-2) + max(0, wr-2) + max(0, te-1)

        d1, d2, d3 = st.columns([1, 3, 1])
        with d1:
            st.metric("Projected Score", f"{total_pts:.1f}")
            st.write(f"**Players:** {len(current_selection)}/10")
        with d2:
            st.write("##### Roster Requirements")
            s1, s2, s3, s4, s5, s6 = st.columns(6)
            s1.markdown(f"**QB**<br>{'✅' if qb==1 else '❌'} {qb}/1", unsafe_allow_html=True)
            s2.markdown(f"**RB**<br>{'✅' if rb>=2 else '⚠️'} {rb}", unsafe_allow_html=True)
            s3.markdown(f"**WR**<br>{'✅' if wr>=2 else '⚠️'} {wr}", unsafe_allow_html=True)
            s4.markdown(f"**TE**<br>{'✅' if te>=1 else '⚠️'} {te}", unsafe_allow_html=True)
            s5.markdown(f"**K**<br>{'✅' if k==1 else '❌'} {k}/1", unsafe_allow_html=True)
            s6.markdown(f"**DEF**<br>{'✅' if def_==1 else '❌'} {def_}/1", unsafe_allow_html=True)
            if flex > 2: st.error(f"Too many Flex! ({flex}/2)")
        with d3:
            valid_roster = (qb==1 and rb>=2 and wr>=2 and te>=1 and flex<=2 and k==1 and def_==1 and len(current_selection)==10)
            if valid_roster:
                if st.button(f"💾 Submit Week {current_week}", type="primary", use_container_width=True, key="save_btn"):
                    with st.spinner("Saving..."):
                        sheet = get_sheet()
                        if sheet:
                            raw_names = my_team_data['name'].tolist()
                            roster_str = ", ".join(raw_names)
                            records = sheet.get_all_records()
                            df_cloud = pd.DataFrame(records)
                            
                            if df_cloud.empty or owner_name not in df_cloud['Manager'].values:
                                new_row = {"Manager": owner_name}
                                df_cloud = pd.concat([df_cloud, pd.DataFrame([new_row])], ignore_index=True)
                            
                            idx = df_cloud.index[df_cloud['Manager'] == owner_name].tolist()[0]
                            df_cloud.at[idx, f'Roster_{current_week}'] = roster_str
                            df_cloud.at[idx, f'Points_{current_week}'] = total_pts
                            
                            sheet.clear()
                            sheet.update([df_cloud.columns.values.tolist()] + df_cloud.values.tolist())
                            st.success(f"Week {current_week} Saved!")
            else:
                st.button("Roster Invalid", disabled=True, use_container_width=True)

# --- 6. PAGE ROUTER ---
if st.session_state['logged_in']:
