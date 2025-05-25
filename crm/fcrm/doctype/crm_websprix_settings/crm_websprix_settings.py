import frappe
import requests
from frappe import _
from frappe.model.document import Document


class CRMWebsprixSettings(Document):
	def validate(self):
		self.verify_credentials()

	def verify_credentials(self):
		if self.enabled:
			response = requests.get(
				f"https://etw-pbx-cloud1.websprix.com/api/v2/onboard/get_ip_info/{self.organization_id}/{self.extension}/1",
				headers={"X-Auth-Token": self.get_password("api_key")},
			)
			if response.status_code != 200:
				frappe.throw(
					_(f"Please enter valid WebSprix credentials: {response.reason}"),
					title=_("Invalid credentials"),
				)
