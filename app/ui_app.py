import os
import pandas as pd
import ast
import streamlit as st
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# 🌐 Streamlit config
st.set_page_config(page_title="AI Smart Leftovers Manager 🍱", layout="centered")

# 🌈 Theme-aware CSS
st.markdown("""
    <style>
        .main {
            padding: 2rem;
        }
        h1, h2, h3 {
            color: var(--text-color);
        }
        .stForm {
            background-color: var(--background-color);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .stButton>button {
            background-color: #ff4b4b;
            color: white;
            font-weight: bold;
            border: none;
            border-radius: 5px;
            padding: 0.5rem 1rem;
        }
        .stTextInput input {
            background-color: var(--secondary-background-color);
            color: var(--text-color);
        }
        div[data-testid="stFormSubmitButton"] {
            margin-bottom: 0;
        }
    </style>
""", unsafe_allow_html=True)

# 🔖 Header
st.markdown("## 👩‍🍳AI Smart Leftovers Manager")
st.markdown("#### *Turn your leftover ingredients into delicious recipes using AI!* ✨")
st.markdown("---")

# 🔐 Gemini API Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyBt8T3jvv93HmsQguY4-InsPTzpNrr6yBM"
llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash-latest", temperature=0.4)

# 📦 Load recipe data with only needed columns
@st.cache_data
def load_data():
    df = pd.read_csv("data/RAW_recipes.csv")
    df = df[["Name", "RecipeIngredientParts", "Calories", "FatContent", "ProteinContent", "CarbohydrateContent"]].dropna()
    df.rename(columns={
        "Name": "name",
        "RecipeIngredientParts": "ingredients"
    }, inplace=True)

    def clean_ingredients(raw):
        if raw.startswith("c("):
            cleaned = raw.replace('c(', '[').replace(')', ']').replace('"', "'")
            try:
                return ", ".join(ast.literal_eval(cleaned)).lower()
            except Exception:
                return ""
        return ""

    df["ingredients"] = df["ingredients"].apply(clean_ingredients)
    df = df[df["ingredients"] != ""]
    return df

# ✅ Cache TF-IDF for faster loading
@st.cache_data
def get_vectorizer_and_matrix(ingredients_list):
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(ingredients_list)
    return vectorizer, matrix

# 🚀 Load data with spinner
with st.spinner("📦 Loading recipes... Hang tight!"):
    df = load_data()
    vectorizer, tfidf_matrix = get_vectorizer_and_matrix(df["ingredients"])

# 📝 Input form
with st.container():
    with st.form("input_form"):
        st.markdown("🍽️ **Enter your ingredients** to see what you can cook:")
        ingredients = st.text_input("Leftovers", placeholder="e.g., rice, onion, pasta")
        st.markdown("🎯 **Preferences** *(Optional)* — vegetarian, quick, spicy etc.")
        preferences = st.text_input("Preferences", placeholder="e.g., spicy, sweet, healthy")
        submitted = st.form_submit_button("🔍 Find Recipes")

# 🚀 On Submit
if submitted and ingredients:
    # Direct Gemini query — skip vector similarity
    with st.spinner("👨‍🍳 Generating Tasty Recipes For You..."):
        prompt = (
            f"You are a professional chef assistant helping users make meals from leftover ingredients."
            f"This meal is for a human, only give recipes for animals if asked."
            f"Your task is to take the ingredients and suggest 3 real-world recipe that only uses them or common pantry staples."
            f"Don't hallucinate unrelated ingredients like beef or pizza if not mentioned."
            f"Always keep the ingredients strictly to the list or standard human pantry items (e.g. oil, salt, pepper)."
            f"Use these leftovers: {ingredients}"
            f"Preferences: {preferences}"
            f"Respond in markdown format with headings:\n"
            f"### 🍽️ Recipe Name\n"
            f"**Nutrition Info:**\n"
            f"- Calories\n- Fat\n- Carbs\n- Protein\n"
            f"**Instructions:**\n1. Step-by-step...\n"
            f"**Tips:**\n- Optional tips here"
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        result = response.content.strip() if isinstance(response.content, str) else str(response.content)

    # Display full response
    st.subheader("📋 Delicious Recipes For Your Leftovers:")
    st.markdown(result)

# 📎 Footer
st.markdown("---")
st.caption("© 2025 AI Smart Leftovers Manager 🍱")
