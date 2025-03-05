from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow only the Next.js frontend
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  # Allow all headers
)

@app.get("/api/data")
async def get_data():
    return {"message": "Hello from FastAPI!"}
