from tests.test_appointments import admin_headers, auth_headers, register

SERVICES_URL = "/api/services"
ADMIN_SERVICES_URL = "/api/admin/services"

SERVICE_DATA = {
    "name": "Приём терапевта (первичный)",
    "description": "Осмотр, сбор анамнеза, постановка предварительного диагноза.",
    "category": "consultation",
    "price": "150.00",
    "duration_minutes": 20,
}


async def test_admin_creates_a_service(client, db):
    admin = await admin_headers(client, db)

    response = await client.post(ADMIN_SERVICES_URL, json=SERVICE_DATA, headers=admin)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == SERVICE_DATA["name"]
    assert body["price"] == "150.00"
    assert body["currency"] == "TJS"
    assert body["is_active"] is True


async def test_public_sees_active_services_without_login(client, db):
    admin = await admin_headers(client, db)
    await client.post(ADMIN_SERVICES_URL, json=SERVICE_DATA, headers=admin)

    response = await client.get(SERVICES_URL)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == [SERVICE_DATA["name"]]


async def test_hidden_service_drops_out_of_the_public_list(client, db):
    admin = await admin_headers(client, db)
    created = await client.post(ADMIN_SERVICES_URL, json=SERVICE_DATA, headers=admin)
    service_id = created.json()["id"]

    await client.patch(
        f"{ADMIN_SERVICES_URL}/{service_id}", json={"is_active": False}, headers=admin
    )

    assert await client.get(SERVICES_URL) is not None
    assert (await client.get(SERVICES_URL)).json() == []
    assert (await client.get(f"{SERVICES_URL}/{service_id}")).status_code == 404
    assert len((await client.get(ADMIN_SERVICES_URL, headers=admin)).json()) == 1


async def test_price_keeps_two_decimals(client, db):
    admin = await admin_headers(client, db)

    response = await client.post(
        ADMIN_SERVICES_URL, json={**SERVICE_DATA, "price": "99.90"}, headers=admin
    )

    assert response.json()["price"] == "99.90"


async def test_services_filter_by_category_and_search(client, db):
    admin = await admin_headers(client, db)
    await client.post(ADMIN_SERVICES_URL, json=SERVICE_DATA, headers=admin)
    await client.post(
        ADMIN_SERVICES_URL,
        json={
            "name": "УЗИ органов брюшной полости",
            "category": "diagnostics",
            "price": "180.00",
        },
        headers=admin,
    )

    by_category = await client.get(SERVICES_URL, params={"category": "diagnostics"})
    by_search = await client.get(SERVICES_URL, params={"search": "терапевт"})

    assert [item["name"] for item in by_category.json()] == ["УЗИ органов брюшной полости"]
    assert [item["name"] for item in by_search.json()] == [SERVICE_DATA["name"]]


async def test_duplicate_service_name_is_rejected(client, db):
    admin = await admin_headers(client, db)
    await client.post(ADMIN_SERVICES_URL, json=SERVICE_DATA, headers=admin)

    response = await client.post(ADMIN_SERVICES_URL, json=SERVICE_DATA, headers=admin)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SERVICE_ALREADY_EXISTS"


async def test_unknown_category_is_rejected(client, db):
    admin = await admin_headers(client, db)

    response = await client.post(
        ADMIN_SERVICES_URL, json={**SERVICE_DATA, "category": "магия"}, headers=admin
    )

    assert response.status_code == 422


async def test_patient_cannot_touch_the_price_list(client, db):
    await register(client, "patient.services@ometus.test")
    headers = await auth_headers(client, "patient.services@ometus.test")

    response = await client.post(ADMIN_SERVICES_URL, json=SERVICE_DATA, headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_admin_deletes_a_service(client, db):
    admin = await admin_headers(client, db)
    created = await client.post(ADMIN_SERVICES_URL, json=SERVICE_DATA, headers=admin)

    response = await client.delete(
        f"{ADMIN_SERVICES_URL}/{created.json()['id']}", headers=admin
    )

    assert response.status_code == 200
    assert (await client.get(SERVICES_URL)).json() == []
