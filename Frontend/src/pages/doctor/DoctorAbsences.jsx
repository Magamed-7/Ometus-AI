import { useCallback, useEffect, useState } from "react";
import { errorText } from "../../lib/api/errorText.js";
import { createMyAbsence, deleteMyAbsence, getMyAbsences } from "../../lib/api/schedules.js";
import { formatDate, isoDate } from "../../lib/format.js";
import { useI18n } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Field } from "../../components/Field.jsx";
import Skeleton from "../../components/Skeleton.jsx";

const today = () => isoDate(new Date());

export default function DoctorAbsences() {
  const { t, lang } = useI18n();
  const toast = useToast();
  const [absences, setAbsences] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ date_from: today(), date_to: today(), reason: "" });
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return getMyAbsences()
      .then(setAbsences)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const change = (name) => (e) => setForm((prev) => ({ ...prev, [name]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      await createMyAbsence({
        date_from: form.date_from,
        date_to: form.date_to,
        reason: form.reason.trim() || null,
      });
      toast.success(t("common.saved"));
      setForm({ date_from: today(), date_to: today(), reason: "" });
      setOpen(false);
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async (absence) => {
    if (!window.confirm(t("doctorCabinet.deleteAbsenceConfirm"))) return;

    setRemoving(absence.id);

    try {
      await deleteMyAbsence(absence.id);
      toast.success(t("doctorCabinet.absenceDeleted"));
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setRemoving(null);
    }
  };

  const sorted = [...absences].sort((a, b) => String(b.date_from).localeCompare(String(a.date_from)));

  return (
    <section className="mt-xl">
      <div className="mb-md flex flex-wrap items-center justify-between gap-sm">
        <h2 className="text-headline-md font-bold text-on-surface">{t("doctorCabinet.absences")}</h2>
        <Button
          variant={open ? "outline" : "primary"}
          icon={open ? "close" : "add"}
          onClick={() => setOpen((prev) => !prev)}
        >
          {open ? t("common.cancel") : t("doctorCabinet.addAbsence")}
        </Button>
      </div>

      {open && (
        <Card as="form" onSubmit={submit} className="mb-md space-y-md p-md">
          <div className="grid gap-sm sm:grid-cols-3">
            <Field
              label={t("doctorCabinet.dateFrom")}
              type="date"
              required
              value={form.date_from}
              onChange={change("date_from")}
            />
            <Field
              label={t("doctorCabinet.dateTo")}
              type="date"
              required
              min={form.date_from}
              value={form.date_to}
              onChange={change("date_to")}
            />
            <Field
              label={t("doctorCabinet.reason")}
              hint={t("common.optional")}
              value={form.reason}
              onChange={change("reason")}
            />
          </div>
          <Button type="submit" icon="save" loading={saving}>
            {t("common.save")}
          </Button>
        </Card>
      )}

      {error ? (
        <ErrorState onRetry={load} />
      ) : loading ? (
        <div className="space-y-sm">
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      ) : sorted.length === 0 ? (
        <EmptyState
          icon="beach_access"
          title={t("doctorCabinet.noAbsences")}
          text={t("doctorCabinet.noAbsencesText")}
        />
      ) : (
        <div className="space-y-sm">
          {sorted.map((absence) => (
            <Card
              key={absence.id}
              className="flex flex-wrap items-center justify-between gap-sm p-md"
            >
              <div className="flex items-center gap-md">
                <span className="material-symbols-outlined text-tertiary">beach_access</span>
                <div>
                  <p className="font-bold text-on-surface">
                    {formatDate(absence.date_from, lang)} – {formatDate(absence.date_to, lang)}
                  </p>
                  {absence.reason && (
                    <p className="text-label-md text-on-surface-variant">{absence.reason}</p>
                  )}
                </div>
              </div>
              <button
                type="button"
                onClick={() => remove(absence)}
                disabled={removing === absence.id}
                aria-label={t("common.delete")}
                className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-error-container hover:text-error disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-lg">delete</span>
              </button>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
