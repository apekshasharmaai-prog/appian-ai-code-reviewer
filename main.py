from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

import os
import json

# Load environment variables
load_dotenv()

# OpenAI Client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# FastAPI App
app = FastAPI(
    title="AI Assistant API",
    description="Ask AI and Code Review APIs",
    version="1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Request Models
# -----------------------------

class QueryRequest(BaseModel):
    question: str


class ReviewRequest(BaseModel):
    language: str
    code: str


# -----------------------------
# Ask AI Endpoint
# -----------------------------

@app.post("/ask")
def ask_ai(req: QueryRequest):

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Answer in 3-4 concise lines."
            },
            {
                "role": "user",
                "content": req.question
            }
        ],
        temperature=0.3,
        max_tokens=150
    )

    return {
        "question": req.question,
        "answer": response.choices[0].message.content,
        "tokens_used": response.usage.total_tokens
    }


# -----------------------------
# Code Review Endpoint
# -----------------------------

@app.post("/review")
def review_code(req: ReviewRequest):

    prompt = f"""
    You are a Senior Appian Technical Architect with deep expertise in Appian design patterns, Appian documentation, Appian      Community recommendations, and Appian best practices.
    
    Review the following Appian code.
    
    While performing the review:
    
    - Evaluate the code against Appian official best practices.
    - Consider Appian performance recommendations.
    - Consider Appian Community guidance.
    - Consider maintainability and scalability.
    - Consider User Experience
    - Consider interface responsiveness.
    - Consider naming conventions.
    - Consider Appian Health Check recommendations.
    Identify:
    - Anti-patterns
    - Unnecessary refreshes
    - Excessive nesting
    - Unused variables
    - Potential performance bottlenecks
    Before generating findings, carefully assess whether the implementation follows commonly accepted Appian best practices and standards.
    
    Evaluate the code in the following categories:
    
    1. Performance
    2. Maintainability
    3. Best Practices
    4. Security
    5. Readability
     Scoring Guide:
90-100 = Excellent
80-89 = Good
70-79 = Fair
Below 70 = Needs Improvement
    Return ONLY valid JSON.
    
    {{
      "overall_score": 0,
      "verdict": "",
      "performance_score": 0,
      "maintainability_score": 0,
      "best_practices_score": 0,
      "security_score": 0,
      "readability_score": 0,
    
      "findings": [
        {{
          "severity": "",
          "category": "",
          "title": "",
          "description": "",
          "recommendation": ""
        }}
      ],
    
      "strengths": [],
      "summary": ""
    }}
    

    
    Appian Code:
    
    {req.code}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                You are an expert software architect.
                
                Return ONLY valid JSON.
                Do not wrap JSON inside markdown.
                Do not use ```json blocks.
                """
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=1200
    )

    try:
        review_result = json.loads(
            response.choices[0].message.content
        )

        review_result["tokens_used"] = (
            response.usage.total_tokens
        )

        return review_result

    except Exception as e:

        return {
            "error": "Failed to parse AI response",
            "details": str(e),
            "raw_response": response.choices[0].message.content
        }


# -----------------------------
# Health Check
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "AI Assistant API Running"
    }