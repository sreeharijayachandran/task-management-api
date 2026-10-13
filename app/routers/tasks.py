from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task
from app.schemas import TaskCreate
from app.auth import get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


@router.post("/")
def create_task(
    task: TaskCreate,
    db=Depends(get_db),
    current_user_id=Depends(get_current_user)
):
    new_task = Task(
        title=task.title,
        description=task.description,
        completed=task.completed,
        user_id=current_user_id
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


@router.get("/")
def get_tasks(
    db=Depends(get_db),
    current_user_id=Depends(get_current_user)
):
    return db.query(Task).filter(
        Task.user_id == current_user_id
    ).all()

@router.get("/{task_id}")
def get_task(
    task_id: int,
    db=Depends(get_db),
    current_user_id=Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


@router.put("/{task_id}")
def update_task(
    task_id: int,
    task: TaskCreate,
    db=Depends(get_db),
    current_user_id=Depends(get_current_user)
):
    existing_task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user_id
    ).first()

    if existing_task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    existing_task.title = task.title
    existing_task.description = task.description
    existing_task.completed = task.completed

    db.commit()
    db.refresh(existing_task)

    return existing_task


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db=Depends(get_db),
    current_user_id=Depends(get_current_user)
):
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user_id
    ).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {
        "message": "Task deleted successfully"
    }