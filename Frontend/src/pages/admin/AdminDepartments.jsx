import { useCallback, useEffect, useState } from "react";
import {
  createDepartment,
  deleteDepartment,
  updateDepartment,
} from "../../lib/api/admin.js";
import { getDepartments } from "../../lib/api/departments.js";
import { errorText } from "../../lib/api/errorText.js";
import { getFilials } from "../../lib/api/filials.js";
import { useT } from "../../lib/i18n.jsx";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ConfirmDialog from "../../components/ConfirmDialog.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Field, Select } from "../../components/Field.jsx";
import Modal from "../../components/Modal.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";

const EMPTY_FORM = { filial_id: "", name: "", description: "" };

export default function AdminDepartments() {
  const t = useT();
  const toast = useToast();
  const [departments, setDepartments] = useState([]);
  const [filials, setFilials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filialId, setFilialId] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(null);
  const [deleting, setDeleting] = useState(false);

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

  const change = (name) => (e) => setForm((prev) => ({ ...prev, [name]: e.target.value }));

  const openCreate = () => {
    setForm({ ...EMPTY_FORM, filial_id: filialId || String(filials[0]?.id || "") });
    setEditing("new");
  };

  const openEdit = (department) => {
    setForm({
      filial_id: String(department.filial_id),
      name: department.name,
      description: department.description || "",
    });
    setEditing(department);
  };

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const payload = {
      filial_id: Number(form.filial_id),
      name: form.name.trim(),
      description: form.description.trim() || null,
    };

    try {
      if (editing === "new") {
        await createDepartment(payload);
      } else {
        await updateDepartment(editing.id, payload);
      }
      toast.success(t("common.saved"));
      setEditing(null);
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    setDeleting(true);

    try {
      await deleteDepartment(removing.id);
      toast.success(t("admin.departmentDeleted"));
      setRemoving(null);
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setDeleting(false);
    }
  };

  if (error) return <ErrorState onRetry={load} />;

  return (
    <div className="space-y-md">
      <div className="flex flex-wrap items-end justify-between gap-sm">
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
        <Button icon="add" onClick={openCreate} disabled={filials.length === 0}>
          {t("admin.addDepartment")}
        </Button>
      </div>

      {loading ? (
        <div className="space-y-sm">
          <LoadingStatus />
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-14" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <EmptyState icon="meeting_room" title={t("admin.noDepartments")} />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[42rem] text-left text-body-md">
            <thead className="border-b border-outline-variant text-label-md text-on-surface-variant">
              <tr>
                <th className="px-4 py-3 font-semibold">{t("admin.name")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.filial")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.description")}</th>
                <th className="px-4 py-3 text-right font-semibold">{t("admin.actions")}</th>
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
                  <td className="px-4 py-3">
                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={() => openEdit(department)}
                        aria-label={t("common.edit")}
                        className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
                      >
                        <span aria-hidden="true" className="material-symbols-outlined text-lg">edit</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setRemoving(department)}
                        aria-label={t("common.delete")}
                        className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-error-container hover:text-error"
                      >
                        <span aria-hidden="true" className="material-symbols-outlined text-lg">delete</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {editing && (
        <Modal
          title={editing === "new" ? t("admin.addDepartment") : t("admin.editDepartment")}
          onClose={() => setEditing(null)}
          footer={
            <>
              <Button variant="outline" onClick={() => setEditing(null)} className="flex-1">
                {t("common.cancel")}
              </Button>
              <Button
                form="department-form"
                type="submit"
                loading={saving}
                disabled={!form.name.trim() || !form.filial_id}
                className="flex-1"
              >
                {t("common.save")}
              </Button>
            </>
          }
        >
          <form id="department-form" onSubmit={submit} className="space-y-sm">
            <Select
              label={t("admin.filial")}
              required
              value={form.filial_id}
              onChange={change("filial_id")}
            >
              {filials.map((filial) => (
                <option key={filial.id} value={filial.id}>
                  {filial.name}
                </option>
              ))}
            </Select>
            <Field label={t("admin.name")} required value={form.name} onChange={change("name")} />
            <Field
              label={t("admin.description")}
              hint={t("common.optional")}
              value={form.description}
              onChange={change("description")}
            />
          </form>
        </Modal>
      )}

      {removing && (
        <ConfirmDialog
          title={t("admin.deleteDepartment")}
          text={t("admin.deleteDepartmentConfirm", { name: removing.name })}
          loading={deleting}
          onConfirm={remove}
          onClose={() => setRemoving(null)}
        />
      )}
    </div>
  );
}
