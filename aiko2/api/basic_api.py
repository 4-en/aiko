from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
import sqlite3
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import List

# FastAPI instance
app = FastAPI()

# Database setup
DATABASE = "chat.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configurations
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    sender_id: int
    content: str
    timestamp: str

# Utility functions
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Routes
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(user.password)
    cur.execute("INSERT INTO users (username, hashed_password) VALUES (?, ?)", (user.username, hashed_password))
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    return {"id": user_id, "username": user.username}

@app.post("/login", response_model=Token)
def login(user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    db_user = cur.fetchone()
    conn.close()
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": db_user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            timestamp = datetime.utcnow().isoformat()
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO messages (content, timestamp) VALUES (?, ?)", (data, timestamp))
            conn.commit()
            conn.close()
            await manager.broadcast(f"{timestamp}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/chat_history", response_model=List[MessageResponse])
def get_chat_history():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT sender_id, content, timestamp FROM messages")
    messages = cur.fetchall()
    conn.close()
    return [{"sender_id": msg["sender_id"], "content": msg["content"], "timestamp": msg["timestamp"]} for msg in messages]
