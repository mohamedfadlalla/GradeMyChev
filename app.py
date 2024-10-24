import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import prompts
from mongo_counter import init_counter

# Set page configuration
st.set_page_config(
   page_title="Chevening Essay Analyzer",
   page_icon="LOGO.jpg",
   layout="centered"
)

# Add logo and title in a container
col1, col2 = st.columns([1, 4])

with col1:
   st.image("LOGO.jpg", width=100)
   
with col2:
   st.title("Chevening Essay Analyzer 📝")
   st.markdown("[Visit Mihnati on Facebook](https://www.facebook.com/Mihnati.sd) 🔗")

# Main description
st.write("""
A free tool from Mihnati to analyze your Chevening scholarship essays and get an instant score out of 4 points,
matching the official Chevening evaluation criteria.
""")

# Warning message
st.warning("""
⚠️ This AI-powered analysis provides suggestions to improve your essay along with a score out of 4. 
Final evaluations by Chevening reviewers may vary.
""")

# Instructions
st.write("""
1. Paste your Chevening essay below
2. Click 'Evaluate Essay'
3. Review your score and detailed feedback
""")


counter = init_counter()
if not hasattr(st.session_state, 'db_connected'):
    if counter.connect():
        st.session_state.db_connected = True

total_evaluations = counter.get_total_evaluations()
if total_evaluations is not None:
    st.markdown(f"### Total Number of Essays Evaluated: <span style='color: red'>{total_evaluations}</span>", unsafe_allow_html=True)

# Set up Groq LLM
llm = ChatGroq(api_key=st.secrets["GROQ_API_KEY"], model_name="llama-3.1-70b-versatile", temperature=0)

# Define output structure for formatting chain
class FormattedEvaluation(BaseModel):
    score: float = Field(description="Numerical score out of 4")
    reasoning: str = Field(description="Detailed reasoning for the score")

# Create the evaluation chain
def create_evaluation_chain(prompt_text):
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_text),
        ("human", "Essay: {essay}\n\nEvaluate the essay and provide an overall score with justification.")
    ])
    return prompt | llm | StrOutputParser()

# Create formatting chain
def create_formatting_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts.extract),
        ("human", "Evaluation: {evaluation}")
    ])
    return prompt | llm | PydanticOutputParser(pydantic_object=FormattedEvaluation)

def count_words(text):
    return len(text.split())

def create_essay_section(essay_type, prompt_text):
    st.write(f"{essay_type} Essay (500 words maximum):")
    essay_text = st.text_area("", key=f"{essay_type}_essay", height=300)
    word_count = count_words(essay_text)
    st.write(f"Word count: {word_count}/500")
    
    if word_count > 500:
        st.warning("Your essay exceeds the 500-word limit. Please shorten it before submitting.")
        
    if st.button(f"Evaluate {essay_type} Essay", key=f"{essay_type}_button", disabled=word_count > 500):
        if essay_text and word_count <= 500:
            with st.spinner(f"Evaluating your {essay_type} essay..."):
                evaluation_chain = create_evaluation_chain(prompt_text)
                formatting_chain = create_formatting_chain()
                
                raw_evaluation = evaluation_chain.invoke({"essay": essay_text})
                formatted_result = formatting_chain.invoke({"evaluation": raw_evaluation})
                
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f0f2f6;
                        border-radius: 10px;
                        padding: 20px;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <h2 style="color: #1f77b4; margin-bottom: 10px;">{essay_type} Essay Score</h2>
                        <p style="font-size: 48px; font-weight: bold; color: #2c3e50; margin: 0;">
                            {formatted_result.score:.2f}
                        </p>
                        <p style="font-size: 18px; color: #7f8c8d;">out of 4.00</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                new_count = counter.increment_and_get_count()
                
                with st.expander(f"See detailed {essay_type} evaluation"):
                    st.write(formatted_result.reasoning)
                    
        else:
            st.warning(f"Please provide a {essay_type} essay within the 500-word limit to evaluate.")

# Streamlit app
st.markdown("### Chevening Essay Evaluator")

# Create tabs for each essay type
tab1, tab2, tab3, tab4 = st.tabs(["Leadership", "Networking", "Study in the UK", "Career Plan"])

with tab1:
    create_essay_section("Leadership", prompts.leadership)


with tab2:
    create_essay_section("Networking", prompts.networking)

with tab3:
    create_essay_section("Study in the UK", prompts.study_in_uk)

with tab4:
    create_essay_section("Career Plan", prompts.career_plan)