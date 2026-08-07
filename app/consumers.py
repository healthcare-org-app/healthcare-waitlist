"""Kafka consumers for waitlist-service.

One handler per subscribed topic. Real handlers write to this service's own
database and/or publish follow-up events; stub handlers just log + audit.
"""
from __future__ import annotations

import logging

from psycopg.types.json import Json

from healthcare_common.audit import emit_audit

log = logging.getLogger("waitlist-service.consumers")

TABLE = "waitlist"


def register(svc) -> None:
    bus = svc.bus
    db = svc.db
    clients = svc.clients

    @bus.on("appointment.cancelled")
    def _on_appointment_cancelled(envelope: dict) -> None:
        data = envelope.get("data") or {}
        try:
                    # Try to fill the slot from the waitlist. (Best-effort — no locking here.)
                    candidate = db.query_one(
                        f"SELECT * FROM {TABLE} WHERE status='waiting' ORDER BY id LIMIT 1"
                    )
                    if candidate:
                        db.execute(f"UPDATE {TABLE} SET status='offered', updated_at=now() WHERE id=%s",
                                   (candidate["id"],))
                        bus.publish("notification.requested", key=str(candidate["data"].get("patient_id")),
                                    value={"patient_id": candidate["data"].get("patient_id"),
                                           "subject": "Appointment slot opened for you",
                                           "source": "waitlist.offer"})
        except Exception as e:
            log.exception("waitlist-service/appointment.cancelled handler failed: %s", e)
        emit_audit(bus, action="consume.appointment.cancelled", actor="system:waitlist-service",
                   target=None, details={"envelope_id": envelope.get("id")})

