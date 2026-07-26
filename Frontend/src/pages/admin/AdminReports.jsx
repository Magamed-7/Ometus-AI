import { useEffect, useState } from "react";
import { getWorkloadReport } from "../../lib/api/admin.js";
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
import Skeleton from "../../components/Skeleton.jsx";

function monthStart() {
  const now = new Date();
  return isoDate(new Date(now.getFullYear(), now.getMonth(), 1));
}

export default function AdminReports() {
  const t = useT();
  const toast = useToast();
  const [departments, setDepartments] = useState([]);
  const [dateFrom, setDateFrom] = useState(monthStart);
  const [dateTo, setDateTo] = useState(() => isoDate(new Date()));
  const [departmentId, setDepartmentId] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = () => {
    setLoading(true);
    setError(false);
    return getWorkloadReport({
      date_from: dateFrom,
      date_to: dateTo,
      department_id: departmentId || undefined,
    })
      .then(setRows)
      .catch((err) => {
        setError(true);
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
        <h2 className="mb-sm text-headline-md text-on-surface">{t("admin.reportWorkload")}</h2>
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
        <div className="space-y-sm">
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      ) : error ? (
        <ErrorState onRetry={load} />
      ) : rows.length === 0 ? (
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
                  <td className="px-4 py-3 text-right text-on-surface-variant">{row.completed}</td>
                  <td className="px-4 py-3 text-right text-on-surface-variant">{row.cancelled}</td>
                  <td className="px-4 py-3 text-right text-on-surface-variant">{row.no_show}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
