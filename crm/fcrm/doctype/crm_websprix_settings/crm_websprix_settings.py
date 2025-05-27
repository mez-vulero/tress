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
				f"https://etw-pbx-cloud1.websprix.com/api/v1/Account/{self.auth_id}/",
				auth=(self.auth_id, self.get_password("auth_token")),
			)
			if response.status_code != 200:
				frappe.throw(
					_(f"Please enter valid WebSprix Auth ID & Auth Token: {response.reason}"),
					title=_("Invalid credentials"),
				)

			if self.organization_id and self.api_key:
				verify_url = (
					f"https://etw-pbx-cloud1.websprix.com/api/v2/cust_ext/{self.organization_id}/cust"
				)
				headers = {"x-api-key": self.api_key}
				res = requests.get(verify_url, headers=headers)
				if res.status_code not in [200, 201]:
					frappe.throw(_("Invalid WebSprix Organization ID or API Key"))
