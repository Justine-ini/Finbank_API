from fastapi import FastAPI

app = FastAPI(
    title="Finbank - API",
    description="Fully featured banking API built with FastAPI"
)


@app.get("/")
def home():
    return {"message": "Welcome to Finbank API"}
