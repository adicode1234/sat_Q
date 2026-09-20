import type { AuthApiError, LoginRequest, RegisterRequest } from '@/types/auth';
export type AuthUser = { id: string; email: string; name: string };
export class AuthRequestError extends Error {
  constructor(public readonly error: AuthApiError) { super(error.message); }
}
async function request(path: string, body?: unknown) {
  const response = await fetch(`/api/auth/${path}`, {
    method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new AuthRequestError({ code: String(response.status),
    message: typeof data.detail === 'string' ? data.detail : 'Unable to authenticate. Please try again.' });
  return data;
}
export const login = (payload: LoginRequest) => request('login', payload);
export const register = (payload: RegisterRequest) => request('register', payload);
export const logout = () => request('logout', {});
export const getSession = (): Promise<{ user: AuthUser | null }> => request('session');
