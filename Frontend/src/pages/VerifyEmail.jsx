import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import * as authApi from "../lib/api/auth.js";
import { errorText } from "../lib/api/errorText.js";
import { useT } from "../lib/i18n.jsx";
import { useToast } from "../lib/toast.jsx";
import Button from "../components/Button.jsx";
import { Field } from "../components/Field.jsx";
import LangSwitcher from "../components/LangSwitcher.jsx";
import ThemeToggle from "../components/ThemeToggle.jsx";

export default function VerifyEmail() {
  const t = useT();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState(location.state?.email || "");
  const [code, setCode] = useState("");
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    const next = {};
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) next.email = t("errors.VALIDATION_ERROR");
    if (!/^\d{6}$/.test(code)) next.code = t("errors.INVALID_CODE");
    setErrors(next);
    if (Object.keys(next).length) return;

    setSubmitting(true);
    try {
      await authApi.verifyEmail(email, code);
      toast.success(t("auth.verify"));
      navigate("/login");
    } catch (err) {
      const message = errorText(t, err);
      setErrors({ form: message });
      toast.error(message);
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
            {t("auth.verifyTitle")}
          </h1>
          <p className="mb-lg mt-1 text-body-md text-on-surface-variant">
            {t("auth.verifySubtitle", { email: email || "…" })}
          </p>

          {errors.form && (
            <div className="mb-md rounded-xl border border-error/40 bg-error-container px-4 py-3 text-body-md text-on-error-container">
              {errors.form}
            </div>
          )}

          <form onSubmit={onSubmit} noValidate className="flex flex-col gap-md">
            {!location.state?.email && (
              <Field
                label={t("auth.email")}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={errors.email}
                required
              />
            )}
            <Field
              label={t("auth.code")}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              error={errors.code}
              inputMode="numeric"
              placeholder="000000"
              className="text-center text-2xl tracking-[0.5em]"
              required
            />
            <Button type="submit" loading={submitting} className="w-full">
              {t("auth.verify")}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
