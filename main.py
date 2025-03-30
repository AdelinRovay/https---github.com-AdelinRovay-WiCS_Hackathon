import io
import os
import openai
from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from PyPDF2 import PdfReader
import json

from pydantic import BaseModel

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class InputData(BaseModel):
    input: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def extract_text_from_pdf(pdf_file: UploadFile):
    try:
        file_bytes = await pdf_file.read()
        pdf_io = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_io)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text.strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def generate_flashcards(text):
    try:
        openai.api_key = OPENAI_API_KEY
        prompt = f"""Extract key points and generate at least 10 flashcards in Q&A format from the following text. Make sure to return it in the below JSON format:
[
  {{ "question": "What is Photosynthesis?", "answer": "The process where plants convert sunlight into energy." }},
  {{ "question": "Define Newton's second law.", "answer": "Force equals mass times acceleration." }}
]:\n{text}"""
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error generating flashcards: {str(e)}"

def format_flashcards(response_text):
    try:
        flashcards_list = json.loads(response_text)
        if not isinstance(flashcards_list, list):
            raise ValueError("The provided JSON is not a list.")
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON input provided.") from e
    output = {"flashcards": flashcards_list}
    return json.dumps(output, indent=2)

@app.post("/pdfFlashCards/")
async def upload_pdf(file: UploadFile = File(...)):
    text = await extract_text_from_pdf(file)
    if "Error" in text:
        return {"error": text}
    flashcards = format_flashcards(generate_flashcards(text))
    return flashcards

@app.post("/textFlashCards/")
async def text(input_data: InputData):
    input_text = input_data.input
    flashcards = format_flashcards(generate_flashcards(input_text))

    return flashcards
@app.get("/")
async def root():
    return {"message": "Welcome to the Flashcards API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
