from datetime import date, timedelta


def _payload(**overrides):
    data = {
        "name": "Netflix",
        "price": 10,
        "currency": "USD",
        "billing_cycle": "monthly",
        "next_renewal": (date.today() + timedelta(days=5)).isoformat(),
    }
    data.update(overrides)
    return data


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"


def test_default_categories_exist(client):
    names = [c["name"] for c in client.get("/categories").json()]
    assert "Entertainment" in names and "Other" in names


def test_create_and_read_subscription(client):
    response = client.post("/subscriptions", json=_payload())
    assert response.status_code == 201
    sub = response.json()
    assert sub["name"] == "Netflix"
    assert sub["days_until_renewal"] == 5
    assert sub["base_currency"] == "PKR"
    # 10 USD at the fallback rate of 280 PKR per USD
    assert sub["monthly_cost"] == 2800.0
    assert sub["yearly_cost"] == 33600.0

    assert client.get(f"/subscriptions/{sub['id']}").json()["name"] == "Netflix"


def test_validation_errors(client):
    assert client.post("/subscriptions", json=_payload(price=-5)).status_code == 422
    assert client.post("/subscriptions", json=_payload(name="   ")).status_code == 422
    assert client.post("/subscriptions", json=_payload(currency="XXX")).status_code == 422
    assert client.post("/subscriptions", json=_payload(billing_cycle="daily")).status_code == 422
    assert client.post("/subscriptions", json=_payload(category_id=9999)).status_code == 400


def test_yearly_plan_monthly_cost(client):
    sub = client.post("/subscriptions", json=_payload(price=120, billing_cycle="yearly")).json()
    assert sub["monthly_cost"] == round(120 * 280 / 12, 2)


def test_past_renewal_rolls_forward(client):
    past = (date.today() - timedelta(days=40)).isoformat()
    sub = client.post("/subscriptions", json=_payload(next_renewal=past)).json()
    assert sub["days_until_renewal"] >= 0
    assert sub["days_until_renewal"] <= 31


def test_update_toggle_delete(client):
    sub = client.post("/subscriptions", json=_payload()).json()
    sub_id = sub["id"]

    updated = client.put(f"/subscriptions/{sub_id}", json={"price": 20, "name": "Netflix 4K"}).json()
    assert updated["price"] == 20 and updated["name"] == "Netflix 4K"

    paused = client.patch(f"/subscriptions/{sub_id}/toggle").json()
    assert paused["is_active"] is False
    assert client.patch(f"/subscriptions/{sub_id}/toggle").json()["is_active"] is True

    assert client.delete(f"/subscriptions/{sub_id}").status_code == 204
    assert client.get(f"/subscriptions/{sub_id}").status_code == 404
    assert client.delete(f"/subscriptions/{sub_id}").status_code == 404


def test_filters_and_sorting(client):
    client.post("/subscriptions", json=_payload(name="Alpha", price=5))
    client.post("/subscriptions", json=_payload(name="Beta", price=50))
    client.post("/subscriptions", json=_payload(name="Gamma", price=1, is_active=False))

    assert [s["name"] for s in client.get("/subscriptions?sort=price").json()][0] == "Beta"
    assert len(client.get("/subscriptions?status=active").json()) == 2
    assert len(client.get("/subscriptions?status=paused").json()) == 1
    assert [s["name"] for s in client.get("/subscriptions?search=alp").json()] == ["Alpha"]


def test_display_currency_switch(client):
    client.post("/subscriptions", json=_payload(price=10))
    usd = client.get("/subscriptions?base=USD").json()[0]
    assert usd["monthly_cost"] == 10.0
    assert client.get("/subscriptions?base=NOPE").status_code == 422


def test_category_creation_and_duplicates(client):
    created = client.post("/categories", json={"name": "Gaming", "color": "#22c55e"})
    assert created.status_code == 201
    assert client.post("/categories", json={"name": "gaming"}).status_code == 409


def test_dashboard_numbers(client):
    client.post("/subscriptions", json=_payload(name="A", price=10, next_renewal=(date.today() + timedelta(days=2)).isoformat()))
    far = (date.today() + timedelta(days=100)).isoformat()
    client.post("/subscriptions", json=_payload(name="B", price=120, billing_cycle="yearly", next_renewal=far))
    client.post("/subscriptions", json=_payload(name="C", price=99, is_active=False))

    data = client.get("/dashboard?base=USD").json()
    assert data["active_count"] == 2
    assert data["paused_count"] == 1
    assert data["monthly_total"] == 20.0  # 10 monthly + 120/12
    assert data["yearly_total"] == 240.0
    assert data["paused_monthly_savings"] == 99.0
    assert data["due_7_count"] == 1
    assert data["due_7_total"] == 10.0
    assert len(data["timeline"]) == 5
    assert data["top"][0]["name"] in {"A", "B"}
    assert data["insights"]


def test_empty_dashboard(client):
    data = client.get("/dashboard").json()
    assert data["monthly_total"] == 0
    assert data["active_count"] == 0
    assert data["upcoming"] == []


def test_csv_export(client):
    client.post("/subscriptions", json=_payload(name="Spotify, Duo"))
    response = client.get("/reports/export.csv?base=USD")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    text = response.content.decode("utf-8-sig")
    assert "Monthly cost (USD)" in text
    assert '"Spotify, Duo"' in text


def test_demo_seed_and_clear(client):
    assert client.post("/demo/seed").json()["added"] == 12
    assert client.post("/demo/seed").json()["added"] == 0  # only seeds an empty table
    assert client.delete("/demo/clear").json()["deleted"] == 12
    assert client.get("/subscriptions").json() == []


def test_unicode_names_are_stored(client):
    sub = client.post("/subscriptions", json=_payload(name="نیٹ فلکس", notes="خاندان کے ساتھ")).json()
    assert client.get(f"/subscriptions/{sub['id']}").json()["name"] == "نیٹ فلکس"
    assert client.post("/categories", json={"name": "کھیل"}).status_code == 201


def test_category_name_with_wildcards_is_not_a_pattern(client):
    assert client.post("/categories", json={"name": "100%"}).status_code == 201
    assert client.post("/categories", json={"name": "%"}).status_code == 201  # not treated as "match anything"
