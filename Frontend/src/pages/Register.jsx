import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as authApi from "../lib/api/auth.js";
import { errorText } from "../lib/api/errorText.js";
import { useT } from "../lib/i18n.jsx";
import { useToast } from "../lib/toast.jsx";
import Button from "../components/Button.jsx";
import { Field } from "../components/Field.jsx";
import LangSwitcher from "../components/LangSwitcher.jsx";
import ThemeToggle from "../components/ThemeToggle.jsx";

const EMPTY = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  password: "",
  passwordConfirm: "",
};

export default function Register() {
  const t = useT();
  const toast = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const validate = () => {
    const next = {};
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email)) next.email = t("errors.VALIDATION_ERROR");
    if (form.password.length < 8) next.password = t("auth.passwordMin");
    if (form.passwordConfirm !== form.password) next.passwordConfirm = t("auth.passwordMismatch");
    if (form.phone && form.phone.replace(/\D/g, "").length < 9) next.phone = t("errors.VALIDATION_ERROR");
    return next;
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    const found = validate();
    setErrors(found);
    if (Object.keys(found).length) return;

    setSubmitting(true);
    try {
      await authApi.register({
        email: form.email,
        password: form.password,
        first_name: form.first_name || null,
        last_name: form.last_name || null,
        phone: form.phone || null,
        role: "patient",
      });
      toast.success(t("auth.verifySent"));
      navigate("/verify-email", { state: { email: form.email } });
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
        <div className="w-full max-w-form rounded-2xl border border-outline-variant bg-surface-container-lowest p-lg shadow-sm">
          <h1 className="text-headline-lg-mobile font-bold text-on-surface">
            {t("auth.registerTitle")}
          </h1>
          <p className="mb-lg mt-1 text-body-md text-on-surface-variant">
            {t("auth.registerSubtitle")}
          </p>

          {errors.form && (
            <div className="mb-md rounded-xl border border-error/40 bg-error-container px-4 py-3 text-body-md text-on-error-container">
              {errors.form}
            </div>
          )}

          <form onSubmit={onSubmit} noValidate className="flex flex-col gap-md">
            <div className="grid grid-cols-1 gap-md sm:grid-cols-2">
              <Field label={t("auth.firstName")} value={form.first_name} onChange={set("first_name")} error={errors.first_name} />
              <Field label={t("auth.lastName")} value={form.last_name} onChange={set("last_name")} error={errors.last_name} />
            </div>
            <Field label={t("auth.email")} type="email" value={form.email} onChange={set("email")} error={errors.email} required autoComplete="email" />
            <Field label={t("auth.phone")} value={form.phone} onChange={set("phone")} error={errors.phone} placeholder="+992 …" />
            <Field label={t("auth.password")} type="password" value={form.password} onChange={set("password")} error={errors.password} required autoComplete="new-password" />
            <Field label={t("auth.passwordConfirm")} type="password" value={form.passwordConfirm} onChange={set("passwordConfirm")} error={errors.passwordConfirm} required autoComplete="new-password" />
            <Button type="submit" loading={submitting} className="w-full">
              {t("auth.signUp")}
            </Button>
          </form>

          <p className="mt-md text-center text-body-md text-on-surface-variant">
            {t("auth.haveAccount")}{" "}
            <Link to="/login" className="font-semibold text-primary hover:underline">
              {t("auth.toLogin")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
