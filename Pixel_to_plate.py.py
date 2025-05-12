import os
import streamlit as st
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

GOOGLE_API_KEY = "AIzaSyCr35hxFrpVsbNWgqOwU6PwmkpwLmO2dJA"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

from together import Together
os.environ["TOGETHER_API_KEY"] = "43db26fd2d288ee094966557dd2f2c2621cd3b4956c72a382b9ff36c25808531"
client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

# Dietary Planner Agent
dietary_planner = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    description="Creates personalized dietary plans based on user input.",
    instructions=[
        "Generate a diet plan with breakfast, lunch, dinner, and snacks.",
        "Consider dietary preferences like Keto, Vegetarian, or Low Carb.",
        "Ensure proper hydration and electrolyte balance.",
        "Provide nutritional breakdown including macronutrients and vitamins.",
        "Suggest meal preparation tips for easy implementation.",
    ],
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    markdown=True
)

def generate_recipe_with_deepseek(ingredients, age, weight, height, activity_level, dietary_preference, fitness_goal, custom_prompt=""):
    prompt = (
        "You are a logical chef who carefully thinks through each step of recipe creation.\n"
        f"Based on the following ingredients: {ingredients}, create a healthy and personalized recipe for a "
        f"{age}-year-old person weighing {weight}kg and {height}cm tall, with a '{activity_level}' activity level. "
        f"The person follows a '{dietary_preference}' diet and their fitness goal is '{fitness_goal}'."
        f"\nAdditional User Preferences: {custom_prompt.strip()}\n"
        "1. Identify the main ingredient.\n"
        "2. Suggest complementary ingredients.\n"
        "3. Determine the best cooking method.\n"
        "4. Provide a recipe name, ingredient list, step-by-step cooking instructions.\n"
        "5. Mention the cooking time, servings, and a brief nutritional breakdown (macronutrients).\n"
        "6. List any extra ingredients required beyond the provided ones.\n\n"
    )

    # Add custom user prompt to the thinking part
    # if custom_prompt.strip():
    #     prompt += 

    prompt += "\nPlease enclose your thought process in <think>...</think> tags and write clearly.\n\nRecipe:"

    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# def load_nllb_model():
#     model_name = "facebook/nllb-200-distilled-600M"
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
#     return tokenizer, model

# nllb_tokenizer, nllb_model = load_nllb_model()


# def translate_to_hindi(text, tokenizer, model):
#     inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
#     translated_tokens = model.generate(**inputs, forced_bos_token_id=tokenizer.lang_code_to_id["hin_Deva"])
#     translated_text = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
#     return translated_text

# from google.cloud import translate_v2 as translate

# def translate_with_google(text):
#     translate_client = translate.Client()
#     result = translate_client.translate(text, target_language="hi")
#     return result["translatedText"]

from deep_translator import GoogleTranslator

def translate_with_google(text):
    return GoogleTranslator(source='auto', target='hi').translate(text)

# Function to generate a recipe
def get_recipe(ingredients, age, weight, height, activity_level, dietary_preference, fitness_goal, custom_prompt=""):
    return generate_recipe_with_deepseek(ingredients, age, weight, height, activity_level, dietary_preference, fitness_goal, custom_prompt)

# Set up Streamlit UI
st.set_page_config(page_title="AI Health & Fitness Plan", page_icon="🏋️‍♂️", layout="wide")

st.markdown("""
    <h1 style='text-align: center; color: #FF6347;'>📋 Personalized Recipe Generator</h1>
    <p style='text-align: center; color: #4CAF50;'>Personalized fitness, nutrition, and recipe recommendations!</p>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ Health & Fitness Inputs")

# User inputs for personal information
age = st.sidebar.number_input("Age (in years)", min_value=10, max_value=100, value=25)
weight = st.sidebar.number_input("Weight (in kg)", min_value=30, max_value=200, value=70)
height = st.sidebar.number_input("Height (in cm)", min_value=100, max_value=250, value=170)
activity_level = st.sidebar.selectbox("Activity Level", ["Low", "Moderate", "High"])
dietary_preference = st.sidebar.selectbox("Dietary Preference", ["Keto", "Vegetarian", "Low Carb", "Balanced"])
fitness_goal = st.sidebar.selectbox("Fitness Goal", ["Weight Loss", "Muscle Gain", "Endurance", "Flexibility"])

# Upload ingredients file
uploaded_file = st.sidebar.file_uploader("Upload Ingredients File (TXT)", type=["txt"])
ingredients = ""
if uploaded_file is not None:
    ingredients = uploaded_file.read().decode("utf-8")

# Optional user prompt extension
customize_prompt = st.sidebar.checkbox("Add Custom Preferences", value=False)

custom_prompt = ""
if customize_prompt:
    custom_prompt = st.sidebar.text_area("Enter additional preferences (e.g., avoid garlic, prefer Indian cuisine, 30-min prep):", height=100)

Transaltion = st.sidebar.checkbox("📘 Translate Recipe to Hindi", value=True)



show_dietary_guidance = st.sidebar.checkbox("Include Dietary Guidance", value=True)

import re

def split_think_and_recipe(recipe_text):
    think_match = re.search(r"<think>(.*?)</think>", recipe_text, re.DOTALL)
    if think_match:
        think_part = think_match.group(1).strip()
        recipe_part = recipe_text.replace(think_match.group(0), "").strip()
        return think_part, recipe_part
    else:
        return None, recipe_text  # No <think> tag found


# Button to generate recipe
if st.sidebar.button("Generate Recipe"):
    if not ingredients:
        st.sidebar.warning("Please upload an ingredients file.")
    else:
        with st.spinner("🍽️ Creating your personalized recipe..."):
            recipe = get_recipe(ingredients, age, weight, height, activity_level, dietary_preference, fitness_goal, custom_prompt)


            think_part, recipe_body = split_think_and_recipe(recipe)

            if think_part:
                st.subheader("🧠 Thought Process")
                st.markdown(f"<i>{think_part}</i>", unsafe_allow_html=True)


            st.subheader("👨‍🍳 Your Personalized Recipe")
            st.markdown(recipe_body)
            
            if Transaltion:           
                with st.spinner("Translating to Hindi..."):
                    hindi_recipe = translate_with_google(recipe_body)
                    st.subheader("🍛 Recipe in Hindi")
                    st.markdown(hindi_recipe)
        
            if show_dietary_guidance:
                planner_prompt = (
                    f"The user is {age} years old, weighs {weight}kg, and is {height}cm tall. "
                    f"Their activity level is '{activity_level}', dietary preference is '{dietary_preference}', "
                    f"and their fitness goal is '{fitness_goal}'. "
                    f"The ingredients available are: {ingredients}.\n\n"
                    "Please provide an overview of the ideal dietary composition and guidance based on this information."
                )

                dietary_plan = dietary_planner.run(planner_prompt)
                st.subheader("📝 Personalized Dietary Guidance")
                st.markdown(dietary_plan.content)

            st.success("Enjoy your healthy meal!")
