import requests

def test_google():
    response = requests.get("https://www.google.com")
    assert response.status_code == 200