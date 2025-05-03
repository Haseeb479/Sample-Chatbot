import pandas as pd
import streamlit as st
import re
import os

st.set_page_config(page_title="🏡 Home Value Chatbot", layout="centered")

# ========== Load CSV Automatically ==========
CSV_PATH = "us-county-home-value.csv"

@st.cache_data
def load_data():
    if not os.path.exists(CSV_PATH):
        st.error(f"❌ CSV file not found at path: `{CSV_PATH}`")
        return None
    df = pd.read_csv(CSV_PATH)
    df.columns = [col.strip() for col in df.columns]
    df.set_index("CountyCode", inplace=True)
    df.columns = pd.to_datetime(df.columns, errors='coerce')
    df = df.loc[:, df.columns.notnull()]
    return df

# ========== Data Analysis Functions ==========
def get_county_trend(df, county_code, start_year):
    county_data = df.loc[county_code]
    filtered = county_data[county_data.index >= pd.to_datetime(f"{start_year}-01-01")]
    return filtered

def compute_avg_annual_growth(df, county_code, start_year):
    county_data = get_county_trend(df, county_code, start_year)
    start = county_data.iloc[0]
    end = county_data.iloc[-1]
    years = (county_data.index[-1] - county_data.index[0]).days / 365
    return ((end / start) ** (1 / years)) - 1

def get_top_growing_counties(df, since_year=2020, top_n=5):
    growth = {}
    for county in df.index:
        data = df.loc[county]
        data = data[data.index >= pd.to_datetime(f"{since_year}-01-01")]
        if len(data) > 1:
            growth[county] = (data.iloc[-1] - data.iloc[0]) / data.iloc[0]
    sorted_growth = sorted(growth.items(), key=lambda x: x[1], reverse=True)
    return sorted_growth[:top_n]

# ========== Intent Handler ==========
def handle_query(df, user_input):
    user_input_lower = user_input.lower()

    # Extract possible details from prompt
    county_match = re.search(r'county\s*(\d+)', user_input_lower)
    year_match = re.search(r'past\s*(\d+)\s*year', user_input_lower)
    since_year_match = re.search(r'since\s*(\d{4})', user_input_lower)

    county_code = int(county_match.group(1)) if county_match else None
    years = int(year_match.group(1)) if year_match else 5
    since_year = int(since_year_match.group(1)) if since_year_match else 2020
    start_year = 2025 - years

    # 🔥 Handle: Top Counties (No county code needed)
    if "highest increase" in user_input_lower or "top counties" in user_input_lower:
        top = get_top_growing_counties(df, since_year=since_year)
        response = f"🏆 Top Counties Since {since_year}:\n"
        for county, growth in top:
            response += f"- County {county}: {growth * 100:.2f}%\n"
        return response

    # 📈 Handle: County Trend (needs county code)
    elif "market trend" in user_input_lower or "property prices" in user_input_lower:
        if county_code:
            trend = get_county_trend(df, county_code, start_year)
            return f"📈 County {county_code} Trend from {start_year} to 2025:\nStart: {trend.iloc[0]:,.2f}, End: {trend.iloc[-1]:,.2f}"
        else:
            return "❓ Please specify a county code."

    # 📊 Handle: Growth Rate (needs county code)
    elif "growth rate" in user_input_lower or "annual growth" in user_input_lower:
        if county_code:
            growth = compute_avg_annual_growth(df, county_code, start_year)
            return f"📊 Average Annual Growth Rate in County {county_code}: {growth * 100:.2f}%"
        else:
            return "❓ Please specify a county code."

    return "🤖 Sorry, I didn't understand that. Try asking about trends, growth rate, or top counties."


# ========== UI Setup ==========
st.title("🏡 Home Value Chatbot")

df = load_data()

# Session State to Hold Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if df is not None:
    user_input = st.chat_input("hi, im ur real estate assistent ")
    if user_input:
        # Display user message
        st.chat_message("user").markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generate response
        response = handle_query(df, user_input)

        # Display bot response
        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})