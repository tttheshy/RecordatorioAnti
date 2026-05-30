import os
from dataclasses import dataclass
from pathlib import Path


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta configurar la variable de entorno {name}")
    return value


def _parse_target_day() -> int:
    raw_value = os.getenv("TARGET_DAY", "28")
    try:
        target_day = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("TARGET_DAY debe ser 27, 28 o 29") from exc

    if target_day not in {27, 28, 29}:
        raise RuntimeError("TARGET_DAY debe ser 27, 28 o 29")

    return target_day


def _normalize_whatsapp_number(number: str, env_name: str) -> str:
    normalized = number.strip().replace(" ", "")
    if normalized.startswith("whatsapp:"):
        normalized = normalized.removeprefix("whatsapp:")

    if not normalized.startswith("+"):
        raise RuntimeError(
            f"{env_name} debe usar formato internacional, por ejemplo whatsapp:+56912345678"
        )

    return f"whatsapp:{normalized}"


def _parse_recipients() -> list[str]:
    raw_value = _get_required_env("WHATSAPP_TO_NUMBERS")
    recipients = [
        _normalize_whatsapp_number(number, "WHATSAPP_TO_NUMBERS")
        for number in raw_value.split(",")
        if number.strip()
    ]
    if not recipients:
        raise RuntimeError("WHATSAPP_TO_NUMBERS debe incluir al menos un numero")
    return recipients


@dataclass(frozen=True)
class Settings:
    twilio_account_sid: str
    twilio_auth_token: str
    whatsapp_from: str
    whatsapp_to_numbers: list[str]
    target_day: int
    timezone: str
    sent_log_path: Path


def get_settings() -> Settings:
    return Settings(
        twilio_account_sid=_get_required_env("TWILIO_ACCOUNT_SID"),
        twilio_auth_token=_get_required_env("TWILIO_AUTH_TOKEN"),
        whatsapp_from=_normalize_whatsapp_number(
            _get_required_env("WHATSAPP_FROM"),
            "WHATSAPP_FROM",
        ),
        whatsapp_to_numbers=_parse_recipients(),
        target_day=_parse_target_day(),
        timezone=os.getenv("TIMEZONE", "America/Santiago"),
        sent_log_path=Path(os.getenv("SENT_LOG_PATH", "data/sent_reminders.json")),
    )
