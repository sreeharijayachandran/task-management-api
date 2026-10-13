from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.main import get_db

TEST_DATABASE_URL = (
    "postgresql+psycopg2://postgres:87654321@localhost:5432/task_management_test"
)

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Task Management API is running"
    }

def test_register_user():
    response = client.post(
        "/register",
        json={
            "username": "testuser8",
            "email": "testuser8@example.com",
            "password": "password123"
        }
    )
    print("REGISTER RESPONSE:", response.json())

    assert response.status_code == 200

def test_login_user():
    response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_tasks_authenticated():
    # Login
    login_response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Call protected endpoint
    response = client.get(
        "/tasks",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_tasks_unauthenticated():
    response = client.get("/tasks")

    assert response.status_code == 401

def test_create_task():
    # Step 1: Log in
    login_response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    # Step 2: Extract the JWT token
    token = login_response.json()["access_token"]

    # Step 3: Create a task
    response = client.post(
        "/tasks",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Test Task",
            "description": "Testing task creation",
            "completed": False
        }
    )

    # Step 4: Verify the response
    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Test Task"
    assert data["description"] == "Testing task creation"
    assert data["completed"] is False

def test_get_all_tasks():
    # 1. Log in
    login_response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # 2. Retrieve all tasks
    response = client.get(
        "/tasks",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    # 3. Verify the response
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_single_task():
    # 1. Log in
    login_response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # 2. Create a task
    create_response = client.post(
        "/tasks",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Single Task Test",
            "description": "Testing retrieval of one task",
            "completed": False
        }
    )

    assert create_response.status_code == 200

    task_id = create_response.json()["id"]

    # 3. Retrieve that task using its ID
    response = client.get(
        f"/tasks/{task_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    # 4. Verify the response
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task_id
    assert data["title"] == "Single Task Test"
    assert data["description"] == "Testing retrieval of one task"

def test_update_task():
    # 1. Log in
    login_response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 2. Create a task
    create_response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Original Task",
            "description": "Original description",
            "completed": False
        }
    )

    assert create_response.status_code == 200
    task_id = create_response.json()["id"]

    # 3. Update the task
    update_response = client.put(
        f"/tasks/{task_id}",
        headers=headers,
        json={
            "title": "Updated Task",
            "description": "Updated description",
            "completed": True
        }
    )

    # 4. Verify the update
    assert update_response.status_code == 200

    data = update_response.json()

    assert data["id"] == task_id
    assert data["title"] == "Updated Task"
    assert data["description"] == "Updated description"
    assert data["completed"] is True

def test_delete_task():
    # 1. Log in
    login_response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 2. Create a task
    create_response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Task to Delete",
            "description": "This task will be deleted",
            "completed": False
        }
    )

    assert create_response.status_code == 200

    task_id = create_response.json()["id"]

    # 3. Delete the task
    delete_response = client.delete(
        f"/tasks/{task_id}",
        headers=headers
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "message": "Task deleted successfully"
    }

    # 4. Verify that the task no longer exists
    get_response = client.get(
        f"/tasks/{task_id}",
        headers=headers
    )

    assert get_response.status_code == 404

def test_duplicate_registration():
    user_data = {
        "username": "duplicate_test1_user",
        "email": "duplicate_test1@example.com",
        "password": "password123"
    }

    # First registration
    first_response = client.post(
        "/register",
        json=user_data
    )

    assert first_response.status_code == 200

    # Attempt to register the same user again
    second_response = client.post(
        "/register",
        json=user_data
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Username already exists"

def test_invalid_login():
    response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_user_cannot_access_another_users_task():
    # Log in as the first user
    login_response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a task belonging to the first user
    task_response = client.post(
        "/tasks",
        json={
            "title": "Private Task",
            "description": "This task belongs to the first user",
            "completed": False
        },
        headers=headers
    )

    task_id = task_response.json()["id"]

    # Try accessing the task using a different user ID
    response = client.get(
        f"/tasks/{task_id + 99999}",
        headers=headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

def test_user_cannot_access_another_users_task_with_two_users():
    # Register a second user
    client.post(
        "/register",
        json={
            "username": "seconduser",
            "email": "seconduser@example.com",
            "password": "password123"
        }
    )

    # First user logs in
    first_login = client.post(
        "/login",
        data={
            "username": "testuser5",
            "password": "password123"
        }
    )

    first_token = first_login.json()["access_token"]
    first_headers = {"Authorization": f"Bearer {first_token}"}

    # First user creates a task
    task_response = client.post(
        "/tasks",
        json={
            "title": "Private Task",
            "description": "Belongs to the first user",
            "completed": False
        },
        headers=first_headers
    )

    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    # Second user logs in
    second_login = client.post(
        "/login",
        data={
            "username": "seconduser",
            "password": "password123"
        }
    )

    second_token = second_login.json()["access_token"]
    second_headers = {"Authorization": f"Bearer {second_token}"}

    # Second user attempts to access the first user's task
    response = client.get(
        f"/tasks/{task_id}",
        headers=second_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

def test_user_cannot_update_another_users_task():
    # Log in as the first user
    first_login = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    first_headers = {
        "Authorization": f"Bearer {first_login.json()['access_token']}"
    }

    # First user creates a task
    task_response = client.post(
        "/tasks",
        json={
            "title": "Original Task",
            "description": "Original description",
            "completed": False
        },
        headers=first_headers
    )

    task_id = task_response.json()["id"]

    # Log in as the second user
    second_login = client.post(
        "/login",
        data={
            "username": "seconduser",
            "password": "password123"
        }
    )

    second_headers = {
        "Authorization": f"Bearer {second_login.json()['access_token']}"
    }

    # Second user attempts to update the first user's task
    response = client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Hacked Task",
            "description": "Modified by another user",
            "completed": True
        },
        headers=second_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

    # Verify the original task was not changed
    original_task = client.get(
        f"/tasks/{task_id}",
        headers=first_headers
    )

    assert original_task.status_code == 200
    assert original_task.json()["title"] == "Original Task"
    assert original_task.json()["completed"] is False

def test_user_cannot_delete_another_users_task():
    # Log in as the first user
    first_login = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    first_headers = {
        "Authorization": f"Bearer {first_login.json()['access_token']}"
    }

    # First user creates a task
    task_response = client.post(
        "/tasks",
        json={
            "title": "Important Task",
            "description": "This task must not be deleted by another user",
            "completed": False
        },
        headers=first_headers
    )

    assert task_response.status_code == 200
    task_id = task_response.json()["id"]

    # Log in as the second user
    second_login = client.post(
        "/login",
        data={
            "username": "seconduser",
            "password": "password123"
        }
    )

    second_headers = {
        "Authorization": f"Bearer {second_login.json()['access_token']}"
    }

    # Second user attempts to delete the first user's task
    delete_response = client.delete(
        f"/tasks/{task_id}",
        headers=second_headers
    )

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Task not found"

    # Verify the first user's task still exists
    verify_response = client.get(
        f"/tasks/{task_id}",
        headers=first_headers
    )

    assert verify_response.status_code == 200
    assert verify_response.json()["title"] == "Important Task"

def test_create_task_with_empty_title():
    # Log in
    login_response = client.post(
        "/login",
        data={
            "username": "testuser8",
            "password": "password123"
        }
    )

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Try creating a task with an empty title
    response = client.post(
        "/tasks",
        json={
            "title": "",
            "description": "A valid description",
            "completed": False
        },
        headers=headers
    )

    assert response.status_code == 422