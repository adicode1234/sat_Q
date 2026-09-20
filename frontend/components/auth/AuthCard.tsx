import type { ReactNode } from "react";
export default function AuthCard({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="auth-card" aria-labelledby="form-title">
      <div className="card-eyebrow">YOUR EARTH INTELLIGENCE WORKSPACE</div>
      <h2 id="form-title">{title}</h2>
      <p className="card-description">{description}</p>
      {children}
    </section>
  );
}
