import frappe
import requests
from frappe import _
from frappe.model.document import Document


class CRMWebSprixSettings(Document):
    def validate(self) -> None:
        self.verify_credentials()

    def verify_credentials(self) -> None:
        if self.enabled and self.organization_id and self.api_key:
            verify_url = (
                f"https://etw-pbx-cloud1.websprix.com/api/v2/cust_ext/{self.organization_id}/cust"
            )
            headers = {"x-api-key": self.api_key}
            res = requests.get(verify_url, headers=headers)
            if res.status_code not in [200, 201]:
                frappe.throw(_("Invalid WebSprix Organization ID or API Key"))
