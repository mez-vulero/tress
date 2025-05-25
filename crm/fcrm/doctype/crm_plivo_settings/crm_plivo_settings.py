import frappe
import requests
from frappe import _
from frappe.model.document import Document


class CRMPlivoSettings(Document):
    def validate(self):
        self.verify_credentials()

    def verify_credentials(self):
        if self.enabled:
            response = requests.get(
                f"https://api.plivo.com/v1/Account/{self.auth_id}/",
                auth=(self.auth_id, self.get_password("auth_token")),
            )
            if response.status_code != 200:
                frappe.throw(
                    _(f"Please enter valid Plivo Auth ID & Auth Token: {response.reason}"),
                    title=_("Invalid credentials"),
                )
