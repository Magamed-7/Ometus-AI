from tests.test_appointments import (
    DOCTOR_APPOINTMENTS_URL,
    admin_headers,
    book,
    setup_doctor,
    setup_patient,
)

REVIEWS_URL = "/api/reviews"
ADMIN_REVIEWS_URL = "/api/admin/reviews"


async def completed_visit(client, db, patient_email="patient@ometus.test"):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(
        client, patient_email, first_name="Азиз", last_name="Мирзоев"
    )
    created = await book(client, headers, doctor_id)
    appointment_id = created.json()["id"]

    await client.put(
        f"{DOCTOR_APPOINTMENTS_URL}/{appointment_id}/complete", headers=doctor_headers
    )

    return appointment_id, doctor_id, headers


async def test_patient_leaves_a_review_after_the_visit(client, db):
    appointment_id, doctor_id, headers = await completed_visit(client, db)

    response = await client.post(
        REVIEWS_URL,
        json={"appointment_id": appointment_id, "rating": 5, "text": "Внимательный врач"},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["rating"] == 5
    assert body["doctor_id"] == doctor_id
    assert body["filial_name"] == "Ometus Центр"


async def test_author_is_shortened_to_a_first_name_and_an_initial(client, db):
    appointment_id, _, headers = await completed_visit(client, db)

    response = await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 5}, headers=headers
    )

    assert response.json()["author"] == "Азиз М."


async def test_review_before_the_visit_is_rejected(client, db):
    doctor_id, department_id, doctor_headers = await setup_doctor(client, db)
    patient_id, headers = await setup_patient(client)
    created = await book(client, headers, doctor_id)

    response = await client.post(
        REVIEWS_URL,
        json={"appointment_id": created.json()["id"], "rating": 5},
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "APPOINTMENT_NOT_COMPLETED"


async def test_second_review_of_the_same_visit_is_rejected(client, db):
    appointment_id, _, headers = await completed_visit(client, db)
    await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 5}, headers=headers
    )

    response = await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 1}, headers=headers
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REVIEW_ALREADY_LEFT"


async def test_patient_cannot_review_someone_elses_visit(client, db):
    appointment_id, _, _ = await completed_visit(client, db)
    _, stranger = await setup_patient(client, "stranger@ometus.test")

    response = await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 1}, headers=stranger
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "APPOINTMENT_NOT_FOUND"


async def test_rating_outside_one_to_five_is_rejected(client, db):
    appointment_id, _, headers = await completed_visit(client, db)

    response = await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 9}, headers=headers
    )

    assert response.status_code == 422


async def test_empty_list_reports_no_average(client, db):
    response = await client.get(REVIEWS_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["summary"]["average"] is None


async def test_summary_counts_the_average_and_the_breakdown(client, db):
    appointment_id, doctor_id, headers = await completed_visit(client, db)
    await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 4}, headers=headers
    )

    response = await client.get(REVIEWS_URL)

    summary = response.json()["summary"]
    assert summary["average"] == 4.0
    assert summary["total"] == 1
    assert summary["breakdown"]["4"] == 1


async def test_unpublished_review_disappears_from_the_public_list(client, db):
    appointment_id, _, headers = await completed_visit(client, db)
    created = await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 5}, headers=headers
    )
    admin = await admin_headers(client, db)

    await client.patch(
        f"{ADMIN_REVIEWS_URL}/{created.json()['id']}",
        json={"is_published": False},
        headers=admin,
    )

    public = await client.get(REVIEWS_URL)
    assert public.json()["items"] == []
    assert public.json()["summary"]["total"] == 0
    assert len((await client.get(ADMIN_REVIEWS_URL, headers=admin)).json()) == 1


async def test_reviews_filter_by_doctor(client, db):
    appointment_id, doctor_id, headers = await completed_visit(client, db)
    await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 5}, headers=headers
    )

    mine = await client.get(REVIEWS_URL, params={"doctor_id": doctor_id})
    other = await client.get(REVIEWS_URL, params={"doctor_id": doctor_id + 999})

    assert mine.json()["total"] == 1
    assert other.json()["total"] == 0


async def test_admin_deletes_a_review(client, db):
    appointment_id, _, headers = await completed_visit(client, db)
    created = await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 5}, headers=headers
    )
    admin = await admin_headers(client, db)

    response = await client.delete(
        f"{ADMIN_REVIEWS_URL}/{created.json()['id']}", headers=admin
    )

    assert response.status_code == 200
    assert (await client.get(REVIEWS_URL)).json()["total"] == 0


MY_REVIEWS_URL = "/api/reviews/mine"


async def test_patient_sees_own_reviews_with_appointment_id(client, db):
    appointment_id, _, headers = await completed_visit(client, db)

    await client.post(
        REVIEWS_URL,
        json={"appointment_id": appointment_id, "rating": 5, "text": "Спасибо"},
        headers=headers,
    )

    response = await client.get(MY_REVIEWS_URL, headers=headers)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["appointment_id"] == appointment_id
    assert rows[0]["rating"] == 5
    assert rows[0]["is_published"] is True


async def test_patient_does_not_see_reviews_of_other_patients(client, db):
    appointment_id, _, headers = await completed_visit(client, db)
    await client.post(
        REVIEWS_URL, json={"appointment_id": appointment_id, "rating": 4}, headers=headers
    )

    _, stranger = await setup_patient(client, "stranger@ometus.test")

    response = await client.get(MY_REVIEWS_URL, headers=stranger)

    assert response.status_code == 200
    assert response.json() == []


async def test_my_reviews_require_a_patient(client, db):
    response = await client.get(MY_REVIEWS_URL)

    assert response.status_code == 401
