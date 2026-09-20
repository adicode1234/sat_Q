

import { useRef, useState, type FormEvent } from "react";
import { register, AuthRequestError } from "@/services/authApi";
import { normalizeEmail, validateRegister } from "@/lib/validation";
import type { FieldErrors } from "@/types/auth";
import AuthInput from "./AuthInput";
import PasswordInput from "./PasswordInput";
import PasswordStrength from "./PasswordStrength";
export default function SignUpForm({ onSuccess, onSwitch }: { onSuccess: () => void; onSwitch: () => void }) {

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [terms, setTerms] = useState(false);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [success, setSuccess] = useState<"signed-in" | "confirmation" | null>(null);
  const pending = useRef(false);
  const status = useRef<HTMLDivElement>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    const form = event.currentTarget;
    const payload = {
      full_name: fullName.trim().replace(/\s+/g, " "),
      email: normalizeEmail(email),
      password,
    };
    const validation = validateRegister(payload, confirm, terms);
    setErrors(validation);
    setMessage("");
    if (Object.keys(validation).length) {
      (
        form.elements.namedItem(Object.keys(validation)[0]) as HTMLInputElement
      )?.focus();
      return;
    }
    pending.current = true;
    setBusy(true);
    try {
      const result = await register(payload);
      setSuccess(result.signedIn ? "signed-in" : "confirmation");
      if (result.signedIn) {
        onSuccess();
      }
      setPassword("");
      setConfirm("");
    } catch (error) {
      setMessage(
        error instanceof AuthRequestError
          ? error.message
          : "Unable to create your account. Please try again.",
      );
      if (error instanceof AuthRequestError)
        setErrors(error.error.fields ?? {});
      requestAnimationFrame(() => status.current?.focus());
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }
  if (success)
    return (
      <div role="status" className="success-message">
        {success === "signed-in"
          ? "Your account is ready. Opening your account..."
          : "Check your email for a confirmation link. You must verify your email before signing in. If you already have an account, sign in instead."}
        <p><button className="auth-text-button" type="button" onClick={onSwitch}>Back to sign in</button></p>
      </div>
    );
  return (
    <form noValidate onSubmit={submit} aria-busy={busy}>
      <AuthInput
        id="full_name"
        name="full_name"
        label="Full name"
        autoComplete="name"
        placeholder="Your full name"
        required
        maxLength={120}
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
        error={errors.full_name}
      />
      <AuthInput
        id="email"
        name="email"
        label="Email address"
        type="email"
        autoComplete="email"
        placeholder="you@example.com"
        required
        maxLength={254}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={errors.email}
      />
      <PasswordInput
        id="password"
        name="password"
        label="Password"
        autoComplete="new-password"
        placeholder="Create a strong password"
        required
        maxLength={128}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={errors.password}
      />
      <PasswordStrength password={password} />
      <PasswordInput
        id="confirmPassword"
        name="confirmPassword"
        label="Confirm password"
        autoComplete="new-password"
        placeholder="Re-enter your password"
        required
        maxLength={128}
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        error={errors.confirmPassword}
      />
      <label className="checkbox-label terms">
        <input
          id="terms"
          name="terms"
          type="checkbox"
          checked={terms}
          onChange={(e) => setTerms(e.target.checked)}
          aria-invalid={!!errors.terms}
          aria-describedby={errors.terms ? "terms-error" : "prototype-terms"}
        />
        I accept the prototype terms below.
      </label>
      <details className="help-details" id="prototype-terms">
        <summary>Prototype terms</summary>
        <p>
          This interface is for prototype evaluation. Authentication is provided
          by Supabase. Do not submit sensitive or
          operational data. Production terms and a privacy policy must be
          supplied before public use.
        </p>
      </details>
      {errors.terms && (
        <p className="field-error" id="terms-error">
          {errors.terms}
        </p>
      )}
      {message && (
        <div className="form-error" role="alert" tabIndex={-1} ref={status}>
          {message}
        </div>
      )}
      <button className="primary-button" type="submit" disabled={busy}>
        {busy ? (
          "Creating account..."
        ) : (
          <>
            Create account <span aria-hidden="true">&#8599;</span>
          </>
        )}
      </button>
      <p className="switch-form">
        Already have an account? <button className="auth-text-button" type="button" onClick={onSwitch}>Sign in</button>
      </p>
      <p className="provider-note">
        Authentication secured by Supabase
      </p>
    </form>
  );
}
