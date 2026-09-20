import { useState } from "react";
import AuthInput from "./AuthInput";
import type { ComponentProps } from "react";
export default function PasswordInput(props: ComponentProps<typeof AuthInput>) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="password-field">
      <AuthInput {...props} type={visible ? "text" : "password"} />
      <button
        className="visibility"
        type="button"
        aria-label={`${visible ? "Hide" : "Show"} ${props.label.toLowerCase()}`}
        aria-pressed={visible}
        onClick={() => setVisible(!visible)}
      >
        {visible ? "Hide" : "Show"}
      </button>
    </div>
  );
}
