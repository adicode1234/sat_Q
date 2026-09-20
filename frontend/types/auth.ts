export interface LoginRequest {
  email: string;
  password: string;
}
export interface RegisterRequest extends LoginRequest {
  full_name: string;
}
export type FieldErrors = Partial<
  Record<
    "full_name" | "email" | "password" | "confirmPassword" | "terms",
    string
  >
>;
export interface AuthApiError {
  code: string;
  message: string;
  fields?: FieldErrors;
}
