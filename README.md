# Recordatorios WhatsApp CESFAM

Sistema automatico en Python para enviar recordatorios por WhatsApp sobre la aplicacion mensual de anticonceptivo en CESFAM.

## Reglas implementadas

- Usa zona horaria `America/Santiago`.
- Prefiere el dia 28 de cada mes.
- Si la fecha configurada cae sabado o domingo, mueve la aplicacion al dia habil anterior.
- Permite configurar `TARGET_DAY` con `27`, `28` o `29`.
- Envia recordatorios 7 dias antes, 3 dias antes, 1 dia antes y el mismo dia.
- Evita duplicados usando `data/sent_reminders.json`, persistido por GitHub Actions.

## Archivos

- `main.py`: logica principal y envio por Twilio.
- `config.py`: lectura de configuracion desde variables de entorno.
- `.github/workflows/reminder.yml`: workflow diario de GitHub Actions.
- `tests/test_dates.py`: pruebas de calculo de fechas.
- `requirements.txt`: dependencias.

## Configuracion local

Instala dependencias:

```bash
pip install -r requirements.txt
```

Configura variables de entorno:

```bash
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export WHATSAPP_FROM="whatsapp:+14155238886"
export WHATSAPP_TO_NUMBERS="whatsapp:+56911111111,whatsapp:+56922222222"
export TARGET_DAY="28"
export TIMEZONE="America/Santiago"
```

En Windows PowerShell:

```powershell
$env:TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:TWILIO_AUTH_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:WHATSAPP_FROM="whatsapp:+14155238886"
$env:WHATSAPP_TO_NUMBERS="whatsapp:+56911111111,whatsapp:+56922222222"
$env:TARGET_DAY="28"
$env:TIMEZONE="America/Santiago"
```

Probar sin enviar mensajes:

```bash
python main.py --dry-run
```

Ejecutar pruebas:

```bash
pytest
```

## GitHub Secrets

En GitHub, crea estos secrets en `Settings > Secrets and variables > Actions > Secrets`:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `WHATSAPP_FROM`
- `WHATSAPP_TO_NUMBERS`

Formato recomendado:

- `WHATSAPP_FROM`: `whatsapp:+14155238886` para sandbox de Twilio, o tu numero aprobado de WhatsApp Business.
- `WHATSAPP_TO_NUMBERS`: dos numeros separados por coma, por ejemplo `whatsapp:+56911111111,whatsapp:+56922222222`.

Opcionalmente crea una variable de repositorio en `Settings > Secrets and variables > Actions > Variables`:

- `TARGET_DAY`: `27`, `28` o `29`. Si no existe, se usa `28`.

## GitHub Actions

El workflow corre diariamente con cron:

```yaml
0 12 * * *
```

El script decide si ese dia corresponde enviar una alerta. Si no corresponde, termina sin enviar mensajes.

Para evitar duplicados, el workflow guarda los envios realizados en `data/sent_reminders.json` y lo confirma al repositorio. El archivo no contiene numeros telefonicos en claro; guarda hashes SHA-256 de los destinatarios.

## Twilio WhatsApp

Para pruebas con Twilio Sandbox:

1. Activa el sandbox de WhatsApp en Twilio.
2. Une cada telefono destinatario al sandbox siguiendo la instruccion de Twilio.
3. Usa `WHATSAPP_FROM=whatsapp:+14155238886`, salvo que Twilio indique otro remitente.

Para produccion necesitas un remitente de WhatsApp aprobado por Twilio/Meta.
