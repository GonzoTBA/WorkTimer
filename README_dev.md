# WorkTimer Dev Notes

Este fichero sirve como contexto rapido para retomar el proyecto en nuevos hilos sin tener que rediscover todo desde cero.

## Resumen del proyecto

- App de escritorio en Python con `PySide6`.
- Es una utilidad de barra/tray para lanzar un temporizador de pausas.
- La UI principal es una ventana compacta flotante y sin marco.
- Cuando el temporizador termina, muestra un dialogo modal y una notificacion del tray.

## Entorno de desarrollo

- Directorio del proyecto: `/Users/javier/Programming/WorkTimer`
- Rama habitual vista hasta ahora: `master`
- Python del proyecto: `.venv/bin/python`
- Version comprobada: `Python 3.10.16`
- Dependencia declarada actualmente en `requirements.txt`:
  - `PySide6==6.11.0`

## Arranque rapido

Activar entorno virtual:

```bash
source .venv/bin/activate
```

Ejecutar la app:

```bash
python main.py
```

Sin activar la venv:

```bash
./.venv/bin/python main.py
```

## Problema conocido importante

- Si se ejecuta con el `python3` global del sistema en vez de la `.venv`, aparece:
  - `ModuleNotFoundError: No module named 'PySide6'`
- Antes de asumir que falta una dependencia, comprobar siempre si el comando se esta ejecutando con `./.venv/bin/python`.

## Mapa rapido de archivos

- `main.py`
  - Punto de entrada.
  - Crea `QApplication`, valida que exista system tray y arranca `PauseTimerTrayApp`.

- `tray_app.py`
  - Contiene casi toda la UI.
  - `BreakReminderDialog`: dialogo final que aparece al terminar el temporizador.
  - `TimerWindow`: ventana principal compacta con presets, duracion, mensaje y controles.
  - `PauseTimerTrayApp`: integra tray icon, refresco por `QTimer`, posicionamiento de la ventana y notificaciones.

- `timer_model.py`
  - Logica del temporizador separada de la UI.
  - Estados: `IDLE`, `RUNNING`, `PAUSED`, `FINISHED`.
  - Usa `time.monotonic()` para medir el tiempo de forma robusta.

- `settings_manager.py`
  - Persistencia con `QSettings`.
  - Guarda ultima duracion y mensaje final.

- `resources/tray_icon.svg`
  - Icono del tray.

- `requirements.txt`
  - Dependencias Python reproducibles del proyecto.

## Flujo de la app

1. `main.py` crea la aplicacion Qt.
2. Se comprueba que el system tray este disponible.
3. `PauseTimerTrayApp` crea:
   - `SettingsManager`
   - `TimerModel`
   - `TimerWindow`
   - `BreakReminderDialog`
   - un `QTimer` de refresco cada 250 ms
4. Al pulsar Start, el modelo pasa a `RUNNING`.
5. En cada tick, `_on_refresh_tick()` actualiza la UI.
6. Cuando `model.tick()` detecta fin:
   - cambia a `FINISHED`
   - recupera y guarda el mensaje final
   - muestra el dialogo de pausa
   - lanza una notificacion del tray

## Comportamientos a preservar

- La duracion solo debe ser editable en `IDLE` o `FINISHED`.
- Los presets deben sincronizarse con el valor del `QSpinBox`.
- El mensaje final debe persistirse con `QSettings`.
- El temporizador debe seguir basado en `time.monotonic()`, no en tiempo de pared.
- La ventana debe posicionarse cerca del tray si la geometria del icono esta disponible.
- Si falta el icono SVG, la app cae a un icono estandar de Qt.

## Detalles de UI actuales

- Texto visible principalmente en espanol.
- Estetica oscura.
- Ventana principal:
  - sin marco
  - flotante
  - siempre encima
- Dialogo final:
  - modal
  - centrado en la pantalla resuelta desde el tray/cursor

## Verificaciones utiles al tocar el proyecto

Comprobar imports:

```bash
./.venv/bin/python -c "import main; print('main import OK')"
```

Comprobar que `PySide6` esta instalada en la venv:

```bash
./.venv/bin/python -m pip show PySide6
```

## Limitaciones actuales

- No hay suite de tests automatizados en el repo por ahora.
- No hay `pyproject.toml`.
- No hay `requirements-dev.txt`.
- No hay script de arranque dedicado.

## Convenciones practicas para futuros cambios

- Antes de editar, revisar si hay cambios locales con `git status --short`.
- No asumir que el problema es de codigo si el error puede venir de no usar la `.venv`.
- Si se toca la logica del temporizador, revisar tambien la habilitacion/deshabilitacion de botones en `TimerWindow.refresh_ui()`.
- Si se toca persistencia, revisar los nombres de clave de `QSettings` para no romper compatibilidad.
- Si se cambia el copy en espanol, mantener consistencia con el resto de la UI.

## Ultimo contexto observado

- Ultimo commit visto: `1acf06b Add break reminder dialog`
- Estado del repo al crear este fichero: sin cambios locales aparte de la documentacion anadida en sesiones recientes.
