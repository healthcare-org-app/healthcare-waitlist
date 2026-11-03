from app.routes import RESOURCE


def test_crud(client, svc):
    r = client.post(f"/api/{RESOURCE}/", json={"name": "test"})
    assert r.status_code == 201, r.data
    rid = r.get_json()["id"]

    r = client.get(f"/api/{RESOURCE}/{rid}")
    assert r.status_code == 200

    r = client.patch(f"/api/{RESOURCE}/{rid}", json={"name": "updated"})
    assert r.status_code == 200
    assert r.get_json()["name"] == "updated"

    r = client.delete(f"/api/{RESOURCE}/{rid}")
    assert r.status_code == 200

    r = client.get(f"/api/{RESOURCE}/")
    body = r.get_json()
    assert body["count"] >= 1


def test_get_missing(client):
    r = client.get(f"/api/{RESOURCE}/999999")
    assert r.status_code == 404


def test_audit_emitted_on_create(client, svc):
    client.post(f"/api/{RESOURCE}/", json={"name": "audit-me"})
    topics = [t for t, _, _ in svc.bus.published]
    assert "audit.event" in topics


class _FakeResp:
    def __init__(self, status_code, body):
        self.status_code, self._body, self.text = status_code, body, str(body)

    def json(self):
        return self._body


class _FakeAppointments:
    def __init__(self, resp=None, exc=None):
        self.resp, self.exc, self.calls = resp, exc, []

    def post(self, path, json=None, **kw):
        self.calls.append((path, kw.get("headers")))
        if self.exc:
            raise self.exc
        return self.resp


def _entry(client, **data):
    return client.post(f"/api/{RESOURCE}/", json=data).get_json()["id"]


def test_arrive_checks_in_the_appointment(client, svc):
    svc.clients["appointments-service"] = _FakeAppointments(
        _FakeResp(200, {"id": 2001, "status": "checked-in"}))
    rid = _entry(client, appointment_id=2001, patient_id=1001)
    r = client.post(f"/api/{RESOURCE}/{rid}/arrive", headers={"Authorization": "Bearer t"})
    assert r.status_code == 200, r.data
    assert r.get_json()["appointment"]["status"] == "checked-in"
    assert svc.clients["appointments-service"].calls == [
        ("/api/appointments/2001/check-in", {"Authorization": "Bearer t"})]
    assert "audit.event" in [t for t, _, _ in svc.bus.published]


def test_arrive_passes_a_refusal_through(client, svc):
    svc.clients["appointments-service"] = _FakeAppointments(
        _FakeResp(409, {"error": {"code": "eligibility_denied"}}))
    rid = _entry(client, appointment_id=2002, patient_id=1002)
    r = client.post(f"/api/{RESOURCE}/{rid}/arrive")
    assert r.status_code == 409
    assert r.get_json()["upstream"]["error"]["code"] == "eligibility_denied"


def test_arrive_needs_an_appointment(client):
    rid = _entry(client, patient_id=1001)
    assert client.post(f"/api/{RESOURCE}/{rid}/arrive").status_code == 422


def test_arrive_when_appointments_service_is_down(client, svc):
    from healthcare_common.http import ServiceUnavailable
    svc.clients["appointments-service"] = _FakeAppointments(exc=ServiceUnavailable("down"))
    rid = _entry(client, appointment_id=2001, patient_id=1001)
    assert client.post(f"/api/{RESOURCE}/{rid}/arrive").status_code == 503
