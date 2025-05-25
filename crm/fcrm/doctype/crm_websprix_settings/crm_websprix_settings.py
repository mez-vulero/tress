import frappe
import requests
from frappe import _
from frappe.model.document import Document

class CRMWebSprixSettings(Document):
    def validate(self):
        self.verify_credentials()

    def verify_credentials(self):
        if self.enabled:
            response = requests.get(
                f"https://api.websprix.com/v1/organizations/{self.organization_id}/extensions/{self.extension}",
                headers={"Authorization": f"Bearer {self.get_password('api_key')}"},
            )
            if response.status_code != 200:
                frappe.throw(
                    _(f"Please enter valid WebSprix credentials: {response.reason}"),
                    title=_("Invalid credentials"),
                )
