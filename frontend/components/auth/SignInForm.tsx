

import { useRef, useState, type FormEvent } from "react";
import { login, AuthRequestError } from "@/services/authApi";
import { normalizeEmail, validateLogin } from "@/lib/validation";
import type { FieldErrors } from "@/types/auth";
import AuthInput from "./AuthInput";
import PasswordInput from "./PasswordInput";
export default function SignInForm({ onSuccess, onSwitch }: { onSuccess: () => void; onSwitch: () => void }) {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [success, setSuccess] = useState(false);
  const pending = useRef(false);
  const status = useRef<HTMLDivElement>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    const form = event.currentTarget;
    const validation = validateLogin({ email, password });
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
      await login({ email: normalizeEmail(email), password });
      setSuccess(true);
      setPassword("");
      onSuccess();
    } catch (error) {
      setMessage(
        error instanceof AuthRequestError
          ? error.message
          : "Unable to sign in. Please try again.",
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
        You have signed in successfully. Opening your account...
      </div>
    );
  return (
    <form noValidate onSubmit={submit} aria-busy={busy}>
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
        autoComplete="current-password"
        placeholder="Enter your password"
        required
        maxLength={128}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={errors.password}
      />
      <div className="form-options">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked
            disabled
            name="remember"
            aria-describedby="remember-note"
          />
          Remember me
        </label>
        <span className="unavailable" title="Password reset is not configured">
          Reset unavailable
        </span>
      </div>
      <p className="hint" id="remember-note">
        Your session stays signed in on this browser until you sign out.
      </p>
      <details className="help-details">
        <summary>Forgot password?</summary>
        <p>
          Password reset is not available in this app yet.
        </p>
      </details>
      {message && (
        <div className="form-error" role="alert" tabIndex={-1} ref={status}>
          {message}
        </div>
      )}
      <button className="primary-button" type="submit" disabled={busy}>
        {busy ? (
          "Signing in..."
        ) : (
          <>
            Sign in <span aria-hidden="true">&#8599;</span>
          </>
        )}
      </button>
      <p className="switch-form">
        New to SATQUERY.AI? <button className="auth-text-button" type="button" onClick={onSwitch}>Create an account</button>
      </p>
      <p className="provider-note">
        Authentication secured by Supabase
      </p>
    </form>
  );
}
