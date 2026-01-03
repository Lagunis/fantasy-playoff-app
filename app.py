import streamlit as st
import pandas as pd
import gspread

st.set_page_config(layout="wide")
st.title("🏆 Playoff Fantasy Manager 2026")

# --- GOOGLE SHEETS CONNECTION ---
# This function connects to Google and returns the "Sheet1" worksheet
def get_sheet():
    # access the secrets you pasted into the Streamlit dashboard
    creds = st.secrets["gcp_service_account"]

    # Authenticate using the dictionary, not a file
    gc = gspread.service_account_from_dict(creds)

    # Open the sheet
    sh = gc.open("fantasy_league_db")
    return sh.sheet1

# --- DATA LOADING (PLAYERS) ---
# We still keep players local for speed, but you could move this to Sheets too!
@st.cache_data
def load_players():
    return pd.read_csv('players.csv')

all_players = load_players()

# --- DATA LOADING (TEAMS FROM GOOGLE) ---
# We don't cache this strictly because we want fresh updates
def load_teams_from_sheet():
    worksheet = get_sheet()
    # get_all_records returns a list of dictionaries, perfect for DataFrame
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# --- CONFIGURATION ---
ROSTER_LIMITS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1}

# --- SIDEBAR: DRAFT ROOM ---
st.sidebar.header("Draft Room")
owner_name = st.sidebar.text_input("Manager Name (Type to Login)", "User 1")

# --- LOGIN LOGIC ---
default_roster = []
# Try to load existing teams. If the sheet is empty, handle the error gracefully.
try:
    teams_df = load_teams_from_sheet()
    
    # Check if user exists
    if not teams_df.empty and owner_name in teams_df['Manager'].values:
        st.sidebar.success(f"Welcome back, {owner_name}!")
        saved_roster_str = teams_df.loc[teams_df['Manager'] == owner_name, 'Roster'].iloc[0]
        saved_list = saved_roster_str.split(", ")
        default_roster = [p for p in saved_list if p in all_players['name'].tolist()]
except Exception as e:
    # If sheet is empty or has issues, start with empty dataframe
    teams_df = pd.DataFrame(columns=["Manager", "Roster", "Points"])

# --- DRAFT INTERFACE ---
available_players = all_players['name'].tolist()

selected_names = st.sidebar.multiselect(
    "Select your 10 Starters:",
    options=available_players,
    default=default_roster
)

# --- CORE LOGIC ---
if selected_names:
    my_team = all_players[all_players['name'].isin(selected_names)]
    total_projected = my_team['projected_points'].sum()
    
    # Validation Logic
    counts = my_team['position'].value_counts().to_dict()
    def get_count(pos): return counts.get(pos, 0)
    qb, rb, wr, te, k, def_ = get_count("QB"), get_count("RB"), get_count("WR"), get_count("TE"), get_count("K"), get_count("DEF")
    flex = max(0, rb-2) + max(0, wr-2) + max(0, te-1)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"{owner_name}'s Lineup")
        st.dataframe(my_team)
        st.metric("Total Projected Points", f"{total_projected:.2f}")
    
    with col2:
        st.subheader("Roster Status")
        valid_roster = True
        if qb != 1: valid_roster = False
        if rb < 2: valid_roster = False
        if wr < 2: valid_roster = False
        if te < 1: valid_roster = False
        if flex > 2: valid_roster = False
        if k != 1: valid_roster = False
        if def_ != 1: valid_roster = False
        
        if valid_roster:
            st.success("Roster Valid ✅")
        else:
            st.error("Roster Invalid ❌")

    # --- SAVE TO GOOGLE SHEETS ---
    st.divider()
    
    if len(selected_names) == 10 and valid_roster:
        btn_label = "🔄 Update Team" if default_roster else "💾 Save New Team"
        
        if st.button(btn_label):
            with st.spinner('Saving to Google Cloud...'):
                roster_string = ", ".join(selected_names)
                
                # 1. Get the current sheet object
                worksheet = get_sheet()
                
                # 2. Logic: It's hard to "edit" a specific cell in Sheets without complexity.
                # EASIEST WAY: Read all data, update in Python, clear sheet, write all back.
                
                # Get fresh data
                current_data = worksheet.get_all_records()
                df_cloud = pd.DataFrame(current_data)
                
                # Create the new row
                new_row = {
                    "Manager": owner_name,
                    "Roster": roster_string,
                    "Points": total_projected
                }
                
                # Remove old entry if it exists
                if not df_cloud.empty:
                    df_cloud = df_cloud[df_cloud['Manager'] != owner_name]
                
                # Add new entry
                df_cloud = pd.concat([df_cloud, pd.DataFrame([new_row])], ignore_index=True)
                
                # Sort by points
                df_cloud = df_cloud.sort_values(by="Points", ascending=False)
                
                # 3. WRITE BACK TO GOOGLE
                worksheet.clear() # Wipe the sheet
                # update([headers] + [data])
                worksheet.update([df_cloud.columns.values.tolist()] + df_cloud.values.tolist())
                
                st.success(f"Saved to cloud! Check your Google Sheet.")
                st.rerun()

# --- LEAGUE STANDINGS ---
st.divider()
st.header("🏆 League Standings")

# We reload data here to ensure we see the latest updates
try:
    live_standings = load_teams_from_sheet()
    if not live_standings.empty:
        # Sort by points (descending)
        live_standings = live_standings.sort_values(by="Points", ascending=False)
        st.dataframe(live_standings)
    else:
        st.write("No teams in the league yet.")
except:

    st.write("Connecting to league database...")
