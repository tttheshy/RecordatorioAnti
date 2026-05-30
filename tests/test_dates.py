import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import (
    calcular_fecha_aplicacion,
    es_dia_habil,
    obtener_dias_recordatorio,
)


def test_es_dia_habil_lunes_a_viernes():
    assert es_dia_habil(date(2026, 5, 29)) is True


def test_es_dia_habil_fin_de_semana():
    assert es_dia_habil(date(2026, 5, 30)) is False
    assert es_dia_habil(date(2026, 5, 31)) is False


def test_calcular_fecha_aplicacion_prefiere_28_si_es_habil():
    assert calcular_fecha_aplicacion(2026, 5) == date(2026, 5, 28)


def test_calcular_fecha_aplicacion_mueve_sabado_al_viernes_anterior():
    assert calcular_fecha_aplicacion(2026, 2) == date(2026, 2, 27)


def test_calcular_fecha_aplicacion_mueve_domingo_al_viernes_anterior():
    assert calcular_fecha_aplicacion(2026, 6) == date(2026, 6, 26)


def test_calcular_fecha_aplicacion_permite_target_day_29():
    assert calcular_fecha_aplicacion(2026, 5, target_day=29) == date(2026, 5, 29)


def test_calcular_fecha_aplicacion_rechaza_target_day_invalido():
    with pytest.raises(ValueError):
        calcular_fecha_aplicacion(2026, 5, target_day=30)


def test_obtener_dias_recordatorio():
    fecha_aplicacion = date(2026, 5, 28)

    assert obtener_dias_recordatorio(fecha_aplicacion) == {
        7: date(2026, 5, 21),
        3: date(2026, 5, 25),
        1: date(2026, 5, 27),
        0: date(2026, 5, 28),
    }
