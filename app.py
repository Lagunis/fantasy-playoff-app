import streamlit as st
import pandas as pd
import gspread

st.set_page_config(layout="wide")
st.title("🏆 Playoff Fantasy Manager 2026")

# --- GOOGLE SHEETS CONNECTION (CLOUD VERSION) ---
def get_sheet():
    # We use st.secrets to get the credentials from the Streamlit website
    # This prevents us from needing the 'credentials.json' file
    if "gcp_service_account" not in st.secrets:
        st.error("Secrets not found! Make sure you pasted the TOML into Streamlit Settings.")
        return None
        
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("fantasy_league_db")
    return sh.sheet1

# --- DATA LOADING ---
@st.cache_data
def load_players():
    # Make sure players.csv is in your GitHub repo!
    return pd.read_csv('players.csv')

try:
    all_players = load_players()
except:
    st.error("Could not find players.csv. Is it uploaded to GitHub?")
    st.stop()

def load_teams_from_sheet():
    worksheet = get_sheet()
    if worksheet:
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    return pd.DataFrame()

# --- CONFIGURATION ---
ROSTER_LIMITS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1}

# --- SIDEBAR: LOGIN ---
st.sidebar.header("Draft Room")
owner_name = st.sidebar.text_input("Manager Name", "User 1")

default_roster = []

# Try to load existing roster for this user
try:
    teams_df = load_teams_from_sheet()
    if not teams_df.empty and owner_name in teams_df['Manager'].values:
        st.sidebar.success(f"Welcome back, {owner_name}!")
        saved_roster_str = teams_df.loc[teams_df['Manager'] == owner_name, 'Roster'].iloc[0]
        # Clean up the string and match with current player list
        saved_list = saved_roster_str.split(", ")
        default_roster = [p for p in saved_list if p in all_players['name'].tolist()]
except Exception as e:
    # If connection fails, just proceed with empty roster
    print(f"Database error: {e}")

# --- DRAFT INTERFACE ---
available_players = all_players['name'].tolist()

selected_names = st.sidebar.multiselect(
    "Select your Starters:",
    options=available_players,
    default=default_roster
)

# --- DASHBOARD LOGIC ---
if selected_names:
    my_team = all_players[all_players['name'].isin(selected_names)]
    total_projected = my_team['projected_points'].sum()
    
    # Count positions
    counts = my_team['position'].value_counts().to_dict()
    def get_count(pos): return counts.get(pos, 0)
    
    qb = get_count("QB")
    rb = get_count("RB")
    wr = get_count("WR")
    te = get_count("TE")
    k  = get_count("K")
    def_ = get_count("DEF")
    flex = max(0, rb-2) + max(0, wr-2) + max(0, te-1)

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"{owner_name}'s Lineup")
        st.dataframe(my_team)
        st.metric("Total Projected Points", f"{total_projected:.2f}")

    with col2:
        st.subheader("Roster Status")
        
        # LOGIC: Show warnings but don't crash
        if qb != 1: st.warning(f"⚠️ QB: {qb}/1")
        else: st.success("✅ QB: 1/1")
            
        if rb < 2: st.warning(f"⚠️ RB: {rb} (min 2)")
        else: st.success(f"✅ RB: {rb}")
            
        if wr < 2: st.warning(f"⚠️ WR: {wr} (min 2)")
        else: st.success(f"✅ WR: {wr}")
            
        if flex > 2: st.error(f"❌ FLEX: {flex}/2 (Too many!)")
        elif flex < 2: st.info(f"ℹ️ FLEX: {flex}/2")
        else: st.success("✅ FLEX: 2/2")

    # --- SAVING SYSTEM (TESTING MODE) ---
    st.divider()
    
    # Allow saving if ANY player is selected (easiest for testing)
    if len(selected_names) > 0:
        btn_label = "🔄 Update Team" if default_roster else "💾 Save Team"
        
        if st.button(btn_label):
            with st.spinner('Saving to Google Cloud...'):
                worksheet = get_sheet()
                
                if worksheet:
                    roster_string = ", ".join(selected_names)
                    
                    # Read current data
                    current_data = worksheet.get_all_records()
                    df_cloud = pd.DataFrame(current_data)
                    
                    # Prepare new row
                    new_row = {
                        "Manager": owner_name,
                        "Roster": roster_string,
                        "Points": total_projected
                    }
                    
                    # Remove old entry if exists
                    if not df_cloud.empty and 'Manager' in df_cloud.columns:
                        df_cloud = df_cloud[df_cloud['Manager'] != owner_name]
                    
                    # Add new entry
                    df_cloud = pd.concat([df_cloud, pd.DataFrame([new_row])], ignore_index=True)
                    
                    # Sort if we have points
                    if 'Points' in df_cloud.columns:
                        df_cloud = df_cloud.sort_values(by="Points", ascending=False)
                    
                    # Write back to Google
                    worksheet.clear()
                    worksheet.update([df_cloud.columns.values.tolist()] + df_cloud.values.tolist())
                    
                    st.success(f"Saved to Cloud! Check your Google Sheet.")
                    st.rerun()
                else:
                    st.error("Could not connect to Google Sheets.")

# --- LEAGUE STANDINGS ---
st.divider()
st.header("🏆 League Standings")

try:
    live_standings = load_teams_from_sheet()
    if not live_standings.empty:
        if 'Points' in live_standings.columns:
            live_standings = live_standings.sort_values(by="Points", ascending=False)
        st.dataframe(live_standings)
    else:
        st.write("No teams yet. Be the first!")
except:
    st.write("Loading standings...")
