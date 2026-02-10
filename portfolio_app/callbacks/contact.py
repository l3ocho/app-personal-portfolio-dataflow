"""Contact form submission callback with Formspree integration."""

import re
from typing import Any

import dash_mantine_components as dmc
import requests
from dash import Input, Output, State, callback, no_update
from dash_iconify import DashIconify

FORMSPREE_ENDPOINT = "https://formspree.io/f/mqelqzpd"
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _validate_form(
    name: str | None, email: str | None, message: str | None
) -> str | None:
    """Validate form fields and return error message if invalid."""
    if not name or not name.strip():
        return "Please enter your name."
    if not email or not email.strip():
        return "Please enter your email address."
    if not EMAIL_REGEX.match(email.strip()):
        return "Please enter a valid email address."
    if not message or not message.strip():
        return "Please enter a message."
    return None


def _create_success_alert() -> dmc.Alert:
    """Create success feedback alert."""
    return dmc.Alert(
        "Thank you for your message! I'll get back to you soon.",
        title="Message Sent",
        color="green",
        variant="light",
        icon=DashIconify(icon="tabler:check", width=20),
        withCloseButton=True,
    )


def _create_error_alert(message: str) -> dmc.Alert:
    """Create error feedback alert."""
    return dmc.Alert(
        message,
        title="Error",
        color="red",
        variant="light",
        icon=DashIconify(icon="tabler:alert-circle", width=20),
        withCloseButton=True,
    )


@callback(  # type: ignore[misc]
    Output("contact-feedback", "children"),
    Output("contact-submit", "loading"),
    Output("contact-name", "value"),
    Output("contact-email", "value"),
    Output("contact-subject", "value"),
    Output("contact-message", "value"),
    Output("contact-name", "error"),
    Output("contact-email", "error"),
    Output("contact-message", "error"),
    Input("contact-submit", "n_clicks"),
    State("contact-name", "value"),
    State("contact-email", "value"),
    State("contact-subject", "value"),
    State("contact-message", "value"),
    State("contact-gotcha", "value"),
    prevent_initial_call=True,
)
def submit_contact_form(
    n_clicks: int | None,
    name: str | None,
    email: str | None,
    subject: str | None,
    message: str | None,
    gotcha: str | None,
) -> tuple[Any, ...]:
    """Submit contact form to Formspree.

    Args:
        n_clicks: Button click count.
        name: User's name.
        email: User's email address.
        subject: Message subject (optional).
        message: Message content.
        gotcha: Honeypot field value (should be empty for real users).

    Returns:
        Tuple of (feedback, loading, name, email, subject, message,
                  name_error, email_error, message_error).
    """
    if not n_clicks:
        return (no_update,) * 9

    # Check honeypot - if filled, silently "succeed" (it's a bot)
    if gotcha:
        return (
            _create_success_alert(),
            False,
            "",
            "",
            None,
            "",
            None,
            None,
            None,
        )

    # Validate form
    validation_error = _validate_form(name, email, message)
    if validation_error:
        # Determine which field has the error
        name_error = "Required" if not name or not name.strip() else None
        email_error = None
        message_error = "Required" if not message or not message.strip() else None

        if not email or not email.strip():
            email_error = "Required"
        elif not EMAIL_REGEX.match(email.strip()):
            email_error = "Invalid email format"

        return (
            _create_error_alert(validation_error),
            False,
            no_update,
            no_update,
            no_update,
            no_update,
            name_error,
            email_error,
            message_error,
        )

    # Prepare form data (validation passed, so name/email/message are not None)
    assert name is not None
    assert email is not None
    assert message is not None
    form_data = {
        "name": name.strip(),
        "email": email.strip(),
        "subject": subject or "General Inquiry",
        "message": message.strip(),
        "_gotcha": "",  # Formspree honeypot
    }

    # Submit to Formspree
    try:
        response = requests.post(
            FORMSPREE_ENDPOINT,
            json=form_data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if response.status_code == 200:
            # Success - clear form
            return (
                _create_success_alert(),
                False,
                "",
                "",
                None,
                "",
                None,
                None,
                None,
            )
        else:
            # Formspree returned an error
            return (
                _create_error_alert(
                    "Failed to send message. Please try again or use direct contact."
                ),
                False,
                no_update,
                no_update,
                no_update,
                no_update,
                None,
                None,
                None,
            )

    except requests.exceptions.Timeout:
        return (
            _create_error_alert("Request timed out. Please try again."),
            False,
            no_update,
            no_update,
            no_update,
            no_update,
            None,
            None,
            None,
        )
    except requests.exceptions.RequestException:
        return (
            _create_error_alert(
                "Network error. Please check your connection and try again."
            ),
            False,
            no_update,
            no_update,
            no_update,
            no_update,
            None,
            None,
            None,
        )
