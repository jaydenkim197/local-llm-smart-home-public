# Local Context-Aware Smart Home Controller

A local-first smart-home controller that combines speech, live environmental context,
and a lightweight LLM to produce validated device commands.

```text
Browser microphone or text
        -> faster-whisper STT
        -> Home Assistant state + local solar + cached weather context
        -> Ollama llama3.2:3b
        -> deterministic normalization, policy, and actuator allow-list
        -> Home Assistant
        -> Matter / Aqara Hub M3
        -> Zigbee curtain and IR air conditioner
```

The system was developed and physically demonstrated on a MacBook Air M1 with 8 GB
RAM. It also retains a simulation backend for development without the Home Assistant
VM or physical devices.

![Context-aware control dashboard](docs/assets/demo/context-aware-dashboard.png)

![Physical living-room curtain installation](docs/assets/demo/physical-living-room.jpg)

## Verified MVP

- English text and browser-microphone commands
- Local `faster-whisper` STT using `tiny.en`
- Local Ollama inference using `llama3.2:3b`
- Request-time Home Assistant snapshots for temperature, humidity, illuminance, and curtain position
- Local sunrise, sunset, solar position, and window alignment calculations
- Cached Open-Meteo weather and solar-radiation context with graceful offline behavior
- Context-aware no-op suppression and physical actuator allow-list
- Aqara curtain control through Home Assistant, Matter, and Hub M3
- Aqara M3 IR air-conditioner control through bounded Scene Sync commands

The filmed acceptance test verified microphone input through physical curtain and AC
operation. IR AC control is command-only: command acceptance must not be interpreted as
authoritative AC power, mode, or temperature feedback.

## Local Models

- LLM: `llama3.2:3b`
- STT: `faster-whisper` with `tiny.en`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Install Ollama, then pull the model:

```bash
ollama pull llama3.2:3b
```

Copy `.env.example` to `.env`. Keep coordinates, Home Assistant tokens, and entity IDs
only in `.env`; it is excluded from Git.

## Simulation Mode

Simulation is the default backend and does not require Home Assistant. Ollama is
optional because deterministic fallback parsing remains available.

```bash
./scripts/run.sh simulation
```

Open `http://127.0.0.1:8000`.

## Physical Mode

Set these local `.env` values before starting:

```text
CONTROL_BACKEND=home_assistant
HOME_ASSISTANT_URL=...
HOME_ASSISTANT_TOKEN=...
HOME_ASSISTANT_AC_COOL_ENTITY=...
HOME_ASSISTANT_AC_OFF_ENTITY=...
```

The verified logical mappings are:

```text
cover.living_room_curtain -> Aqara curtain cover entity
climate.air_conditioner   -> AC Off and AC Cool 24 Matter Scene Sync switches
```

Start Ollama, the Home Assistant VM, and then the application with
`./scripts/run.sh home_assistant`.
Physical mode rejects commands for unmapped virtual devices.

## API

- `POST /api/command/text`
- `POST /api/command/audio`
- `GET /api/devices`
- `POST /api/devices/reset`
- `GET /api/health`
- `GET /api/context`

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

The suite covers simulation API flows, context policy, Home Assistant request mapping,
IR scene semantics, solar calculations, and cached weather normalization.

## Documentation

- [Project documentation](docs/README.md)
- [Current architecture](docs/architecture/system_overview.md)
- [Final MVP report](docs/reports/2026-09-06-mvp-final-report.ko.md)
- [Portfolio summary](docs/portfolio/project-summary.ko.md)
- [Demo media catalog](docs/media/demo-evidence.md)

## Example Commands

- `I am going to watch a movie from now on.`
- `Turn everything on.`
- `Close the living room curtain.`
- `It's too hot in the living room. Make it comfortable.`
- `Turn off the air conditioner.`
- `What time is sunset today?`
