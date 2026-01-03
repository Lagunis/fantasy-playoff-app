import streamlit as st
import pandas as pd
import gspread

st.set_page_config(layout="wide", page_title="Playoff Fantasy")

# --- 1. SETUP & CONNECTIONS ---
def get_sheet():
    if "gcp_service_account" not in st.secrets:
        st.error("Secrets not found!")
        return None
    creds = st.secrets["gcp_service_account"]
    gc = gspread.service_account_from_dict(creds)
    sh = gc.open("fantasy_league_db")
    return sh.sheet1

@st.cache_data
def load_players():
    df = pd.read_csv('players.csv')
    # 1. UI CHANGE: Create the "Name (Team)" format
    df['display_name'] = df['name'] + " (" + df['team'] + ")"
    return df

try:
    all_players = load_players()
except:
    st.error("CRITICAL ERROR: Could not find players.csv")
    st.stop()

if 'my_roster' not in st.session_state:
    st.session_state['my_roster'] = []

# --- 2. HEADER & LOGIN ---
st.title("🏈 Playoff Draft Board")

with st.expander("Manager Login & Tools", expanded=True):
    col_login, col_btn = st.columns([3, 1])
    with col_login:
        owner_name = st.text_input("Manager Name", "User 1")
    with col_btn:
        st.write("") 
        if st.button("📂 Load Saved Roster"):
            try:
                sheet = get_sheet()
                records = sheet.get_all_records()
                df_cloud = pd.DataFrame(records)
                
                if not df_cloud.empty and owner_name in df_cloud['Manager'].values:
                    saved_str = df_cloud.loc[df_cloud['Manager'] == owner_name, 'Roster'].iloc[0]
                    # We need to map the stored "Name" back to our list
                    # (Assuming saved roster stores raw names, not display names)
                    # For simplicity in this version, let's assume we save the raw name 
                    # but we need to match it to 'display_name' for the UI.
                    saved_raw_names = saved_str.split(", ")
                    
                    # Reconstruct the display names
                    restored_roster = all_players[all_players['name'].isin(saved_raw_names)]['display_name'].tolist()
                    
                    st.session_state['my_roster'] = restored_roster
                    st.toast(f"Roster loaded for {owner_name}!", icon="✅")
                    st.rerun()
                else:
                    st.toast("No saved team found.", icon="⚠️")
            except:
                st.error("Connection failed.")

# --- 3. THE TOP DASHBOARD (UI CHANGE #2) ---
# We calculate stats BEFORE rendering the columns so we can show them at the top
current_roster_names = st.session_state['my_roster']
my_team_data = all_players[all_players['display_name'].isin(current_roster_names)]

# Calculate Counts
counts = my_team_data['position'].value_counts().to_dict()
def get_count(pos): return counts.get(pos, 0)

qb, rb, wr, te = get_count("QB"), get_count("RB"), get_count("WR"), get_count("TE")
k, def_ = get_count("K"), get_count("DEF")
flex = max(0, rb-2) + max(0, wr-2) + max(0, te-1)
total_pts = my_team_data['projected_points'].sum()

# Render the Dashboard
st.divider()
dash_col1, dash_col2, dash_col3 = st.columns([1, 3, 1])

with dash_col1:
    st.metric("Projected Score", f"{total_pts:.1f}")
    st.write(f"**Players:** {len(current_roster_names)}/10")

with dash_col2:
    # A visual status bar for positions
    st.write("##### Roster Requirements")
    # Using columns for the little status indicators
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    s1.markdown(f"**QB**<br>{'✅' if qb==1 else '❌'} {qb}/1", unsafe_allow_html=True)
    s2.markdown(f"**RB**<br>{'✅' if rb>=2 else '⚠️'} {rb}", unsafe_allow_html=True)
    s3.markdown(f"**WR**<br>{'✅' if wr>=2 else '⚠️'} {wr}", unsafe_allow_html=True)
    s4.markdown(f"**TE**<br>{'✅' if te>=1 else '⚠️'} {te}", unsafe_allow_html=True)
    s5.markdown(f"**K**<br>{'✅' if k==1 else '❌'} {k}/1", unsafe_allow_html=True)
    s6.markdown(f"**DEF**<br>{'✅' if def_==1 else '❌'} {def_}/1", unsafe_allow_html=True)
    
    # Flex Check
    if flex > 2: st.error(f"Too many Flex players! ({flex}/2)")
    elif flex <= 2: st.caption(f"Flex Slots Used: {flex}/2")

with dash_col3:
    # Save Button Area
    valid_roster = (qb==1 and rb>=2 and wr>=2 and te>=1 and flex<=2 and k==1 and def_==1 and len(current_roster_names)==10)
    
    if valid_roster:
        if st.button("💾 Submit Roster", type="primary", use_container_width=True):
            with st.spinner("Saving..."):
                sheet = get_sheet()
                if sheet:
                    # Save the RAW names, not the display names (cleaner for database)
                    raw_names = my_team_data['name'].tolist()
                    roster_str = ", ".join(raw_names)
                    
                    records = sheet.get_all_records()
                    df_cloud = pd.DataFrame(records)
                    
                    new_row = {"Manager": owner_name, "Roster": roster_str, "Points": total_pts}
                    
                    if not df_cloud.empty and 'Manager' in df_cloud.columns:
                        df_cloud = df_cloud[df_cloud['Manager'] != owner_name]
                    
                    df_cloud = pd.concat([df_cloud, pd.DataFrame([new_row])], ignore_index=True)
                    sheet.clear()
                    sheet.update([df_cloud.columns.values.tolist()] + df_cloud.values.tolist())
                    st.success("Saved!")
    else:
        st.button("Roster Invalid", disabled=True, use_container_width=True)

st.divider()

# --- 4. THE DRAFT BOARD HELPER ---
def render_position_table(position_name, header_text):
    # 1. Get players
    pos_df = all_players[all_players['position'] == position_name].copy()
    
    # 2. Mark checks based on current session state
    pos_df['Draft'] = pos_df['display_name'].isin(st.session_state['my_roster'])
    
    # 3. BUG FIX: Sort ONLY by points. Do NOT sort by 'Draft'.
    # This prevents the rows from jumping around when you click them.
    pos_df = pos_df.sort_values(by=['projected_points'], ascending=False)
    
    st.subheader(header_text)
    
    # 4. Render Table
    edited_df = st.data_editor(
        pos_df[['Draft', 'display_name', 'projected_points']], 
        key=f"editor_{position_name}",
        hide_index=True,
        column_config={
            "Draft": st.column_config.CheckboxColumn(
                "Pick",
                width="small",
                default=False,
            ),
            "display_name": st.column_config.TextColumn(
                "Player",
                width="large", 
            ),
            "projected_points": st.column_config.NumberColumn(
                "Pts",
                format="%.1f",
                width="small"
            )
        },
        disabled=["display_name", "projected_points"],
        height=450
    )
    
    return edited_df[edited_df['Draft'] == True]['display_name'].tolist()

# --- 5. THE 6-COLUMN LAYOUT ---
c1, c2, c3, c4, c5, c6 = st.columns(6)

# UI CHANGE #4: Updated header text
with c1:
    sel_qb = render_position_table("QB", "QB (Pick 1)")
with c2:
    sel_rb = render_position_table("RB", "RB (Pick 2-4)")
with c3:
    sel_wr = render_position_table("WR", "WR (Pick 2-4)")
with c4:
    sel_te = render_position_table("TE", "TE (Pick 1-3)")
with c5:
    sel_k = render_position_table("K", "K (Pick 1)")
with c6:
    sel_def = render_position_table("DEF", "DEF (Pick 1)")

# Combine selections
current_selection = sel_qb + sel_rb + sel_wr + sel_te + sel_k + sel_def

# Update session state for next run
st.session_state['my_roster'] = current_selection
