"""PDF form filling pipeline: extract -> fill -> review -> send."""
import json
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class FormField:
    name: str
    field_type: str  # text, checkbox, signature, date
    value: Optional[str]
    required: bool
    page: int
    rect: tuple  # x, y, width, height


@dataclass
class PDFForm:
    form_id: str
    source: str  # email attachment, file upload
    fields: list
    filled_fields: dict
    status: str  # extracted, filling, review, sent


class PDFFormProcessor:
    """Processes PDF forms: extract fields, fill values, review, send."""

    def __init__(self):
        self.forms = {}

    def extract_fields(self, pdf_path: str, form_id: str) -> PDFForm:
        """Extract form fields from a PDF. Placeholder for PDFKit integration."""
        # In production: use PDFKit (iOS) or PyPDF2/pdfrw (Python) to extract
        # For now, return a mock form
        fields = [
            FormField("patient_name", "text", None, True, 1, (50, 100, 200, 20)),
            FormField("date_of_birth", "date", None, True, 1, (50, 130, 100, 20)),
            FormField("signature", "signature", None, True, 2, (50, 700, 200, 40)),
        ]
        form = PDFForm(
            form_id=form_id,
            source=pdf_path,
            fields=fields,
            filled_fields={},
            status="extracted",
        )
        self.forms[form_id] = form
        return form

    def fill_field(self, form_id: str, field_name: str, value: str) -> bool:
        """Fill a form field with a value."""
        form = self.forms.get(form_id)
        if not form:
            return False
        for field in form.fields:
            if field.name == field_name:
                field.value = value
                form.filled_fields[field_name] = value
                form.status = "filling"
                return True
        return False

    def auto_fill(self, form_id: str, context: dict) -> int:
        """Auto-fill fields from context (user profile, memory corpus)."""
        form = self.forms.get(form_id)
        if not form:
            return 0
        filled = 0
        for field in form.fields:
            if field.name in context:
                field.value = context[field.name]
                form.filled_fields[field.name] = context[field.name]
                filled += 1
        if filled > 0:
            form.status = "filling"
        return filled

    def get_review_summary(self, form_id: str) -> dict:
        """Get a summary for user review before sending."""
        form = self.forms.get(form_id)
        if not form:
            return {}
        required_missing = [
            f.name for f in form.fields if f.required and not f.value
        ]
        return {
            "form_id": form_id,
            "total_fields": len(form.fields),
            "filled_fields": len(form.filled_fields),
            "required_missing": required_missing,
            "ready_to_send": len(required_missing) == 0,
            "fields": [
                {"name": f.name, "type": f.field_type, "value": f.value, "required": f.required}
                for f in form.fields
            ],
        }

    def mark_sent(self, form_id: str):
        """Mark the form as sent."""
        form = self.forms.get(form_id)
        if form:
            form.status = "sent"
