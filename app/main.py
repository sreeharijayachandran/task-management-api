from fastapi import FastAPI, HTTPException, Depends

from app.database import engine, Base, SessionLocal
from app.models import Task, User
from app.schemas import TaskCreate, UserCreate, UserLogin
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from app.database import engine, Base, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Task Management API",
    description="A REST API for managing tasks",
    version="1.0.0"
)
from app.routers.tasks import router as tasks_router

app.include_router(tasks_router)

@app.get("/")
def root():
    return {
        "message": "Task Management API is running"
    }


@app.post("/register")
def register_user(user: UserCreate, db=Depends(get_db)):
    existing_user = db.query(User).filter(
        User.username == user.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    hashed_password = hash_password(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    }

@app.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if existing_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        form_data.password,
        existing_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        data={"sub": str(existing_user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }