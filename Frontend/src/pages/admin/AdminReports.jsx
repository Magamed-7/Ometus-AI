import { useEffect, useState } from "react";
import { getSummaryReport, getWorkloadReport } from "../../lib/api/admin.js";
import { getDepartments } from "../../lib/api/departments.js";
import { errorText } from "../../lib/api/errorText.js";
import { isoDate } from "../../lib/format.js";
import { useT } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Field, Select } from "../../components/Field.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";

function monthStart() {
  const now = new Date();
  return isoDate(new Date(now.getFullYear(), now.getMonth(), 1));
}

function SummaryTile({ icon, label, value, accent = false }) {
  return (
    <div className="rounded-2xl border border-outline-variant bg-surface-container-lowest p-md">
      <div className="flex items-center gap-2 text-on-surface-variant">
        <span aria-hidden="true" className="material-symbols-outlined text-lg">{icon}</span>
        <span className="text-label-md">{label}</span>
      </div>
      <p
        className={`mt-1 text-headline-lg-mobile font-bold ${
          accent ? "text-primary" : "text-on-surface"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

export default function AdminReports() {
  const t = useT();
  const toast = useToast();
  const [departments, setDepartments] = useState([]);
  const [dateFrom, setDateFrom] = useState(monthStart);
  const [dateTo, setDateTo] = useState(() => isoDate(new Date()));
  const [departmentId, setDepartmentId] = useState("");
  const [rows, setRows] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = () => {
    setLoading(true);
    setError(false);
    return Promise.all([
      getWorkloadReport({
        date_from: dateFrom,
        date_to: dateTo,
        department_id: departmentId || undefined,
      }),
      getSummaryReport({ date_from: dateFrom, date_to: dateTo }),
    ])
      .then(([workload, total]) => {
        setRows(workload);
        setSummary(total);
      })
      .catch((err) => {
        setError(err);
        toast.error(errorText(t, err));
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    getDepartments()
      .then(setDepartments)
      .catch(() => {});
  }, []);

  const invalidRange = !dateFrom || !dateTo || dateFrom > dateTo;

  return (
    <div className="space-y-md">
      <Card className="p-md">
        <div className="grid items-end gap-sm sm:grid-cols-2 lg:grid-cols-4">
          <Field
            label={t("admin.dateFrom")}
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
          />
          <Field
            label={t("admin.dateTo")}
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
          />
          <Select
            label={t("admin.department")}
            value={departmentId}
            onChange={(e) => setDepartmentId(e.target.value)}
          >
            <option value="">{t("common.all")}</option>
            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.name}
              </option>
            ))}
          </Select>
          <Button icon="monitoring" onClick={load} disabled={invalidRange} loading={loading}>
            {t("admin.build")}
          </Button>
        </div>
        {invalidRange && dateFrom && dateTo && (
          <p className="mt-sm text-label-md text-error">{t("errors.INVALID_DATE_RANGE")}</p>
        )}
      </Card>

      {loading ? (
        <div className="space-y-md">
          <LoadingStatus />
          <div className="grid gap-sm sm:grid-cols-2 lg:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={load} />
      ) : (
        <>
          {summary && (
            <section className="space-y-sm">
              <h2 className="text-headline-md text-on-surface">{t("admin.reportSummary")}</h2>
              <div className="grid gap-sm sm:grid-cols-2 lg:grid-cols-4">
                <SummaryTile icon="event_note" label={t("admin.total")} value={summary.total} accent />
                <SummaryTile icon="event_available" label={t("status.booked")} value={summary.booked} />
                <SummaryTile icon="task_alt" label={t("status.completed")} value={summary.completed} />
                <SummaryTile icon="event_busy" label={t("status.cancelled")} value={summary.cancelled} />
                <SummaryTile icon="person_off" label={t("status.no_show")} value={summary.no_show} />
                {/* без знаменателя «3» читается как «в клинике три врача»:
                    бэкенд отдаёт doctors_total именно для этого */}
                <SummaryTile
                  icon="stethoscope"
                  label={t("admin.doctorsInvolved")}
                  value={
                    summary.doctors_total
                      ? `${summary.doctors} / ${summary.doctors_total}`
                      : summary.doctors
                  }
                />
                <SummaryTile
                  icon="groups"
                  label={t("admin.patientsUnique")}
                  value={summary.patients}
                />
              </div>
            </section>
          )}

          <h2 className="text-headline-md text-on-surface">{t("admin.reportWorkload")}</h2>

          {rows.length === 0 ? (
            <EmptyState icon="monitoring" title={t("admin.noDoctors")} />
          ) : (
            <Card className="overflow-x-auto">
              <table className="w-full min-w-[44rem] text-left text-body-md">
                <thead className="border-b border-outline-variant text-label-md text-on-surface-variant">
                  <tr>
                    <th className="px-4 py-3 font-semibold">{t("admin.fullName")}</th>
                    <th className="px-4 py-3 font-semibold">{t("admin.specialization")}</th>
                    <th className="px-4 py-3 text-right font-semibold">{t("admin.total")}</th>
                    <th className="px-4 py-3 text-right font-semibold">{t("admin.booked")}</th>
                    <th className="px-4 py-3 text-right font-semibold">{t("admin.completed")}</th>
                    <th className="px-4 py-3 text-right font-semibold">{t("admin.cancelled")}</th>
                    <th className="px-4 py-3 text-right font-semibold">{t("admin.noShow")}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr
                      key={row.doctor_id}
                      className="border-b border-outline-variant/50 last:border-0"
                    >
                      <td className="px-4 py-3 font-semibold text-on-surface">{row.full_name}</td>
                      <td className="px-4 py-3 text-on-surface-variant">{row.specialization}</td>
                      <td className="px-4 py-3 text-right font-bold text-primary">{row.total}</td>
                      <td className="px-4 py-3 text-right text-on-surface-variant">{row.booked}</td>
                      <td className="px-4 py-3 text-right text-on-surface-variant">
                        {row.completed}
                      </td>
                      <td className="px-4 py-3 text-right text-on-surface-variant">
                        {row.cancelled}
                      </td>
                      <td className="px-4 py-3 text-right text-on-surface-variant">{row.no_show}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
