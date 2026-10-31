"""Email templates (research R10).

Rule: emails to visitor-supplied addresses contain only fixed copy and numbers — never text the
visitor typed (name, company, message…). Otherwise the public forms become a spam relay through
the VeritX Gmail account. Free text goes only to the staff inbox. Staff emails are in Spanish.
"""

SIGNATURE = {
    "es": "— Equipo VeritX Vision\nTlaxcala, México",
    "en": "— The VeritX Vision team\nTlaxcala, Mexico",
    "fr": "— L'équipe VeritX Vision\nTlaxcala, Mexique",
}

VISITOR_CONTACT = {
    "es": ("Recibimos tu mensaje — VeritX Vision",
           "Gracias por contactar a VeritX Vision.\n\nRecibimos tu mensaje y te responderemos en "
           "un día hábil."),
    "en": ("We received your message — VeritX Vision",
           "Thank you for contacting VeritX Vision.\n\nWe received your message and will reply "
           "within one business day."),
    "fr": ("Nous avons reçu votre message — VeritX Vision",
           "Merci d'avoir contacté VeritX Vision.\n\nNous avons bien reçu votre message et vous "
           "répondrons sous un jour ouvré."),
}

# Labels mirror src/translations.js → calculatorPage.sections (keep in sync when copy changes).
CALC_LABELS = {
    "es": {
        "subject": "Tu estimación de ahorro — VeritX Vision",
        "intro": "Este es el desglose de ahorro anual que calculaste en nuestro sitio.",
        "inputs": "Datos ingresados", "savings": "Ahorro anual estimado", "total": "Total anual",
        "note": "Es una estimación basada en tus datos; no es una cotización.",
        "sections": {"defects": "1. Reducción de defectos no detectados",
                     "laborHours": "2. Reducción de horas-hombre en inspección manual",
                     "lineSpeed": "3. Aumento de velocidad de línea"},
        "fields": {
            "rateBefore": "Tasa de defectos actual (%)",
            "rateAfter": "Tasa de defectos esperada con el sistema (%)",
            "volume": "Volumen de producción anual (m² producidos)",
            "costPerDefect": "Costo por defecto",
            "hoursBefore": "Horas-persona de inspección antes (por turno)",
            "hoursAfter": "Horas-persona de inspección después (por turno)",
            "hourlyCost": "Costo por hora", "shiftsPerYear": "Turnos/días operativos al año",
            "speedBefore": "Velocidad actual de línea (m/min)",
            "speedAfter": "Nueva velocidad de línea (m/min)",
            "hoursPerYear": "Horas de operación al año",
            "marginPerMeter": "Margen de contribución por metro producido"},
    },
    "en": {
        "subject": "Your savings estimate — VeritX Vision",
        "intro": "Here is the annual savings breakdown you calculated on our website.",
        "inputs": "Your inputs", "savings": "Estimated annual savings", "total": "Annual total",
        "note": "This is an estimate based on your inputs, not a quote.",
        "sections": {"defects": "1. Reducing undetected defects",
                     "laborHours": "2. Reducing manual-inspection labor hours",
                     "lineSpeed": "3. Increasing line speed"},
        "fields": {
            "rateBefore": "Current defect rate (%)",
            "rateAfter": "Expected defect rate with the system (%)",
            "volume": "Annual production volume (m² produced)",
            "costPerDefect": "Cost per defect",
            "hoursBefore": "Inspection hours before (per shift)",
            "hoursAfter": "Inspection hours after (per shift)",
            "hourlyCost": "Cost per hour", "shiftsPerYear": "Operating shifts/days per year",
            "speedBefore": "Current line speed (m/min)", "speedAfter": "New line speed (m/min)",
            "hoursPerYear": "Operating hours per year",
            "marginPerMeter": "Contribution margin per meter produced"},
    },
    "fr": {
        "subject": "Votre estimation d'économies — VeritX Vision",
        "intro": "Voici le détail des économies annuelles que vous avez calculées sur notre site.",
        "inputs": "Vos données", "savings": "Économies annuelles estimées",
        "total": "Total annuel",
        "note": "Il s'agit d'une estimation fondée sur vos données, pas d'un devis.",
        "sections": {"defects": "1. Réduction des défauts non détectés",
                     "laborHours": "2. Réduction des heures de main-d'œuvre en inspection manuelle",
                     "lineSpeed": "3. Augmentation de la vitesse de ligne"},
        "fields": {
            "rateBefore": "Taux de défauts actuel (%)",
            "rateAfter": "Taux de défauts attendu avec le système (%)",
            "volume": "Volume de production annuel (m² produits)",
            "costPerDefect": "Coût par défaut",
            "hoursBefore": "Heures d'inspection avant (par équipe)",
            "hoursAfter": "Heures d'inspection après (par équipe)",
            "hourlyCost": "Coût horaire", "shiftsPerYear": "Équipes/jours d'exploitation par an",
            "speedBefore": "Vitesse de ligne actuelle (m/min)",
            "speedAfter": "Nouvelle vitesse de ligne (m/min)",
            "hoursPerYear": "Heures d'exploitation par an",
            "marginPerMeter": "Marge de contribution par mètre produit"},
    },
}

# Allowed calculator keys (also used for request validation).
CALC_SECTIONS = {
    "defects": ("rateBefore", "rateAfter", "volume", "costPerDefect"),
    "laborHours": ("hoursBefore", "hoursAfter", "hourlyCost", "shiftsPerYear"),
    "lineSpeed": ("speedBefore", "speedAfter", "hoursPerYear", "marginPerMeter"),
}


def _number(value: float, lang: str, decimals: int) -> str:
    text = f"{value:,.{decimals}f}"
    if decimals:
        text = text.rstrip("0").rstrip(".")
    if lang == "fr":
        text = text.replace(",", " ").replace(".", ",")
    return text


def money(value: float, currency: str, lang: str) -> str:
    return f"{_number(round(value), lang, 0)} {currency}"


def visitor_contact(lang: str) -> tuple[str, str]:
    subject, body = VISITOR_CONTACT[lang]
    return subject, f"{body}\n\n{SIGNATURE[lang]}\n"


def visitor_calculator(lang: str, currency: str, inputs: dict, results: dict) -> tuple[str, str]:
    t = CALC_LABELS[lang]
    lines = [t["intro"], ""]
    for section, fields in CALC_SECTIONS.items():
        if section not in inputs and section not in results:
            continue
        lines.append(t["sections"][section])
        for field in fields:
            if field in inputs.get(section, {}):
                lines.append(f"  {t['fields'][field]}: "
                             f"{_number(inputs[section][field], lang, 4)}")
        if section in results:
            lines.append(f"  → {t['savings']}: {money(results[section], currency, lang)}")
        lines.append("")
    if "total" in results:
        lines.append(f"{t['total']}: {money(results['total'], currency, lang)}")
    lines += ["", t["note"], "", SIGNATURE[lang]]
    return t["subject"], "\n".join(lines) + "\n"


_STAFF_FIELDS = (
    ("name", "Nombre"), ("company", "Empresa"), ("email", "Correo"), ("country", "País"),
    ("stage", "Etapa"), ("video_tool", "Herramienta de videollamada"), ("message", "Mensaje"),
)


def staff_contact(payload: dict) -> tuple[str, str]:
    subject = f"[Sitio] Nuevo mensaje: {payload.get('name', '')} ({payload.get('company', '')})"
    lines = ["Nuevo mensaje desde el formulario de contacto del sitio.", ""]
    lines += [f"{label}: {payload[key]}" for key, label in _STAFF_FIELDS if payload.get(key)]
    lines += ["", "Responde a este correo para contestarle directamente."]
    return subject, "\n".join(lines) + "\n"


def staff_calculator(payload: dict) -> tuple[str, str]:
    who = payload.get("name") or payload["email"]
    subject = f"[Sitio] Resultados de calculadora enviados a {who}"
    _, body = visitor_calculator("es", payload["currency"], payload["inputs"], payload["results"])
    header = [f"Nombre: {payload.get('name') or '—'}", f"Correo: {payload['email']}",
              f"Idioma del visitante: {payload['lang']}", "", "Copia de lo que recibió:", ""]
    return subject, "\n".join(header) + body


# Calendar invites go to the visitor-typed address too, so they get fixed copy only.
EVENT_COPY = {
    "es": ("VeritX Vision — Demo", "Reunión con el equipo de VeritX Vision. Usa el enlace de "
           "videollamada de esta invitación. Si necesitas cambiar el horario, responde al correo "
           "de confirmación."),
    "en": ("VeritX Vision — Demo", "Meeting with the VeritX Vision team. Use the video-call link "
           "in this invitation. If you need another time, reply to the confirmation email."),
    "fr": ("VeritX Vision — Démo", "Rendez-vous avec l'équipe VeritX Vision. Utilisez le lien de "
           "visioconférence de cette invitation. Pour changer d'horaire, répondez à l'e-mail de "
           "confirmation."),
}

VISITOR_BOOKING = {
    "es": ("Tu reunión con VeritX Vision está agendada",
           "Tu reunión con VeritX Vision quedó agendada para el {slot} (hora de Ciudad de México)."
           "\n\nRecibirás una invitación de calendario con el enlace de videollamada. Si necesitas "
           "cambiar el horario, responde a este correo."),
    "en": ("Your meeting with VeritX Vision is booked",
           "Your meeting with VeritX Vision is booked for {slot} (Mexico City time).\n\nYou will "
           "receive a calendar invitation with the video-call link. If you need another time, "
           "reply to this email."),
    "fr": ("Votre rendez-vous avec VeritX Vision est confirmé",
           "Votre rendez-vous avec VeritX Vision est prévu le {slot} (heure de Mexico).\n\nVous "
           "recevrez une invitation d'agenda avec le lien de visioconférence. Pour changer "
           "d'horaire, répondez à cet e-mail."),
}


def slot_label(slot_iso: str) -> str:
    """'2026-11-04T10:00:00-06:00' → '2026-11-04 10:00'. Language-neutral on purpose."""
    return f"{slot_iso[:10]} {slot_iso[11:16]}"


def visitor_booking(lang: str, slot_iso: str) -> tuple[str, str]:
    subject, body = VISITOR_BOOKING[lang]
    return subject, f"{body.format(slot=slot_label(slot_iso))}\n\n{SIGNATURE[lang]}\n"


def staff_booking(payload: dict) -> tuple[str, str]:
    subject = (f"[Sitio] Reunión agendada {slot_label(payload['slot_start'])}: "
               f"{payload.get('name', '')} ({payload.get('company', '')})")
    lines = [f"Reunión agendada para el {slot_label(payload['slot_start'])} (CDMX). El evento "
             "ya está en el calendario con enlace de Meet.", ""]
    lines += [f"{label}: {payload[key]}" for key, label in _STAFF_FIELDS if payload.get(key)]
    if payload.get("video_tool") and payload["video_tool"] != "Google Meet":
        lines += ["", f"Prefiere {payload['video_tool']}: envíale otro enlace si hace falta."]
    lines += ["", "Responde a este correo para contestarle directamente."]
    return subject, "\n".join(lines) + "\n"


# Invite and reset emails go to addresses staff entered or that already have an account; they
# still carry no visitor-typed text beyond the account holder's own name (entered by staff).
INVITE = {
    "es": ("Tu acceso a VeritX Vision Home",
           "Hola {name},\n\nVeritX Vision te dio acceso a Vision Home para {company}. Crea tu "
           "contraseña con este enlace (válido 7 días, un solo uso):\n\n{link}\n\nTu usuario es "
           "este correo electrónico."),
    "en": ("Your access to VeritX Vision Home",
           "Hello {name},\n\nVeritX Vision has given you access to Vision Home for {company}. "
           "Set your password with this link (valid for 7 days, single use):\n\n{link}\n\nYour "
           "username is this email address."),
    "fr": ("Votre accès à VeritX Vision Home",
           "Bonjour {name},\n\nVeritX Vision vous a donné accès à Vision Home pour {company}. "
           "Créez votre mot de passe avec ce lien (valable 7 jours, usage unique) :\n\n{link}\n\n"
           "Votre identifiant est cette adresse e-mail."),
}

RESET = {
    "es": ("Restablece tu contraseña de VeritX Vision",
           "Recibimos una solicitud para restablecer tu contraseña. Usa este enlace (válido 30 "
           "minutos, un solo uso):\n\n{link}\n\nSi no fuiste tú, ignora este correo."),
    "en": ("Reset your VeritX Vision password",
           "We received a request to reset your password. Use this link (valid for 30 minutes, "
           "single use):\n\n{link}\n\nIf this wasn't you, ignore this email."),
    "fr": ("Réinitialisez votre mot de passe VeritX Vision",
           "Nous avons reçu une demande de réinitialisation de votre mot de passe. Utilisez ce "
           "lien (valable 30 minutes, usage unique) :\n\n{link}\n\nSi ce n'était pas vous, "
           "ignorez cet e-mail."),
}


def invite(lang: str, name: str, company: str, link: str) -> tuple[str, str]:
    subject, body = INVITE[lang]
    return subject, f"{body.format(name=name, company=company, link=link)}\n\n{SIGNATURE[lang]}\n"


def reset(lang: str, link: str) -> tuple[str, str]:
    subject, body = RESET[lang]
    return subject, f"{body.format(link=link)}\n\n{SIGNATURE[lang]}\n"
