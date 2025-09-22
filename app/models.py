from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Exam(BaseModel):
    id: str
    title: str
    date: str           
    topics: List[str] = []  

class Fragment(BaseModel):
    doc_id: str
    text: str
    page: int = 0

class MCQ(BaseModel):
    question: str
    options: List[str]
    answer: str

class PlanBlock(BaseModel):
    id: str
    title: str
    minutes: int
    fragments: List[Fragment] = []
    covered: bool = False
    asked_mcqs: List[MCQ]=[]

class Session(BaseModel):
    id: str
    name: str
    created_at: str = datetime.now().strftime("%Y-%m-%d %H:%M")
    blocks: List[PlanBlock]
    syllabus_topics: List[str] = []
    pins: List[Fragment] = []
