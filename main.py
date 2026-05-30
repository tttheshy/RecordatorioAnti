from __future__ import annotations

import argparse
import hashlib
import json
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from config import Settings, get_settings


REMINDER_DAYS = (7, 3, 1, 0)


def es_dia_habil(fecha: date) -> bool:
    """Retorna True si la fecha cae entre lunes y viernes."""
    return fecha.weekday() < 5


def calcular_fecha_aplicacion(year: int, month: int, target_day: int = 28) -> date:
    """
    Calcula la fecha habil recomendada para la aplicacion mensual.

    Por defecto usa el dia 28. Si cae sabado o domingo, retrocede al dia habil
    anterior. TARGET_DAY permite elegir 27, 28 o 29.
    """
    if target_day not in {27, 28, 29}:
        raise ValueError("target_day debe ser 27, 28 o 29")

    last_day = monthrange(year, month)[1]
    candidate = date(year, month, min(target_day, last_day))

    while not es_dia_habil(candidate):
        candidate -= timedelta(days=1)

    return candidate


def obtener_dias_recordatorio(fecha_aplicacion: date) -> dict[int, date]:
    """Devuelve las fechas de recordatorio indexadas por dias restantes."""
    return {
        days_before: fecha_aplicacion - timedelta(days=days_before)
        for days_before in REMINDER_DAYS
    }


def _format_days_left(days_left: int) -> str:
    if days_left == 0:
        return "hoy es el dia recomendado"
    if days_left == 1:
        return "falta 1 dia"
    return f"faltan {days_left} dias"


def _build_message(fecha_aplicacion: date, days_left: int) -> str:
    return (
        "Recordatorio CESFAM: la fecha recomendada para la aplicacion mensual "
        f"del anticonceptivo es {fecha_aplicacion.strftime('%d-%m-%Y')}. "
        f"{_format_days_left(days_left)}. "
        "Por favor confirma o asiste al CESFAM."
    )


def _build_test_message(now: datetime) -> str:
    return (
        "Prueba de recordatorio CESFAM: el sistema automatico de WhatsApp "
        f"esta funcionando correctamente. Fecha de prueba: "
        f"{now.strftime('%d-%m-%Y %H:%M')}."
    )


def _load_sent_log(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise RuntimeError(f"El registro de envios {path} no tiene formato valido")

    return {str(key): list(value) for key, value in data.items()}


def _save_sent_log(path: Path, sent_log: dict[str, list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(sent_log, file, ensure_ascii=True, indent=2, sort_keys=True)
        file.write("\n")


def _recipient_hash(recipient: str) -> str:
    return hashlib.sha256(recipient.encode("utf-8")).hexdigest()


def _sent_key(today: date, fecha_aplicacion: date, days_left: int) -> str:
    return f"{today.isoformat()}|{fecha_aplicacion.isoformat()}|{days_left}"


def enviar_whatsapp(
    client: Any,
    from_number: str,
    to_number: str,
    message: str,
    dry_run: bool = False,
) -> str:
    """Envia un mensaje por WhatsApp usando Twilio."""
    if dry_run:
        print(f"[DRY RUN] WhatsApp a {to_number}: {message}")
        return "dry-run"

    sent_message = client.messages.create(
        from_=from_number,
        body=message,
        to=to_number,
    )
    return sent_message.sid


def _find_current_reminder(today: date, target_day: int) -> tuple[date, int] | None:
    current_month_application = calcular_fecha_aplicacion(
        today.year,
        today.month,
        target_day,
    )
    reminder_days = obtener_dias_recordatorio(current_month_application)

    for days_left, reminder_date in reminder_days.items():
        if today == reminder_date:
            return current_month_application, days_left

    return None


def send_test_message(settings: Settings, dry_run: bool = False) -> int:
    zone = ZoneInfo(settings.timezone)
    now = datetime.now(zone)
    message = _build_test_message(now)
    from twilio.rest import Client

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    for recipient in settings.whatsapp_to_numbers:
        sid = enviar_whatsapp(
            client=client,
            from_number=settings.whatsapp_from,
            to_number=recipient,
            message=message,
            dry_run=dry_run,
        )
        print(f"Mensaje de prueba enviado a {recipient}. SID: {sid}")

    return 0


def run(settings: Settings, today: date | None = None, dry_run: bool = False) -> int:
    zone = ZoneInfo(settings.timezone)
    today = today or datetime.now(zone).date()

    reminder = _find_current_reminder(today, settings.target_day)
    if reminder is None:
        print(f"No hay recordatorios programados para {today.isoformat()}.")
        return 0

    fecha_aplicacion, days_left = reminder
    message = _build_message(fecha_aplicacion, days_left)
    sent_log = _load_sent_log(settings.sent_log_path)
    key = _sent_key(today, fecha_aplicacion, days_left)
    already_sent = set(sent_log.get(key, []))
    from twilio.rest import Client

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    sent_any = False

    for recipient in settings.whatsapp_to_numbers:
        recipient_id = _recipient_hash(recipient)
        if recipient_id in already_sent:
            print(f"Envio omitido para {recipient}: ya existe registro para hoy.")
            continue

        sid = enviar_whatsapp(
            client=client,
            from_number=settings.whatsapp_from,
            to_number=recipient,
            message=message,
            dry_run=dry_run,
        )
        print(f"Recordatorio enviado a {recipient}. SID: {sid}")
        already_sent.add(recipient_id)
        sent_any = True

    sent_log[key] = sorted(already_sent)
    _save_sent_log(settings.sent_log_path, sent_log)

    if not sent_any:
        print("No se enviaron mensajes nuevos.")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recordatorios WhatsApp CESFAM")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra los mensajes sin enviarlos por Twilio",
    )
    parser.add_argument(
        "--test-now",
        action="store_true",
        help="Envia un mensaje de prueba inmediatamente",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.test_now:
        raise SystemExit(send_test_message(get_settings(), dry_run=args.dry_run))
    raise SystemExit(run(get_settings(), dry_run=args.dry_run))
