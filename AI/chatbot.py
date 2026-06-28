
from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import Markdown, display
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel
import os

pdfReader = PdfReader("Resources/profile.pdf")
prof_summary = ""
for page in pdfReader.pages:
    text = page.extract_text()
    if text:
        prof_summary += text + "\n"
    display(Markdown(text))

print(prof_summary)

with open("Resources/Summary.txt", "r", encoding="utf-8") as file:
    summary = file.read()

summary

load_dotenv(override=True)

openai_api_key = os.getenv("API_TOKEN")
if openai_api_key:
    print(f"OpenAI API Key exists and begins with {openai_api_key[:14]}")
else:
    print(f"OpenAI API Key not set - please check")

name = "Sowande, Ayomide Boluwatife"

system_prompt = (
    f"You are acting as {name}, representing {name} on their website. "
    f"Your role is to answer questions specifically about {name}'s career, background, skills, and experience. "
    f"You must faithfully and accurately portray {name} in all interactions. "
    f"You have access to a detailed summary of {name}'s background and their LinkedIn profile, which you should use to inform your answers. "
    f"Maintain a professional, engaging, and approachable tone, as if you are speaking to a potential client or future employer visiting the site. "
    f"If you are unsure of an answer, it is better to honestly acknowledge that than to guess."

    f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{prof_summary}\n\n"
    f"Using this context, please converse naturally and consistently, always staying in character as {name}."
)

system_prompt

openai_python_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openai_api_key
)
print("OpenAI Client created", openai_python_client)

def livechat(message, history):
    messages=[{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai_python_client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=messages,
        stream=False
    )

    return response.choices[0].message.content

gr.ChatInterface(
    livechat,
    title="Chat with Sowande, Ayomide Boluwatife",
    description="Ask me anything about career, background, skills and experience!",
).launch()