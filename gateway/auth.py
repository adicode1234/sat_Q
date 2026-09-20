"""Supabase authentication via same-origin, HttpOnly session cookies."""
import os
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix='/api/auth')
ACCESS = 'satquery_access'
REFRESH = 'satquery_refresh'


def configured():
    return bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_PUBLISHABLE_KEY'))


def check_origin(request):
    origin = request.headers.get('origin')
    if origin and urlsplit(origin).netloc != request.headers.get('host'):
        raise HTTPException(403, 'Cross-origin authentication requests are not allowed.')
    if request.headers.get('sec-fetch-site') == 'cross-site':
        raise HTTPException(403, 'Cross-site requests are not allowed.')


async def provider(method, path, *, token=None, body=None):
    if not configured():
        raise HTTPException(503, 'Authentication is not configured.')
    headers = {'apikey': os.environ['SUPABASE_PUBLISHABLE_KEY']}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(method, os.environ['SUPABASE_URL'].rstrip('/') + '/auth/v1/' + path,
                                            headers=headers, json=body)
    except httpx.HTTPError:
        raise HTTPException(503, 'Authentication service is unavailable. Please try again.') from None
    if response.is_error:
        code = response.json().get('error_code', '') if 'json' in response.headers.get('content-type', '') else ''
        message = {
            'email_not_confirmed': 'Please verify your email before signing in.',
            'weak_password': 'Choose a stronger password.',
            'signup_disabled': 'Account registration is currently unavailable.',
        }.get(code, 'Email or password is incorrect.' if path.startswith('token?grant_type=password') else 'Authentication request failed. Please try again.')
        raise HTTPException(429 if response.status_code == 429 else 401, message)
    return response.json() if response.content else {}


def public_user(user):
    return {'id': user['id'], 'email': user.get('email', ''),
            'name': user.get('user_metadata', {}).get('full_name') or user.get('email', '').split('@')[0]}


def set_session(response, data, request):
    for name, value, age in [(ACCESS, data['access_token'], int(data.get('expires_in', 3600))),
                             (REFRESH, data['refresh_token'], 30 * 86400)]:
        response.set_cookie(name, value, max_age=age, httponly=True,
                            secure=request.url.scheme == 'https', samesite='lax', path='/')


async def authenticate(request):
    token = request.cookies.get(ACCESS)
    if token:
        try:
            return await provider('GET', 'user', token=token), None
        except HTTPException as exc:
            if exc.status_code != 401:
                raise
    refresh = request.cookies.get(REFRESH)
    if not refresh:
        raise HTTPException(401, 'Please sign in to continue.')
    data = await provider('POST', 'token?grant_type=refresh_token', body={'refresh_token': refresh})
    user = await provider('GET', 'user', token=data['access_token'])
    return user, data


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class Registration(Credentials):
    full_name: str = Field(min_length=2, max_length=120)


@router.post('/login')
async def login(payload: Credentials, request: Request):
    check_origin(request)
    data = await provider('POST', 'token?grant_type=password',
                          body={'email': payload.email.strip().lower(), 'password': payload.password})
    user = await provider('GET', 'user', token=data['access_token'])
    response = JSONResponse({'user': public_user(user)}, headers={'Cache-Control': 'no-store'})
    set_session(response, data, request)
    return response


@router.post('/register')
async def register(payload: Registration, request: Request):
    check_origin(request)
    if len(payload.password) < 8:
        raise HTTPException(422, 'Use a password with at least 8 characters.')
    data = await provider('POST', 'signup', body={'email': payload.email.strip().lower(),
        'password': payload.password, 'data': {'full_name': payload.full_name.strip()}})
    signed_in = bool(data.get('access_token') and data.get('refresh_token'))
    response = JSONResponse({'signedIn': signed_in}, headers={'Cache-Control': 'no-store'})
    if signed_in:
        await provider('GET', 'user', token=data['access_token'])
        set_session(response, data, request)
    return response


@router.get('/session')
async def session(request: Request):
    try:
        user, refreshed = await authenticate(request)
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
        return JSONResponse({'user': None}, headers={'Cache-Control': 'no-store'})
    response = JSONResponse({'user': public_user(user)}, headers={'Cache-Control': 'no-store'})
    if refreshed:
        set_session(response, refreshed, request)
    return response


@router.post('/logout')
async def logout(request: Request):
    check_origin(request)
    if request.cookies.get(ACCESS) or request.cookies.get(REFRESH):
        try:
            _, refreshed = await authenticate(request)
            token = refreshed['access_token'] if refreshed else request.cookies[ACCESS]
            await provider('POST', 'logout?scope=local', token=token)
        except HTTPException as exc:
            if exc.status_code not in (401, 403):
                raise
    response = JSONResponse({'ok': True}, headers={'Cache-Control': 'no-store'})
    response.delete_cookie(ACCESS, path='/')
    response.delete_cookie(REFRESH, path='/')
    return response


async def protect_workspace(request, call_next):
    path = request.url.path
    protected = (path.startswith(('/api/', '/reports/')) or path in ('/vision-setup', '/review-queue'))
    if protected and not path.startswith('/api/auth/') and path not in ('/api/health', '/api/config', '/api/translate'):
        try:
            if request.method not in ('GET', 'HEAD', 'OPTIONS'):
                check_origin(request)
            user, refreshed = await authenticate(request)
            request.state.user = user
        except HTTPException as exc:
            return JSONResponse({'detail': exc.detail}, status_code=exc.status_code, headers={'Cache-Control': 'no-store'})
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        if refreshed:
            set_session(response, refreshed, request)
        return response
    return await call_next(request)
