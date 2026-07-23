import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { errorText } from "../lib/api/errorText.js";
import { useAuth } from "../lib/auth/AuthContext.jsx";
import { useT } from "../lib/i18n.jsx";
import { useToast } from "../lib/toast.jsx";
import Button from "../components/Button.jsx";
import { Field } from "../components/Field.jsx";
import LangSwitcher from "../components/LangSwitcher.jsx";
import ThemeToggle from "../components/ThemeToggle.jsx";

export default function Login() {
  const t = useT();
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/account");
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <div className="flex items-center justify-between p-sm">
        <Link to="/" className="text-headline-md font-bold text-primary">
          {t("brand.name")}
        </Link>
        <div className="flex items-center gap-xs">
          <LangSwitcher />
          <ThemeToggle />
        </div>
      </div>

      <div className="flex flex-1 items-center justify-center px-sm py-lg">
        <div className="w-full max-w-md rounded-2xl border border-outline-variant bg-surface-container-lowest p-lg shadow-sm">
          <h1 className="text-headline-lg-mobile font-bold text-on-surface">
            {t("auth.loginTitle")}
          </h1>
          <p className="mb-lg mt-1 text-body-md text-on-surface-variant">
            {t("auth.loginSubtitle")}
          </p>

          <form onSubmit={onSubmit} className="flex flex-col gap-md">
            <Field
              label={t("auth.email")}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
            <Field
              label={t("auth.password")}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
            <Button type="submit" loading={submitting} className="w-full">
              {t("auth.signIn")}
            </Button>
          </form>

          <p className="mt-md text-center text-body-md text-on-surface-variant">
            {t("auth.noAccount")}{" "}
            <Link to="/register" className="font-semibold text-primary hover:underline">
              {t("auth.toRegister")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
