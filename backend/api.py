# main.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from anthropic import Anthropic
import os
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
# ... (other imports remain the same)

app = FastAPI(title="Tunisian Baccalaureate AI Tutor API")

# CORS middleware with permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# ... (other parts of your FastAPI code remain the same)

@app.post("/token")
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Explicitly set CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    
    return JSONResponse(content={"access_token": access_token, "token_type": "bearer"})

@app.options("/token")
async def options_token(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    return Response(status_code=200)
# Load Tunisian Baccalaureate program data
with open('bac_program.json', 'r', encoding='utf-8') as f:
    BAC_PROGRAM = json.load(f)

# Security
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Anthropic client
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Models
# Updated User models
class User(BaseModel):
    username: str
    hashed_password: str

class UserInDB(User):
    id: Optional[int] = None

# User database (replace with actual database in production)
users_db = {}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class Question(BaseModel):
    subject: str
    question: str

class PracticeRequest(BaseModel):
    subject: str
    topic: str
    difficulty: str

class AnswerEvaluation(BaseModel):
    subject: str
    question: str
    student_answer: str


# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    if username in users_db:
        user_dict = users_db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Routes
@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(username: str, password: str):
    if username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    hashed_password = get_password_hash(password)
    user_id = len(users_db) + 1
    users_db[username] = {"id": user_id, "username": username, "hashed_password": hashed_password}
    return {"message": "User created successfully"}

async def answer_question(question: Question, current_user: User = Depends(get_current_user)):
    try:
        context = BAC_PROGRAM.get(question.subject, "")
        prompt = f"""Agissez comme un expert et professeur avancé en {question.subject} pour le baccalauréat tunisien. 
        Contexte du programme : {context}

        Donnez toujours une réponse détaillée, bien organisée en markdown (avec LaTeX pour les formules mathématiques).
        Assurez-vous d'inclure :
        1. Une explication claire et concise du concept
        2. Des exemples pertinents
        3. Des formules importantes (en LaTeX si nécessaire)
        4. Des astuces pour mieux comprendre ou mémoriser
        5. Des liens avec d'autres concepts du programme si pertinent

        Question de l'élève : {question.question}

        Réponse :
        """
        
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0.7,
            system="Act like an expert and advanced teacher for the Tunisian baccalaureate.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return {"response": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class Question(BaseModel):
    subject: str
    question: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ... (other parts of your FastAPI code remain the same)

@app.post("/question")
async def answer_question(question: Question, current_user: User = Depends(get_current_user)):
    try:
        context = BAC_PROGRAM.get(question.subject, "")
        prompt = f"""Agissez comme un expert et professeur avancé en {question.subject} pour le baccalauréat tunisien. 
        Contexte du programme : {context}

        Donnez toujours une réponse détaillée, bien organisée en markdown (avec LaTeX pour les formules mathématiques).
        Assurez-vous d'inclure :
        1. Une explication claire et concise du concept
        2. Des exemples pertinents
        3. Des formules importantes (en LaTeX si nécessaire)
        4. Des astuces pour mieux comprendre ou mémoriser
        5. Des liens avec d'autres concepts du programme si pertinent

        Question de l'élève : {question.question}

        Réponse :
        """
        
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0.7,
            system="Act like an expert and advanced teacher for the Tunisian baccalaureate.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return {"response": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PracticeRequest(BaseModel):
    subject: str
    topic: str
    difficulty: str

@app.post("/practice")
async def generate_practice_questions(request: PracticeRequest, current_user: User = Depends(get_current_user)):
    try:
        prompt = f"""Générez 3 questions de pratique en {request.subject} sur le thème '{request.topic}' avec un niveau de difficulté {request.difficulty} pour le baccalauréat tunisien. Formatez chaque question comme suit:
        ALWAYS inMarkdon + latex formaulas if any
        Question 1:
        [Texte de la question]

        Réponse 1:
        [Texte de la réponse]

        Question 2:
        [Texte de la question]

        Réponse 2:
        [Texte de la réponse]

        Question 3:
        [Texte de la question]

        Réponse 3:
        [Texte de la réponse]
        """
        
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1500,
            temperature=0.8,
            system="Generate practice questions for the Tunisian baccalaureate.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return {"questions": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/evaluate")
async def evaluate_answer(evaluation: AnswerEvaluation, current_user: User = Depends(get_current_user)):
    try:
        prompt = f"""Évaluez la réponse de l'élève à la question suivante en {evaluation.subject} pour le baccalauréat tunisien. Donnez un feedback détaillé et des suggestions d'amélioration. Utilisez le format suivant:

        Évaluation:
        [Votre évaluation générale]

        Points forts:
        - [Point fort 1]
        - [Point fort 2]
        - ...

        Points à améliorer:
        - [Point à améliorer 1]
        - [Point à améliorer 2]
        - ...

        Suggestions d'amélioration:
        [Vos suggestions détaillées]

        Note estimée: [Donnez une note sur 20]

        Question : {evaluation.question}

        Réponse de l'élève : {evaluation.student_answer}
        """
        
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0.5,
            system="Evaluate student answers for the Tunisian baccalaureate.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return {"evaluation": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study_tips/{subject}")
async def get_study_tips(subject: str, current_user: User = Depends(get_current_user)):
    try:
        prompt = f"Donnez 5 conseils d'étude efficaces pour réussir en {subject} au baccalauréat tunisien. Formatez votre réponse comme une liste numérotée."
        
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0.7,
            system="Provide study tips for the Tunisian baccalaureate.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return {"study_tips": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/syllabus/{subject}")
async def get_syllabus(subject: str, current_user: User = Depends(get_current_user)):
    syllabus = BAC_PROGRAM.get(subject, {}).get('syllabus', "Syllabus non disponible pour cette matière.")
    return {"syllabus": syllabus}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)