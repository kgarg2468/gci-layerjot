# Sterile Technique Breach Advisory Responses

Source URLs:
- https://www.cdc.gov/infection-control/hcp/intravascular-catheter-related-infections/summary-recommendations.html
- https://www.cdc.gov/healthcare-associated-infections/media/pdfs/checklist-for-CLABSI-P.pdf

Status: Team-curated canned response set for offline or camera-advisory flows. Requires clinical review before institutional use.

Use these responses when the backend or Unity fallback detects a sterile-technique risk:

## Hand hygiene not confirmed

Action command: `show_alert`

Spoken response: "Please confirm hand hygiene was completed before continuing."

Severity: warning

## Non-sterile contact after gloving

Action command: `flag_breach`

Spoken response: "Possible sterile field breach detected. Treat this as advisory and verify sterile technique before continuing."

Severity: warning

## Site antiseptic drying incomplete

Action command: `show_alert`

Spoken response: "Allow the antiseptic to dry fully before catheter placement or dressing application."

Severity: warning

## Dressing integrity concern

Action command: `show_alert`

Spoken response: "Inspect the dressing and confirm it is clean, dry, intact, and properly secured."

Severity: warning

## Unsafe clinical request

Action command: `show_alert`

Spoken response: "I cannot provide diagnosis or medication dosing guidance. Please consult the attending physician."

Severity: warning
