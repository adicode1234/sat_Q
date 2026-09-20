import { useState } from 'react';
import AuthLayout from './AuthLayout';
import AuthCard from './AuthCard';
import SignInForm from './SignInForm';
import SignUpForm from './SignUpForm';
import './auth.css';

export default function AuthPage({ onSuccess, onBack, checking = false, error = '', initialMode = 'signin' }: {
  onSuccess: () => void; onBack: () => void; checking?: boolean; error?: string; initialMode?: 'signin' | 'signup';
}) {
  const [signup, setSignup] = useState(initialMode === 'signup');
  return <div className="satquery-auth"><AuthLayout>
    <AuthCard title={checking ? 'Checking your session' : signup ? 'Create your account' : 'Welcome back'}
      description={signup ? 'Create an account to start exploring your Earth intelligence workspace.' : 'Sign in to continue to your Earth intelligence workspace.'}>
      {error && <p className="form-error" role="alert">{error}</p>}
      {checking ? <p role="status">Please wait…</p> : signup
        ? <SignUpForm onSuccess={onSuccess} onSwitch={() => setSignup(false)} />
        : <SignInForm onSuccess={onSuccess} onSwitch={() => setSignup(true)} />}
      <p className="switch-form"><button className="auth-text-button" type="button" onClick={onBack}>← Back to home</button></p>
    </AuthCard>
  </AuthLayout></div>;
}
