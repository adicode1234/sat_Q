import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from gateway import auth


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(auth.router)
    app.middleware('http')(auth.protect_workspace)

    @app.get('/api/private')
    def private():
        return {'ok': True}

    async def provider(method, path, token=None, body=None):
        if path == 'user':
            if token != 'valid-access':
                raise HTTPException(401, 'Invalid token')
            return {'id': 'user-1', 'email': 'tester@example.com', 'user_metadata': {'full_name': 'Test User'}}
        if path == 'token?grant_type=password':
            if body['password'] != 'Correct-Password1!':
                raise HTTPException(401, 'Email or password is incorrect.')
            return {'access_token': 'valid-access', 'refresh_token': 'valid-refresh', 'expires_in': 3600}
        if path == 'token?grant_type=refresh_token':
            if body['refresh_token'] != 'valid-refresh':
                raise HTTPException(401, 'Expired session')
            return {'access_token': 'valid-access', 'refresh_token': 'rotated-refresh', 'expires_in': 3600}
        if path == 'signup':
            return {'id': 'awaiting-confirmation'}
        if path == 'logout?scope=local':
            return {}
        raise AssertionError(path)

    monkeypatch.setattr(auth, 'provider', provider)
    return TestClient(app, base_url='http://localhost')


def sign_in(client):
    return client.post('/api/auth/login', json={'email': 'tester@example.com', 'password': 'Correct-Password1!'})


def test_explore_requires_real_session_and_rejects_fake_cookie(client):
    assert client.get('/api/private').status_code == 401
    client.cookies.set(auth.ACCESS, 'forged-access')
    assert client.get('/api/private').status_code == 401
    assert client.get('/api/auth/session').json() == {'user': None}


def test_login_persists_and_logout_revokes_browser_access(client):
    response = sign_in(client)
    assert response.status_code == 200
    assert response.json()['user']['name'] == 'Test User'
    assert 'access_token' not in response.text
    assert all('HttpOnly' in value and 'SameSite=lax' in value for value in response.headers.get_list('set-cookie'))
    assert client.get('/api/private').status_code == 200
    assert client.get('/api/auth/session').json()['user']['id'] == 'user-1'
    assert client.post('/api/auth/logout').status_code == 200
    assert not client.cookies
    assert client.get('/api/private').status_code == 401


def test_wrong_password_never_creates_session(client):
    response = client.post('/api/auth/login', json={'email': 'tester@example.com', 'password': 'wrong'})
    assert response.status_code == 401
    assert not client.cookies


def test_registration_waits_for_email_confirmation(client):
    response = client.post('/api/auth/register', json={'full_name': 'Test User', 'email': 'tester@example.com', 'password': 'Correct-Password1!'})
    assert response.json() == {'signedIn': False}
    assert not client.cookies


def test_expired_access_refreshes_on_server(client):
    client.cookies.set(auth.ACCESS, 'expired')
    client.cookies.set(auth.REFRESH, 'valid-refresh')
    response = client.get('/api/auth/session')
    assert response.json()['user']['id'] == 'user-1'
    assert 'rotated-refresh' in response.headers['set-cookie']


def test_cross_origin_login_and_logout_rejected(client):
    headers = {'Origin': 'https://other.example'}
    assert client.post('/api/auth/login', headers=headers, json={'email': 'tester@example.com', 'password': 'Correct-Password1!'}).status_code == 403
    assert client.post('/api/auth/logout', headers=headers).status_code == 403
