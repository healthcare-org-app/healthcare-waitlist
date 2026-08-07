"""Kafka consumers for waitlist-service.

One handler per subscribed topic. Handlers are best-effort logging plus
audit — services override this file to implement real cross-domain behavior.
"""
from __future__ import annotations

import logging

from healthcare_common.audit import emit_audit

log = logging.getLogger("waitlist-service.consumers")


def register(svc) -> None:
    bus = svc.bus

    @bus.on("appointment.cancelled")
    def _on_appointment_cancelled(envelope: dict) -> None:
        log.info("waitlist-service: received appointment.cancelled id=%s", envelope.get("id"))
        emit_audit(bus, action="consume.appointment.cancelled", actor="system:waitlist-service",
                   target=None, details={"envelope_id": envelope.get("id")})

