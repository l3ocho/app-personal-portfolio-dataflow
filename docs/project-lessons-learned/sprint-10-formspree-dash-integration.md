# Sprint 10 - Formspree Integration with Dash Callbacks

## Context
Implementing a contact form on a Dash portfolio site that submits to Formspree, a third-party form handling service.

## Insights

### Formspree AJAX Submission
Formspree supports AJAX submissions (no page redirect) when you:
1. POST with `Content-Type: application/json`
2. Include `Accept: application/json` header
3. Send form data as JSON body

This returns a JSON response instead of redirecting to a thank-you page, which is ideal for single-page Dash applications.

### Dash Multi-Output Callbacks for Forms
When handling form submission with validation and feedback, use a multi-output callback pattern:

```python
@callback(
    Output("feedback-container", "children"),  # Success/error alert
    Output("submit-button", "loading"),        # Button loading state
    Output("field-1", "value"),                # Clear on success
    Output("field-2", "value"),                # Clear on success
    Output("field-1", "error"),                # Field-level errors
    Output("field-2", "error"),                # Field-level errors
    Input("submit-button", "n_clicks"),
    State("field-1", "value"),
    State("field-2", "value"),
    prevent_initial_call=True,
)
```

Use `no_update` for outputs you don't want to change (e.g., keep form values on validation error, only clear on success).

### Honeypot Spam Protection
Simple and effective bot protection without CAPTCHA:
1. Add a hidden text input field (CSS: `position: absolute; left: -9999px`)
2. Set `tabIndex=-1` and `autoComplete="off"` to prevent accidental filling
3. In callback, check if honeypot has value - if yes, it's a bot
4. For bots: return fake success (don't reveal detection)
5. For humans: proceed with real submission

Formspree also accepts `_gotcha` as a honeypot field name in the JSON payload.

## Code Pattern

```python
# Honeypot check - bots fill hidden fields
if honeypot_value:
    # Fake success - don't let bots know they were caught
    return (_create_success_alert(), False, "", "", None, None)

# Real submission for humans
response = requests.post(
    FORMSPREE_ENDPOINT,
    json=form_data,
    headers={"Accept": "application/json", "Content-Type": "application/json"},
    timeout=10,
)
```

## Prevention/Best Practices
- Always use `timeout` parameter with `requests.post()` to avoid hanging
- Wrap external API calls in try/except for network errors
- Return user-friendly error messages, not technical details
- Use DMC's `required=True` and `error` props for form validation feedback

## Tags
formspree, dash, callbacks, forms, spam-protection, honeypot, ajax, python, requests, validation
