import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json == {"message": "Hello from Flask on Render!"}

def test_echo(client):
    response = client.post('/echo', json={"test": "data"})
    assert response.status_code == 201
    assert response.json == {"received": {"test": "data"}}
