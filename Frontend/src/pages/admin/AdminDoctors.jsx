import { useCallback, useEffect, useMemo, useState } from "react";
import { createDoctor, updateDoctor } from "../../lib/api/admin.js";
import { getDepartments } from "../../lib/api/departments.js";
import { searchDoctors } from "../../lib/api/doctors.js";
import { errorText } from "../../lib/api/errorText.js";
import { getFilials } from "../../lib/api/filials.js";
import { useT } from "../../lib/i18n.jsx";
import { copyToClipboard, generatePassword } from "../../lib/password.js";
import { useToast } from "../../lib/toast.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import ErrorState from "../../components/ErrorState.jsx";
import { Field, Select } from "../../components/Field.jsx";
import Modal from "../../components/Modal.jsx";
import LoadingStatus from "../../components/LoadingStatus.jsx";
import Skeleton from "../../components/Skeleton.jsx";
import DoctorAssignments from "./DoctorAssignments.jsx";

const EMPTY_FORM = { email: "", full_name: "", specialization: "", phone: "" };

export default function AdminDoctors() {
  const t = useT();
  const toast = useToast();
  const [doctors, setDoctors] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [filials, setFilials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filialId, setFilialId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [specialization, setSpecialization] = useState("");
  const [specializations, setSpecializations] = useState([]);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [created, setCreated] = useState(null);
  const [editing, setEditing] = useState(null);
  const [editForm, setEditForm] = useState({ full_name: "", specialization: "" });
  const [updating, setUpdating] = useState(false);
  const [assigning, setAssigning] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(false);
    return searchDoctors({
      filial_id: filialId || undefined,
      department_id: departmentId || undefined,
      specialization: specialization || undefined,
    })
      .then(setDoctors)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [filialId, departmentId, specialization]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    Promise.all([getDepartments(), getFilials(), searchDoctors()])
      .then(([deps, brs, all]) => {
        setDepartments(deps);
        setFilials(brs);
        setSpecializations(
          [...new Set(all.map((d) => d.specialization))].sort((a, b) => a.localeCompare(b))
        );
      })
      .catch(() => {});
  }, []);

  const visibleDepartments = useMemo(
    () => (filialId ? departments.filter((d) => String(d.filial_id) === filialId) : departments),
    [departments, filialId]
  );

  const change = (name) => (e) => setForm((prev) => ({ ...prev, [name]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);

    const password = generatePassword();

    try {
      const doctor = await createDoctor({
        email: form.email.trim(),
        password,
        full_name: form.full_name.trim(),
        specialization: form.specialization.trim(),
        phone: form.phone.trim() || null,
      });
      setCreating(false);
      setForm(EMPTY_FORM);
      setCreated({ ...doctor, email: form.email.trim(), password });
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setSaving(false);
    }
  };

  const openEdit = (doctor) => {
    setEditForm({ full_name: doctor.full_name, specialization: doctor.specialization });
    setEditing(doctor);
  };

  const submitEdit = async (e) => {
    e.preventDefault();
    setUpdating(true);

    try {
      await updateDoctor(editing.id, {
        full_name: editForm.full_name.trim(),
        specialization: editForm.specialization.trim(),
      });
      toast.success(t("common.saved"));
      setEditing(null);
      await load();
    } catch (err) {
      toast.error(errorText(t, err));
    } finally {
      setUpdating(false);
    }
  };

  const copyCredentials = async () => {
    const ok = await copyToClipboard(`${created.email}\n${created.password}`);
    if (ok) toast.success(t("admin.credentialsCopied"));
    else toast.error(t("admin.copyFailed"));
  };

  if (error) return <ErrorState onRetry={load} />;

  return (
    <div className="space-y-md">
      <div className="flex justify-end">
        <Button icon="person_add" onClick={() => setCreating(true)}>
          {t("admin.addDoctor")}
        </Button>
      </div>

      <div className="grid gap-sm sm:grid-cols-3">
        <Select
          label={t("admin.filial")}
          value={filialId}
          onChange={(e) => {
            setFilialId(e.target.value);
            setDepartmentId("");
          }}
        >
          <option value="">{t("common.all")}</option>
          {filials.map((filial) => (
            <option key={filial.id} value={filial.id}>
              {filial.name}
            </option>
          ))}
        </Select>
        <Select
          label={t("admin.department")}
          value={departmentId}
          onChange={(e) => setDepartmentId(e.target.value)}
        >
          <option value="">{t("common.all")}</option>
          {visibleDepartments.map((department) => (
            <option key={department.id} value={department.id}>
              {department.name}
            </option>
          ))}
        </Select>
        <Select
          label={t("admin.specialization")}
          value={specialization}
          onChange={(e) => setSpecialization(e.target.value)}
        >
          <option value="">{t("common.all")}</option>
          {specializations.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </Select>
      </div>

      {loading ? (
        <div className="space-y-sm">
          <LoadingStatus />
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-14" />
          ))}
        </div>
      ) : doctors.length === 0 ? (
        <EmptyState icon="stethoscope" title={t("admin.noDoctors")} />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left text-body-md">
            <thead className="border-b border-outline-variant text-label-md text-on-surface-variant">
              <tr>
                <th className="px-4 py-3 font-semibold">#</th>
                <th className="px-4 py-3 font-semibold">{t("admin.fullName")}</th>
                <th className="px-4 py-3 font-semibold">{t("admin.specialization")}</th>
                <th className="px-4 py-3 text-right font-semibold">{t("admin.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {doctors.map((doctor) => (
                <tr key={doctor.id} className="border-b border-outline-variant/50 last:border-0">
                  <td className="px-4 py-3 text-on-surface-variant">{doctor.id}</td>
                  <td className="px-4 py-3 font-semibold text-on-surface">{doctor.full_name}</td>
                  <td className="px-4 py-3 text-on-surface-variant">{doctor.specialization}</td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={() => openEdit(doctor)}
                        aria-label={t("common.edit")}
                        className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
                      >
                        <span aria-hidden="true" className="material-symbols-outlined text-lg">edit</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setAssigning(doctor)}
                        aria-label={t("admin.assignDepartment")}
                        className="grid h-9 w-9 place-items-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
                      >
                        <span aria-hidden="true" className="material-symbols-outlined text-lg">meeting_room</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {creating && (
        <Modal
          title={t("admin.addDoctor")}
          onClose={() => setCreating(false)}
          footer={
            <>
              <Button variant="outline" onClick={() => setCreating(false)} className="flex-1">
                {t("common.cancel")}
              </Button>
              <Button
                form="doctor-form"
                type="submit"
                loading={saving}
                disabled={
                  !form.email.trim() || !form.full_name.trim() || !form.specialization.trim()
                }
                className="flex-1"
              >
                {t("common.create")}
              </Button>
            </>
          }
        >
          <form id="doctor-form" onSubmit={submit} className="space-y-sm">
            <p className="rounded-xl bg-secondary-container px-4 py-3 text-label-md text-on-secondary-container">
              {t("admin.passwordHint")}
            </p>
            <Field
              label={t("admin.email")}
              type="email"
              required
              value={form.email}
              onChange={change("email")}
            />
            <Field
              label={t("admin.fullName")}
              required
              value={form.full_name}
              onChange={change("full_name")}
            />
            <Field
              label={t("admin.specialization")}
              required
              list="specialization-options"
              value={form.specialization}
              onChange={change("specialization")}
            />
            <datalist id="specialization-options">
              {specializations.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
            <Field
              label={t("admin.phone")}
              hint={t("common.optional")}
              value={form.phone}
              onChange={change("phone")}
            />
          </form>
        </Modal>
      )}

      {assigning && (
        <DoctorAssignments
          doctor={assigning}
          departments={departments}
          onClose={() => {
            setAssigning(null);
            load();
          }}
        />
      )}

      {editing && (
        <Modal
          title={t("admin.editDoctor")}
          onClose={() => setEditing(null)}
          footer={
            <>
              <Button variant="outline" onClick={() => setEditing(null)} className="flex-1">
                {t("common.cancel")}
              </Button>
              <Button
                form="doctor-edit-form"
                type="submit"
                loading={updating}
                disabled={!editForm.full_name.trim() || !editForm.specialization.trim()}
                className="flex-1"
              >
                {t("common.save")}
              </Button>
            </>
          }
        >
          <form id="doctor-edit-form" onSubmit={submitEdit} className="space-y-sm">
            <Field
              label={t("admin.fullName")}
              required
              value={editForm.full_name}
              onChange={(e) => setEditForm((prev) => ({ ...prev, full_name: e.target.value }))}
            />
            <Field
              label={t("admin.specialization")}
              required
              list="specialization-options"
              value={editForm.specialization}
              onChange={(e) => setEditForm((prev) => ({ ...prev, specialization: e.target.value }))}
            />
            <datalist id="specialization-options">
              {specializations.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </form>
        </Modal>
      )}

      {created && (
        <Modal
          title={t("admin.doctorCreated")}
          onClose={() => setCreated(null)}
          footer={
            <>
              <Button variant="outline" icon="content_copy" onClick={copyCredentials} className="flex-1">
                {t("admin.copyCredentials")}
              </Button>
              <Button onClick={() => setCreated(null)} className="flex-1">
                {t("common.close")}
              </Button>
            </>
          }
        >
          <p className="mb-md text-body-md text-on-surface">{t("admin.passwordOnce")}</p>
          <dl className="space-y-sm">
            <div className="rounded-xl border border-outline-variant p-md">
              <dt className="text-label-md text-on-surface-variant">{t("admin.email")}</dt>
              <dd className="mt-1 font-mono text-body-lg text-on-surface">{created.email}</dd>
            </div>
            <div className="rounded-xl border border-outline-variant p-md">
              <dt className="text-label-md text-on-surface-variant">{t("admin.password")}</dt>
              <dd className="mt-1 select-all font-mono text-body-lg font-bold text-primary">
                {created.password}
              </dd>
            </div>
          </dl>
        </Modal>
      )}
    </div>
  );
}
