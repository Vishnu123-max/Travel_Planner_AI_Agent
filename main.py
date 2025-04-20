import streamlit as st
import os
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.serpapi_tools import SerpApiTools

# --- Page Configuration ---
st.set_page_config(
    page_title="🌍 AI Travel Planner",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Modern UI ---
st.markdown("""
    <style>
    :root {
        --primary-color: #1F618D;
        --accent-color: #48C9B0;
        --bg-color: #F4F6F7;
        --text-dark: #2C3E50;
        --card-radius: 12px;
        --transition: 0.3s ease;
    }

    html, body, .stApp {
        background-color: var(--bg-color);
    }

    .stButton > button {
        background-color: var(--accent-color);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        height: 3em;
        font-size: 1rem;
        transition: var(--transition);
    }

    .stButton > button:hover {
        transform: scale(1.02);
        background-color: #1ABC9C;
    }

    .main-card {
        background-color: white;
        padding: 2rem;
        border-radius: var(--card-radius);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
    }

    .title-block {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 0.3rem;
    }

    .subtitle-block {
        font-size: 1.1rem;
        color: var(--text-dark);
    }

    .travel-summary {
        background-color: white;
        padding: 1.5rem;
        border-radius: var(--card-radius);
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .expander > div {
        background-color: #f7f9fa;
        border-radius: var(--card-radius);
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar UI ---
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/airplane-take-off.png")
    st.markdown("<div class='title-block'>Trip Settings</div>", unsafe_allow_html=True)

    groq_api_key = st.text_input("🔑 GROQ API Key", type="password")
    serpapi_key = st.text_input("🔍 SerpAPI Key", type="password")

    st.divider()

    destination = st.text_input("🌍 Destination", "")
    duration = st.number_input("📅 Trip Duration (days)", min_value=1, max_value=30, value=5)

    budget = st.select_slider(
        "💰 Budget Level",
        options=["Budget", "Moderate", "Luxury"],
        value="Moderate"
    )

    travel_style = st.multiselect(
        "🎯 Travel Style",
        ["Culture", "Nature", "Adventure", "Relaxation", "Food", "Shopping"],
        ["Culture", "Nature"]
    )

# --- Session State ---
if 'travel_plan' not in st.session_state:
    st.session_state.travel_plan = None
if 'qa_expanded' not in st.session_state:
    st.session_state.qa_expanded = False

# --- Main Content ---
st.markdown("<div class='title-block'>🌎 AI Travel Planner</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle-block'>Let AI help you craft the perfect travel experience ✈️</div>", unsafe_allow_html=True)
st.markdown("")

# --- Summary Card ---
st.markdown(f"""
<div class="travel-summary">
    <h4 style="color:#1F618D;">🧭 Trip Overview</h4>
    <ul style="padding-left: 1.2rem;">
        <li><b>Destination:</b> {destination or "N/A"}</li>
        <li><b>Duration:</b> {duration} day(s)</li>
        <li><b>Budget:</b> {budget}</li>
        <li><b>Travel Styles:</b> {', '.join(travel_style) if travel_style else 'N/A'}</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# --- API and Agent Setup ---
try:
    os.environ["GROQ_API_KEY"] = groq_api_key
    os.environ["SERP_API_KEY"] = serpapi_key

    travel_agent = Agent(
        name="Travel Planner",
        model=Groq(id="llama-3.3-70b-versatile"),
        tools=[SerpApiTools()],
        instructions=[
            "You are a travel planning assistant using Groq Llama.",
            "Help users plan their trips by researching destinations, finding attractions, suggesting accommodations, and providing transportation options.",
            "Give relevant live links for each place and hotel you recommend (this is essential).",
            "Always verify current information before making suggestions."
        ],
        show_tool_calls=True,
        markdown=True
    )

    # --- Generate Button ---
    if st.button("✨ Generate My Perfect Travel Plan", type="primary"):
        if destination:
            with st.spinner("🔍 Crafting your trip..."):
                prompt = f"""Create a comprehensive travel plan for {destination} for {duration} days.

Travel Preferences:
- Budget Level: {budget}
- Travel Styles: {', '.join(travel_style)}

Please include:

1. 🌞 Best Time to Visit
2. 🏨 Accommodation (in {budget} range)
3. 🗺️ Day-by-Day Itinerary
4. 🍽️ Local Culinary Experiences
5. 💡 Travel Tips (transportation, etiquette, budget)
6. 💰 Total Estimated Cost

Provide all information in markdown format with proper sections and links.
"""
                response = travel_agent.run(prompt)
                content = getattr(response, 'content', str(response)).replace('∣', '|').replace('\n\n\n', '\n\n')
                st.session_state.travel_plan = content
                st.markdown(content)
        else:
            st.warning("Please enter a destination first.")

    # --- Display Generated Plan (if exists) ---
    if st.session_state.travel_plan:
        st.markdown(st.session_state.travel_plan)

    # --- Q&A Section ---
    st.divider()
    with st.expander("🤔 Ask a specific question about your destination", expanded=st.session_state.qa_expanded):
        st.session_state.qa_expanded = True

        question = st.text_input("Your question:", placeholder="What would you like to know?")
        if st.button("Get Answer", key="qa_button"):
            if question and st.session_state.travel_plan:
                with st.spinner("🧠 Finding the best answer..."):
                    context_question = f"""
I have a travel plan for {destination}. Here's the plan:

{st.session_state.travel_plan}

Now, answer this question:
{question}
"""
                    response = travel_agent.run(context_question)
                    st.markdown(getattr(response, 'content', str(response)))
            elif not st.session_state.travel_plan:
                st.warning("Generate your travel plan first.")
            else:
                st.warning("Please ask a question.")

except Exception as e:
    st.error(f"⚠️ Application Error: {str(e)}")
