from __future__ import annotations

import re

from .models import (
    Cause,
    Confidence,
    DiagnosticRequest,
    DiagnosticResponse,
    Difficulty,
    SafeStep,
    SelfServiceProbability,
    StopSignal,
)

DATA_RISK_PATTERNS = re.compile(
    r"bitlocker|recovery key|smart|s\.m\.a\.r\.t|clicking|ruido|clic|partition|partici[oó]n|"
    r"format|formatear|diskpart|chkdsk|blue screen|bsod|pantalla azul|ransom|malware|encrypt|"
    r"no boot|no arranca|boot device|kernel panic|nvme|ssd|hdd",
    re.IGNORECASE,
)

NETWORK_PATTERNS = re.compile(
    r"wifi|wi-fi|internet|dns|proxy|ipconfig|network|red|conexi[oó]n|browser|navegador",
    re.IGNORECASE,
)

PRINTER_PATTERNS = re.compile(r"printer|impresora|spooler|cola de impresi[oó]n|print", re.IGNORECASE)
UPDATE_PATTERNS = re.compile(r"update|actualizaci[oó]n|windows update|driver|controlador", re.IGNORECASE)


def build_rule_based_diagnostic(request: DiagnosticRequest, provider: str = "mock") -> DiagnosticResponse:
    text = request.issue_text
    locale = request.locale
    labels = _labels(locale)
    os_label = _os_label(request)

    difficulty = Difficulty.intermediate
    probability = SelfServiceProbability.medium
    causes: list[Cause] = []
    steps: list[SafeStep] = []
    stop: list[StopSignal] = []

    if DATA_RISK_PATTERNS.search(text):
        difficulty = Difficulty.data_risk
        probability = SelfServiceProbability.low
        causes.append(
            Cause(
                title=labels["possible_disk_or_boot"],
                explanation=labels["possible_disk_or_boot_detail"],
                confidence=Confidence.medium,
            )
        )
        steps.extend(
            [
                SafeStep(title=labels["backup_first"], detail=labels["backup_first_detail"], risk=Difficulty.data_risk),
                SafeStep(title=labels["avoid_destructive"], detail=labels["avoid_destructive_detail"], risk=Difficulty.data_risk),
            ]
        )
        stop.append(StopSignal(title=labels["stop_data"], detail=labels["stop_data_detail"]))
    elif NETWORK_PATTERNS.search(text):
        difficulty = Difficulty.basic
        probability = SelfServiceProbability.high
        causes.append(
            Cause(
                title=labels["network_config"],
                explanation=labels["network_config_detail"],
                confidence=Confidence.medium,
            )
        )
        steps.extend(
            [
                SafeStep(title=labels["restart_router"], detail=labels["restart_router_detail"]),
                SafeStep(title=labels["test_other_site"], detail=labels["test_other_site_detail"]),
                SafeStep(title=labels["dns_flush"], detail=labels["dns_flush_detail"]),
            ]
        )
    elif PRINTER_PATTERNS.search(text):
        difficulty = Difficulty.intermediate
        probability = SelfServiceProbability.medium
        causes.append(
            Cause(
                title=labels["printer_queue"],
                explanation=labels["printer_queue_detail"],
                confidence=Confidence.medium,
            )
        )
        steps.extend(
            [
                SafeStep(title=labels["check_printer"], detail=labels["check_printer_detail"]),
                SafeStep(title=labels["restart_spooler"], detail=labels["restart_spooler_detail"], risk=Difficulty.intermediate),
            ]
        )
    elif UPDATE_PATTERNS.search(text):
        difficulty = Difficulty.intermediate
        probability = SelfServiceProbability.medium
        causes.append(
            Cause(
                title=labels["driver_update"],
                explanation=labels["driver_update_detail"],
                confidence=Confidence.medium,
            )
        )
        steps.extend(
            [
                SafeStep(title=labels["create_restore"], detail=labels["create_restore_detail"], risk=Difficulty.intermediate),
                SafeStep(title=labels["install_updates"], detail=labels["install_updates_detail"], risk=Difficulty.intermediate),
            ]
        )
    else:
        difficulty = Difficulty.intermediate
        probability = SelfServiceProbability.medium
        causes.append(
            Cause(
                title=labels["generic_config"],
                explanation=labels["generic_config_detail"],
                confidence=Confidence.low,
            )
        )
        steps.extend(
            [
                SafeStep(title=labels["note_error"], detail=labels["note_error_detail"]),
                SafeStep(title=labels["restart_safe"], detail=labels["restart_safe_detail"]),
                SafeStep(title=labels["check_recent_changes"], detail=labels["check_recent_changes_detail"]),
            ]
        )

    if request.image_provided:
        causes.append(
            Cause(
                title=labels["image_context"],
                explanation=labels["image_context_detail"],
                confidence=Confidence.low,
            )
        )

    stop.extend(
        [
            StopSignal(title=labels["stop_bitlocker"], detail=labels["stop_bitlocker_detail"]),
            StopSignal(title=labels["stop_repeat"], detail=labels["stop_repeat_detail"]),
        ]
    )

    before_touching = [
        labels["before_backup"],
        labels["before_photos"],
        labels["before_power"],
        labels["before_no_delete"],
    ]

    summary = labels["summary"].format(os=os_label)
    whatsapp = labels["whatsapp"].format(os=os_label, difficulty=labels[difficulty.value], issue=_shorten(text, 260))

    return DiagnosticResponse(
        summary=summary,
        likely_causes=causes[:5],
        difficulty=difficulty,
        self_service_probability=probability,
        risk_notice=_risk_notice(locale, difficulty),
        before_touching=before_touching,
        safe_steps=steps[:8],
        stop_and_contact=stop[:6],
        customer_message=labels["customer_message"],
        whatsapp_prefill=whatsapp,
        disclaimer=labels["disclaimer"],
        model_provider=provider,
    )


def _shorten(value: str, limit: int) -> str:
    one_line = " ".join(value.split())
    return one_line if len(one_line) <= limit else f"{one_line[: limit - 1]}…"


def _os_label(request: DiagnosticRequest) -> str:
    mapping = {
        "windows_10": "Windows 10",
        "windows_11": "Windows 11",
        "macos": "macOS",
        "linux_ubuntu": "Ubuntu Linux",
        "linux_debian": "Debian Linux",
        "linux_fedora": "Fedora Linux",
        "linux_mint": "Linux Mint",
        "linux_arch": "Arch Linux",
        "linux_other": request.linux_distribution or "Linux",
    }
    return mapping.get(request.operating_system.value, request.operating_system.value)


def _risk_notice(locale: str, difficulty: Difficulty) -> str:
    if locale == "en":
        notices = {
            Difficulty.basic: "This looks safe for a basic user if the steps are followed slowly.",
            Difficulty.intermediate: "Proceed carefully. Stop if a step asks you to delete data, format a drive, or change partitions.",
            Difficulty.advanced: "Advanced case. A wrong action can worsen the problem; professional support is recommended.",
            Difficulty.data_risk: "Data-risk case. Do not format, reinstall, run diskpart, or force repairs before backing up important files.",
        }
    else:
        notices = {
            Difficulty.basic: "Parece seguro para un usuario básico si sigue los pasos con calma.",
            Difficulty.intermediate: "Procede con cuidado. Detente si un paso pide borrar datos, formatear o tocar particiones.",
            Difficulty.advanced: "Caso avanzado. Una acción incorrecta puede empeorar el problema; se recomienda soporte profesional.",
            Difficulty.data_risk: "Caso con riesgo de datos. No formatees, reinstales, uses diskpart ni fuerces reparaciones antes de respaldar archivos importantes.",
        }
    return notices[difficulty]


def _labels(locale: str) -> dict[str, str]:
    if locale == "en":
        return {
            "basic": "Basic",
            "intermediate": "Intermediate",
            "advanced": "Advanced",
            "data_risk": "Data risk",
            "summary": "Initial triage for {os}. This is guidance, not a guaranteed repair.",
            "possible_disk_or_boot": "Possible disk, boot, encryption, or data-risk issue",
            "possible_disk_or_boot_detail": "The message includes signs commonly linked to storage, boot, partition, malware, or data integrity problems.",
            "network_config": "Possible network, DNS, or router configuration issue",
            "network_config_detail": "The symptoms mention connectivity or browsing failures that are often caused by DNS, Wi-Fi, proxy, or router state.",
            "printer_queue": "Possible printer queue, driver, or spooler issue",
            "printer_queue_detail": "Printer errors are often caused by stuck jobs, offline devices, damaged drivers, or the print spooler service.",
            "driver_update": "Possible driver or update conflict",
            "driver_update_detail": "The report mentions updates or drivers, so a recent change may have affected Windows or device stability.",
            "generic_config": "General configuration or software error",
            "generic_config_detail": "There is not enough evidence for one root cause, so start with safe, reversible checks.",
            "image_context": "Image attached for visual context",
            "image_context_detail": "The screenshot may contain important codes or wording. Confirm exact error text before changing settings.",
            "backup_first": "Back up first",
            "backup_first_detail": "Copy important files to an external drive or cloud before attempting repair steps.",
            "avoid_destructive": "Avoid destructive commands",
            "avoid_destructive_detail": "Do not format, delete partitions, run diskpart clean, or reinstall until data is safe.",
            "restart_router": "Restart router and PC",
            "restart_router_detail": "Power off the router for 30 seconds, restart the PC, and test again.",
            "test_other_site": "Test another website or app",
            "test_other_site_detail": "Check whether the problem affects one service or all internet access.",
            "dns_flush": "Refresh DNS safely",
            "dns_flush_detail": "On Windows, open PowerShell and run: ipconfig /flushdns. Then reconnect Wi-Fi.",
            "check_printer": "Check printer basics",
            "check_printer_detail": "Confirm paper, ink/toner, cables/Wi-Fi, default printer, and that no old job is stuck.",
            "restart_spooler": "Restart print queue",
            "restart_spooler_detail": "Restarting the Print Spooler can clear stuck jobs, but pause if business-critical prints are pending.",
            "create_restore": "Create a restore point",
            "create_restore_detail": "Before driver changes, create a Windows restore point if available.",
            "install_updates": "Install official updates only",
            "install_updates_detail": "Use Windows Update or the manufacturer's support page. Avoid random driver sites.",
            "note_error": "Write down the exact error",
            "note_error_detail": "Copy the full message, code, and app name. This prevents guessing.",
            "restart_safe": "Restart once",
            "restart_safe_detail": "A single restart is safe and can clear temporary lockups. Do not loop forced restarts.",
            "check_recent_changes": "Review recent changes",
            "check_recent_changes_detail": "Think of new apps, updates, drivers, USB devices, or power cuts before the error started.",
            "stop_data": "Stop if data matters",
            "stop_data_detail": "If the device contains important files, get help before repair attempts that modify disks.",
            "stop_bitlocker": "BitLocker or recovery key appears",
            "stop_bitlocker_detail": "Do not reset or reinstall. Locate the recovery key first.",
            "stop_repeat": "The same critical error repeats",
            "stop_repeat_detail": "Repeated blue screens, freezes, or disk warnings need deeper diagnosis.",
            "before_backup": "Back up important files before risky changes.",
            "before_photos": "Take photos of the exact error and current screen.",
            "before_power": "Keep laptops connected to power during repairs.",
            "before_no_delete": "Do not delete partitions, format, or reinstall unless data is already safe.",
            "customer_message": "If you are unsure or the computer contains important business/personal data, Atlas PC Support can review the case remotely before damage happens.",
            "whatsapp": "Hello Atlas PC Support, I used the AI diagnostic. OS: {os}. Difficulty: {difficulty}. Problem: {issue}",
            "disclaimer": "This assistant provides general technical guidance. Atlas PC Support is not responsible for damage, data loss, or service interruption caused by self-service actions. Stop and request professional help if data or business continuity matters.",
        }
    return {
        "basic": "Básico",
        "intermediate": "Intermedio",
        "advanced": "Avanzado",
        "data_risk": "Riesgo de datos",
        "summary": "Triaje inicial para {os}. Es orientación, no una reparación garantizada.",
        "possible_disk_or_boot": "Posible problema de disco, arranque, cifrado o datos",
        "possible_disk_or_boot_detail": "El mensaje incluye señales comunes de almacenamiento, arranque, particiones, malware o integridad de datos.",
        "network_config": "Posible problema de red, DNS o router",
        "network_config_detail": "Los síntomas mencionan conexión o navegación; suele venir de DNS, Wi‑Fi, proxy o estado del router.",
        "printer_queue": "Posible problema de cola, driver o spooler de impresión",
        "printer_queue_detail": "Los errores de impresora suelen venir de trabajos trabados, equipo offline, drivers dañados o servicio spooler.",
        "driver_update": "Posible conflicto de driver o actualización",
        "driver_update_detail": "El reporte menciona updates o drivers; un cambio reciente puede afectar estabilidad de Windows o del dispositivo.",
        "generic_config": "Error general de configuración o software",
        "generic_config_detail": "No hay suficiente evidencia para una sola causa; empieza con revisiones seguras y reversibles.",
        "image_context": "Imagen adjunta como contexto visual",
        "image_context_detail": "La captura puede contener códigos o texto clave. Confirma el error exacto antes de cambiar ajustes.",
        "backup_first": "Respalda primero",
        "backup_first_detail": "Copia archivos importantes a un disco externo o nube antes de intentar reparaciones.",
        "avoid_destructive": "Evita comandos destructivos",
        "avoid_destructive_detail": "No formatees, borres particiones, uses diskpart clean ni reinstales hasta proteger los datos.",
        "restart_router": "Reinicia router y PC",
        "restart_router_detail": "Apaga el router 30 segundos, reinicia la PC y prueba otra vez.",
        "test_other_site": "Prueba otra web o app",
        "test_other_site_detail": "Verifica si falla solo un servicio o todo el acceso a internet.",
        "dns_flush": "Refresca DNS de forma segura",
        "dns_flush_detail": "En Windows, abre PowerShell y ejecuta: ipconfig /flushdns. Luego reconecta Wi‑Fi.",
        "check_printer": "Revisa lo básico de la impresora",
        "check_printer_detail": "Confirma papel, tinta/tóner, cable/Wi‑Fi, impresora predeterminada y que no haya trabajos antiguos trabados.",
        "restart_spooler": "Reinicia la cola de impresión",
        "restart_spooler_detail": "Reiniciar Print Spooler puede limpiar trabajos trabados, pero detente si hay impresiones críticas pendientes.",
        "create_restore": "Crea un punto de restauración",
        "create_restore_detail": "Antes de cambiar drivers, crea un punto de restauración de Windows si está disponible.",
        "install_updates": "Instala solo updates oficiales",
        "install_updates_detail": "Usa Windows Update o la web del fabricante. Evita páginas aleatorias de drivers.",
        "note_error": "Anota el error exacto",
        "note_error_detail": "Copia mensaje completo, código y nombre de app. Así evitamos adivinar.",
        "restart_safe": "Reinicia una vez",
        "restart_safe_detail": "Un reinicio es seguro y puede limpiar bloqueos temporales. No hagas reinicios forzados en bucle.",
        "check_recent_changes": "Revisa cambios recientes",
        "check_recent_changes_detail": "Piensa en apps nuevas, updates, drivers, USB o cortes de luz antes de que empezara el error.",
        "stop_data": "Detente si los datos importan",
        "stop_data_detail": "Si el equipo tiene archivos importantes, pide ayuda antes de reparaciones que modifiquen discos.",
        "stop_bitlocker": "Aparece BitLocker o clave de recuperación",
        "stop_bitlocker_detail": "No reinicies de fábrica ni reinstales. Ubica primero la clave de recuperación.",
        "stop_repeat": "El error crítico se repite",
        "stop_repeat_detail": "Pantallazos azules, congelamientos o avisos de disco repetidos requieren diagnóstico profundo.",
        "before_backup": "Respalda archivos importantes antes de cambios riesgosos.",
        "before_photos": "Toma fotos del error exacto y la pantalla actual.",
        "before_power": "Mantén laptops conectadas a corriente durante reparaciones.",
        "before_no_delete": "No borres particiones, formatees ni reinstales si los datos no están seguros.",
        "customer_message": "Si no estás seguro o la computadora tiene datos personales/de trabajo importantes, Atlas PC Support puede revisar el caso remoto antes de que ocurra un daño.",
        "whatsapp": "Hola Atlas PC Support, usé el diagnóstico IA. Sistema: {os}. Dificultad: {difficulty}. Problema: {issue}",
        "disclaimer": "Este asistente ofrece orientación técnica general. Atlas PC Support no se hace responsable por daños, pérdida de datos o interrupciones causadas por acciones de autoservicio. Detente y solicita ayuda profesional si hay datos importantes o continuidad de negocio en juego.",
    }
