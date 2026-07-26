from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.permissions import require_role
from app.core.errors import AppError
from app.db.database import get_db
from app.schemas.schema_department import (
    DepartmentCreateIn,
    DepartmentOut,
    DepartmentUpdateIn,
)
from app.schemas.schema_appointment import AdminAppointmentOut
from app.schemas.schema_doctor import (
    DoctorCreateIn,
    DoctorCreateOut,
    DoctorDismissIn,
    DoctorDismissOut,
    DoctorDepartmentIn,
    DoctorOut,
    DoctorUpdateIn,
    SpecializationIn,
)
from app.schemas.schema_patient import DependentCreateIn, PatientOut
from app.schemas.schema_filial import FilialCreateIn, FilialOut, FilialUpdateIn
from app.schemas.schema_report import AppointmentsSummaryOut, DoctorWorkloadOut
from app.schemas.schema_schedule import ScheduleCreateIn, ScheduleOut, ScheduleUpdateIn
from app.schemas.schema_user import RoleUpdateIn, UserOut
from app.services import (
    crud_appointment,
    crud_department,
    crud_doctor,
    crud_filial,
    crud_patient,
    crud_report,
    crud_schedule,
    crud_user,
)

admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


@admin_router.post("/filials", response_model=FilialOut)
async def create_filial(
    data: FilialCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    return await crud_filial.create_filial(data, db)


@admin_router.put("/filials/{filial_id}", response_model=FilialOut)
async def update_filial(
    filial_id: int,
    data: FilialUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    filial = await crud_filial.get_by_id(filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    return await crud_filial.update_filial(filial, data, db)


@admin_router.delete("/filials/{filial_id}")
async def delete_filial(
    filial_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    filial = await crud_filial.get_by_id(filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    await crud_filial.delete_filial(filial, db)
    return {"message": "Филиал удалён"}


@admin_router.post("/departments", response_model=DepartmentOut)
async def create_department(
    data: DepartmentCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    filial = await crud_filial.get_by_id(data.filial_id, db)

    if filial is None:
        raise AppError(code="FILIAL_NOT_FOUND", message="Филиал не найден", status_code=404)

    return await crud_department.create_department(data, db)


@admin_router.put("/departments/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: int,
    data: DepartmentUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    department = await crud_department.get_by_id(department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    return await crud_department.update_department(department, data, db)


@admin_router.delete("/departments/{department_id}")
async def delete_department(
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    department = await crud_department.get_by_id(department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    await crud_department.delete_department(department, db)
    return {"message": "Отделение удалено"}


@admin_router.post("/doctors", response_model=DoctorCreateOut)
async def create_doctor(
    data: DoctorCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    existing_user = await crud_user.get_by_email(data.email, db)

    if existing_user:
        raise AppError(code="EMAIL_ALREADY_EXISTS", message="Email уже занят", status_code=409)

    return await crud_doctor.create_doctor(data, db)


@admin_router.put("/doctors/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: int,
    data: DoctorUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    return await crud_doctor.update_doctor(doctor, data, db)


@admin_router.post("/doctors/{doctor_id}/departments")
async def assign_doctor_department(
    doctor_id: int,
    data: DoctorDepartmentIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    department = await crud_department.get_by_id(data.department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    assignment = await crud_doctor.assign_department(doctor_id, data.department_id, db)

    if assignment is None:
        raise AppError(
            code="DOCTOR_ALREADY_IN_DEPARTMENT",
            message="Врач уже назначен в это отделение",
            status_code=409,
        )

    return {"message": "Врач назначен в отделение"}


@admin_router.delete("/doctors/{doctor_id}/departments/{department_id}")
async def remove_doctor_department(
    doctor_id: int,
    department_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    assignment = await crud_doctor.remove_department(doctor_id, department_id, db)

    if assignment is None:
        raise AppError(
            code="DOCTOR_NOT_IN_DEPARTMENT",
            message="Врач не назначен в это отделение",
            status_code=404,
        )

    return {"message": "Врач снят с отделения"}


@admin_router.post("/doctors/{doctor_id}/specializations")
async def add_doctor_specialization(
    doctor_id: int,
    data: SpecializationIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    specialization = await crud_doctor.add_specialization(doctor_id, data.name, db)

    if specialization is None:
        raise AppError(
            code="SPECIALIZATION_ALREADY_EXISTS",
            message="У врача уже есть эта специализация",
            status_code=409,
        )

    return {"message": "Специализация добавлена"}


@admin_router.delete("/doctors/{doctor_id}/specializations/{name}")
async def remove_doctor_specialization(
    doctor_id: int,
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    specialization = await crud_doctor.remove_specialization(doctor_id, name, db)

    if specialization is None:
        raise AppError(
            code="SPECIALIZATION_NOT_FOUND",
            message="У врача нет этой специализации",
            status_code=404,
        )

    return {"message": "Специализация снята"}


@admin_router.get("/reports/workload", response_model=list[DoctorWorkloadOut])
async def get_workload_report(
    date_from: date,
    date_to: date,
    department_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if date_from > date_to:
        raise AppError(
            code="INVALID_DATE_RANGE",
            message="Дата начала должна быть раньше даты окончания",
            status_code=400,
        )

    if department_id:
        department = await crud_department.get_by_id(department_id, db)

        if department is None:
            raise AppError(
                code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
            )

    return await crud_report.get_doctor_workload(db, date_from, date_to, department_id)


@admin_router.get("/doctors/{doctor_id}/schedules", response_model=list[ScheduleOut])
async def list_doctor_schedules(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    return await crud_schedule.get_schedules(doctor_id, db)


@admin_router.post("/doctors/{doctor_id}/schedules", response_model=ScheduleOut)
async def create_doctor_schedule(
    doctor_id: int,
    data: ScheduleCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    if data.start_time >= data.end_time:
        raise AppError(
            code="INVALID_TIME_RANGE",
            message="Начало работы должно быть раньше окончания",
            status_code=400,
        )

    department = await crud_department.get_by_id(data.department_id, db)

    if department is None:
        raise AppError(
            code="DEPARTMENT_NOT_FOUND", message="Отделение не найдено", status_code=404
        )

    departments = await crud_doctor.get_departments(doctor_id, db)

    if data.department_id not in [item.id for item in departments]:
        raise AppError(
            code="DOCTOR_NOT_IN_DEPARTMENT",
            message="Врач не работает в этом отделении",
            status_code=400,
        )

    existing = await crud_schedule.get_schedule_by_weekday(doctor_id, data.weekday, db)

    if data.department_id in [item.department_id for item in existing]:
        raise AppError(
            code="SCHEDULE_ALREADY_EXISTS",
            message="Расписание на этот день уже есть",
            status_code=409,
        )

    return await crud_schedule.create_schedule(doctor_id, data, db)


@admin_router.put("/doctors/{doctor_id}/schedules/{schedule_id}", response_model=ScheduleOut)
async def update_doctor_schedule(
    doctor_id: int,
    schedule_id: int,
    data: ScheduleUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    schedule = await crud_schedule.get_schedule_by_id(schedule_id, db)

    if schedule is None or schedule.doctor_id != doctor_id:
        raise AppError(code="SCHEDULE_NOT_FOUND", message="Расписание не найдено", status_code=404)

    start_time = data.start_time or schedule.start_time
    end_time = data.end_time or schedule.end_time

    if start_time >= end_time:
        raise AppError(
            code="INVALID_TIME_RANGE",
            message="Начало работы должно быть раньше окончания",
            status_code=400,
        )

    return await crud_schedule.update_schedule(schedule, data, db)


@admin_router.delete("/doctors/{doctor_id}/schedules/{schedule_id}")
async def delete_doctor_schedule(
    doctor_id: int,
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    schedule = await crud_schedule.get_schedule_by_id(schedule_id, db)

    if schedule is None or schedule.doctor_id != doctor_id:
        raise AppError(code="SCHEDULE_NOT_FOUND", message="Расписание не найдено", status_code=404)

    await crud_schedule.delete_schedule(schedule, db)
    return {"message": "Расписание удалено"}


@admin_router.get("/appointments", response_model=list[AdminAppointmentOut])
async def list_all_appointments(
    doctor_id: int | None = None,
    patient_id: int | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if date_from and date_to and date_from > date_to:
        raise AppError(
            code="INVALID_DATE_RANGE",
            message="Дата начала должна быть раньше даты окончания",
            status_code=400,
        )

    if doctor_id:
        doctor = await crud_doctor.get_by_id(doctor_id, db)

        if doctor is None:
            raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    return await crud_appointment.get_all_appointments(
        db, doctor_id, patient_id, status, date_from, date_to
    )


@admin_router.get("/reports/summary", response_model=AppointmentsSummaryOut)
async def get_summary_report(
    date_from: date,
    date_to: date,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if date_from > date_to:
        raise AppError(
            code="INVALID_DATE_RANGE",
            message="Дата начала должна быть раньше даты окончания",
            status_code=400,
        )

    return await crud_report.get_appointments_summary(db, date_from, date_to)


@admin_router.get("/users", response_model=list[UserOut])
async def list_users(
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    return await crud_user.get_all_users(db, role)


@admin_router.put("/users/{user_id}/role", response_model=UserOut)
async def change_user_role(
    user_id: int,
    data: RoleUpdateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if user_id == current_user.id:
        raise AppError(
            code="SELF_ROLE_CHANGE",
            message="Нельзя менять собственную роль",
            status_code=400,
        )

    user = await crud_user.get_by_id(user_id, db)

    if user is None:
        raise AppError(code="USER_NOT_FOUND", message="Пользователь не найден", status_code=404)

    if data.role == "doctor" and await crud_doctor.get_by_user_id(user_id, db) is None:
        raise AppError(
            code="DOCTOR_CARD_REQUIRED",
            message="Сначала заведите карточку врача через создание врача",
            status_code=400,
        )

    if data.role == "patient" and await crud_patient.get_by_user_id(user_id, db) is None:
        await crud_patient.create_patient(user, db)

    return await crud_user.set_role(user, data.role, db)


# админ заводит родственника «в аккаунте пациента» — тот же лимит и те же правила,
# что и у самого пациента, просто действие выполняется от лица администратора
@admin_router.get("/patients/{user_id}/dependents", response_model=list[PatientOut])
async def list_patient_dependents(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    user = await crud_user.get_by_id(user_id, db)

    if user is None:
        raise AppError(code="USER_NOT_FOUND", message="Пользователь не найден", status_code=404)

    return await crud_patient.get_dependents(user_id, db)


@admin_router.post("/patients/{user_id}/dependents", response_model=PatientOut)
async def add_patient_dependent(
    user_id: int,
    data: DependentCreateIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    user = await crud_user.get_by_id(user_id, db)

    if user is None:
        raise AppError(code="USER_NOT_FOUND", message="Пользователь не найден", status_code=404)

    if user.role != "patient":
        raise AppError(
            code="NOT_A_PATIENT",
            message="Родственников можно заводить только в аккаунте пациента",
            status_code=400,
        )

    if await crud_patient.count_dependents(user_id, db) >= crud_patient.DEPENDENTS_LIMIT:
        raise AppError(
            code="DEPENDENTS_LIMIT_REACHED",
            message=f"Больше {crud_patient.DEPENDENTS_LIMIT} родственников добавить нельзя",
            status_code=409,
        )

    return await crud_patient.create_dependent(user, data, db)


@admin_router.put("/doctors/{doctor_id}/dismiss", response_model=DoctorDismissOut)
async def dismiss_doctor(
    doctor_id: int,
    data: DoctorDismissIn,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    upcoming = await crud_doctor.count_upcoming_appointments(doctor_id, data.dismissed_at, db)

    # предупреждение перед увольнением: сначала показываем, сколько живых записей
    # попадает на закрываемые даты, и только по confirm=true применяем
    if upcoming and not data.confirm:
        raise AppError(
            code="DOCTOR_HAS_UPCOMING_APPOINTMENTS",
            message=(
                f"К врачу нельзя будет записаться с {data.dismissed_at:%d.%m.%Y}, "
                f"но на эти даты уже есть активных записей: {upcoming}. "
                "Отправьте confirm=true, если всё равно увольняем"
            ),
            status_code=409,
        )

    doctor = await crud_doctor.dismiss_doctor(doctor, data.dismissed_at, db)

    return DoctorDismissOut(
        id=doctor.id,
        full_name=doctor.full_name,
        dismissed_at=doctor.dismissed_at,
        upcoming_appointments=upcoming,
    )


@admin_router.delete("/doctors/{doctor_id}/dismiss", response_model=DoctorDismissOut)
async def restore_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    doctor = await crud_doctor.get_by_id(doctor_id, db)

    if doctor is None:
        raise AppError(code="DOCTOR_NOT_FOUND", message="Врач не найден", status_code=404)

    doctor = await crud_doctor.restore_doctor(doctor, db)
    return DoctorDismissOut(id=doctor.id, full_name=doctor.full_name, dismissed_at=None)
