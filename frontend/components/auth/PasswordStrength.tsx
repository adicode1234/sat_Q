import { passwordChecks } from "@/lib/validation";
export default function PasswordStrength({ password }: { password: string }) {
  const checks = passwordChecks(password).filter(Boolean).length;
  const level = !password
    ? 0
    : checks < 3
      ? 1
      : checks < 5
        ? 2
        : password.length < 12
          ? 3
          : 4;
  const label = ["", "Weak", "Fair", "Good", "Strong"][level];
  return (
    <div className="strength">
      <div className="strength-bars" aria-hidden="true">
        {[1, 2, 3, 4].map((n) => (
          <span key={n} data-active={n <= level} />
        ))}
      </div>
      <p aria-live="polite">
        {password
          ? `Password strength: ${label}`
          : "Use 8+ characters, uppercase, lowercase, number & symbol."}
      </p>
    </div>
  );
}
