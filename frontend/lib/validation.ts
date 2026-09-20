import type { FieldErrors, LoginRequest, RegisterRequest } from "@/types/auth";
export const normalizeEmail = (email: string) => email.trim().toLowerCase();
export const isValidEmail = (email: string) =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
export function passwordChecks(password: string): boolean[] {
  return [
    password.length >= 8,
    /[A-Z]/.test(password),
    /[a-z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9\s]/.test(password),
  ];
}
export const isValidPassword = (password: string) =>
  password.length <= 128 && passwordChecks(password).every(Boolean);
export const passwordsMatch = (password: string, confirm: string) =>
  !!password && password === confirm;
export function validateLogin(values: LoginRequest): FieldErrors {
  const errors: FieldErrors = {};
  if (!isValidEmail(values.email))
    errors.email = "Enter a valid email address.";
  if (!values.password) errors.password = "Enter your password.";
  else if (values.password.length > 128)
    errors.password = "Use no more than 128 characters.";
  return errors;
}
export function validateRegister(
  values: RegisterRequest,
  confirm: string,
  terms: boolean,
): FieldErrors {
  const errors = validateLogin(values);
  const name = values.full_name.trim().replace(/\s+/g, " ");
  if (name.length < 2 || name.length > 120)
    errors.full_name = "Enter your full name (2-120 characters).";
  if (!isValidPassword(values.password))
    errors.password =
      "Use 8-128 characters with uppercase, lowercase, a number and a special character.";
  if (!passwordsMatch(values.password, confirm))
    errors.confirmPassword = "Passwords must match.";
  if (!terms) errors.terms = "Accept the prototype terms to continue.";
  return errors;
}
