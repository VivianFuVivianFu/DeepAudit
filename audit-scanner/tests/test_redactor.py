from privacy.redactor import redact


def test_redact_email():
    text = "Contact me at alice@example.com for details"
    out = redact(text)
    assert (
        "[REDACTED_EMAILS]" in out["redacted_text"].upper()
        or "[REDACTED_EMAILS]" in out["redacted_text"]
    )
    assert out["counts"]["emails"] == 1
