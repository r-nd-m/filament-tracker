import pytest
from app import app, db
from app.models import FilamentRoll, PrintJob

def test_add_roll(client):
    """Test adding a new filament roll."""
    response = client.post("/add_roll", data={
        "maker": "Anycubic",
        "color": "Red",
        "total_weight": 1200,
        "remaining_weight": 1200
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Anycubic" in response.data  # Ensure the new roll is in the response

def test_edit_roll(client, init_database):
    """Test editing an existing filament roll."""
    response = client.post("/edit_roll/1", data={
        "maker": "Updated Maker",
        "color": "Updated Color",
        "total_weight": 900,
        "remaining_weight": 450,
        "in_use": "on"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Updated Maker" in response.data

def test_duplicate_roll(client, init_database):
    """Test duplicating a filament roll."""
    response = client.post("/duplicate_roll/1", data={
        "maker": "Duplicated Maker",
        "color": "Duplicated Color",
        "total_weight": 800,
        "remaining_weight": 800,
        "in_use": "on"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Duplicated Maker" in response.data

def test_delete_roll(client, init_database):
    """Test deleting a filament roll."""
    response = client.post("/delete_roll/1", follow_redirects=True)
    assert response.status_code == 200
    assert b"Prusa" not in response.data  # Ensure it is removed

def test_add_print_job(client, init_database):
    """Test adding a new print job."""
    response = client.post("/add_print", data={
        "filament_id": 1,
        "weight_used": 50.5,
        "project_name": "Test Print",
        "date": "2025-02-08T14:30"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Print" in response.data

def test_edit_print(client, init_database):
    """Test editing an existing print job."""
    client.post("/add_print", data={
        "filament_id": 1,
        "weight_used": 50,
        "project_name": "Original Print",
        "date": "2025-02-08T14:30"
    }, follow_redirects=True)

    response = client.post("/edit_print/1", data={
        "filament_id": 1,
        "weight_used": 60,
        "project_name": "Updated Print",
        "date": "2025-02-08T15:00"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Updated Print" in response.data

def test_duplicate_print(client, init_database):
    """Test duplicating a print job."""
    client.post("/add_print", data={
        "filament_id": 1,
        "weight_used": 30,
        "project_name": "Test Print",
        "date": "2025-02-08T14:30"
    }, follow_redirects=True)

    response = client.post("/duplicate_print/1", data={
        "filament_id": 1,
        "weight_used": 30,
        "project_name": "Duplicated Print",
        "date": "2025-02-08T14:45"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Duplicated Print" in response.data

def test_filament_weight_updates(client, init_database):
    """Ensure filament weight is reduced correctly after adding a print job."""
    client.post("/add_print", data={
        "filament_id": 1,
        "weight_used": 50.5,
        "project_name": "Weight Test",
        "date": "2025-02-08T14:30"
    }, follow_redirects=True)

    with app.app_context():
        filament = db.session.get(FilamentRoll, 1)
        assert filament.remaining_weight == 449.5

def test_delete_print_job(client, init_database):
    """Test deleting a print job."""
    client.post("/add_print", data={
        "filament_id": 1,
        "weight_used": 50,
        "project_name": "Test Print",
        "date": "2025-02-08T14:30"
    }, follow_redirects=True)
    response = client.post("/delete_print/1", follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Print" not in response.data

def test_add_temp_job(client):
    """Test adding a temporary print job via the API."""
    response = client.post("/add_temp_job", json={
        "project_name": "Auto Test",
        "weight_used": 42.0,
        "date": "2025-02-08T14:30"
    })
    assert response.status_code == 200
    assert b"Temporary job added successfully" in response.data

def test_approve_temp_job(client, init_database):
    """Test approving a temporary print job."""
    client.post("/add_temp_job", json={
        "project_name": "Temp Job",
        "weight_used": 42.0,
        "date": "2025-02-08T14:30"
    })

    response = client.post("/approve_temp_job/1", data={
        "project_name": "Approved Job",
        "weight_used": 42.0,
        "date": "2025-02-08T14:30",
        "filament_id": 1
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Approved Job" in response.data

def test_delete_temp_job(client, init_database):
    """Test deleting a temporary print job."""
    client.post("/add_temp_job", json={
        "project_name": "Temp Job",
        "weight_used": 42.0,
        "date": "2025-02-08T14:30"
    })

    response = client.post("/delete_temp_job/1", follow_redirects=True)
    assert response.status_code == 200
