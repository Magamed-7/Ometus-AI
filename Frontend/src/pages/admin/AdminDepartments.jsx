import { useCallback, useEffect, useState } from "react";
import { getDepartments } from "../../lib/api/departments.js";
import { getFilials } from "../../lib/api/filials.js";
import { useT } from "../../lib/i18n.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Select } from "../../components/Field.jsx";
import Skeleton from "../../components/Skeleton.jsx";

export default function AdminDepartments() {
  const t = useT();
  const [departments, setDepartments] = useState([]);
  const [filials, setFilials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filialId, setFilialId] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return Promise.all([getDepartments(), getFilials()])
      .then(([deps, brs]) => {
        setDepartments(deps);
        setFilials(brs);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filialNames = Object.fromEntries(filials.map((f) => [f.id, f.name]));
  const rows = filialId ? departments.filter((d) => String(d.filial_id) === filialId) : departments;

  if (error) return <ErrorState onRetry={load} />;

  return (
    <div className="space-y-md">
      <div className="w-full sm:w-64">
        <Select
          label={t("admin.filial")}
          value={filialId}
          onChange={(e) => setFilialId(e.target.value)}
        >
          <option value="">{t("common.all")}</option>
          {filials.map((filial) => (
            <option key={filial.id} value={filial.id}>
              {filial.name}
            </option>
          ))}
        </Select>
      </div>

      {loading ? (
        <div className="space-y-sm">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-14" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <EmptyState icon="meeting_room" title={t("admin.noDepartments")} />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left text-body-md">
            <thead className="border-b border-outline-variant text-label-md text-on-surface-variant">
              <tr>
                <th className="px-4 py-3 font-semibold">{t("admin.name")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.filial")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.description")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((department) => (
                <tr
                  key={department.id}
                  className="border-b border-outline-variant/50 last:border-0"
                >
                  <td className="px-4 py-3 font-semibold text-on-surface">{department.name}</td>
                  <td className="px-4 py-3 text-on-surface-variant">
                    {filialNames[department.filial_id] || `#${department.filial_id}`}
                  </td>
                  <td className="px-4 py-3 text-on-surface-variant">
                    {department.description || "—"}
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
