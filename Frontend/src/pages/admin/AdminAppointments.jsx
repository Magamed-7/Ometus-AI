import { useCallback, useEffect, useState } from "react";
import { getAllAppointments } from "../../lib/api/admin.js";
import { searchDoctors } from "../../lib/api/doctors.js";
import { clock, formatDate, isoDate, phone as formatPhone } from "../../lib/format.js";
import { useI18n } from "../../lib/i18n.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Field, Select } from "../../components/Field.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";
import StatusPill from "../../components/StatusPill.jsx";

const STATUSES = ["booked", "completed", "cancelled", "no_show"];

function monthStart() {
  const now = new Date();
  return isoDate(new Date(now.getFullYear(), now.getMonth(), 1));
}

export default function AdminAppointments() {
  const { t, lang } = useI18n();
  const [doctors, setDoctors] = useState([]);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [doctorId, setDoctorId] = useState("");
  const [status, setStatus] = useState("");
  const [dateFrom, setDateFrom] = useState(monthStart);
  const [dateTo, setDateTo] = useState(() => isoDate(new Date()));

  const invalidRange = Boolean(dateFrom && dateTo && dateFrom > dateTo);

  const load = useCallback(() => {
    if (invalidRange) return Promise.resolve();
    setLoading(true);
    setError(false);
    return getAllAppointments({
      doctor_id: doctorId || undefined,
      status: status || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    })
      .then(setRows)
      .catch((e) => setError(e))
      .finally(() => setLoading(false));
  }, [doctorId, status, dateFrom, dateTo, invalidRange]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    searchDoctors()
      .then(setDoctors)
      .catch(() => {});
  }, []);

  const reset = () => {
    setDoctorId("");
    setStatus("");
    setDateFrom(monthStart());
    setDateTo(isoDate(new Date()));
  };

  return (
    <div className="space-y-md">
      <Card className="p-md">
        <div className="grid items-end gap-sm sm:grid-cols-2 lg:grid-cols-4">
          <Select
            label={t("admin.doctor")}
            value={doctorId}
            onChange={(e) => setDoctorId(e.target.value)}
          >
            <option value="">{t("common.all")}</option>
            {doctors.map((doctor) => (
              <option key={doctor.id} value={doctor.id}>
                {doctor.full_name}
              </option>
            ))}
          </Select>
          <Select
            label={t("doctorCabinet.filterStatus")}
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">{t("common.all")}</option>
            {STATUSES.map((value) => (
              <option key={value} value={value}>
                {t(`status.${value}`)}
              </option>
            ))}
          </Select>
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
        </div>
        <div className="mt-sm flex flex-wrap items-center gap-sm">
          <Button variant="outline" icon="refresh" onClick={reset}>
            {t("common.reset")}
          </Button>
          {!loading && !error && (
            <span className="text-label-md text-on-surface-variant">
              {t("admin.found", { count: rows.length })}
            </span>
          )}
        </div>
        {invalidRange && (
          <p className="mt-sm text-label-md text-error">{t("errors.INVALID_DATE_RANGE")}</p>
        )}
      </Card>

      {error ? (
        <ErrorState error={error} onRetry={load} />
      ) : loading ? (
        <div className="space-y-sm">
          <LoadingStatus />
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-14" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <EmptyState icon="event_busy" title={t("admin.noAppointments")} />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[48rem] text-left text-body-md">
            <thead className="border-b border-outline-variant text-label-md text-on-surface-variant">
              <tr>
                <th className="px-4 py-3 font-semibold">{t("booking.date")}</th>
                <th className="px-4 py-3 font-semibold">{t("booking.time")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.doctor")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.patient")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.phone")}</th>
                <th className="px-4 py-3 font-semibold">{t("doctorCabinet.filterStatus")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-outline-variant/50 last:border-0">
                  <td className="whitespace-nowrap px-4 py-3 text-on-surface">
                    {formatDate(row.date, lang)}
                  </td>
                  <td className="px-4 py-3 font-semibold text-on-surface">{clock(row.time)}</td>
                  <td className="px-4 py-3">
                    <span className="font-semibold text-on-surface">{row.doctor_name}</span>
                    <span className="block text-label-md text-on-surface-variant">
                      {row.specialization}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-on-surface">
                    {row.patient_name || `#${row.patient_id}`}
                  </td>
                  <td className="px-4 py-3 text-on-surface-variant">
                    {row.patient_phone ? (
                      <a href={`tel:${row.patient_phone}`} className="hover:text-primary">
                        {formatPhone(row.patient_phone)}
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-xs">
                      <StatusPill status={row.status} />
                      {row.is_emergency && (
                        <span className="rounded-full bg-error-container px-2 py-0.5 text-label-md font-semibold text-on-error-container">
                          {t("admin.emergency")}
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
