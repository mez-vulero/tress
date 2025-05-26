import frappe
import requests
from frappe import _

from crm.integrations.api import get_contact_by_phone_number

BASE_URL = "https://etw-pbx-cloud1.websprix.com/api/v2"


@frappe.whitelist()
def get_user_settings():
	user = frappe.session.user
	agent = frappe.db.get_value("CRM Telephony Agent", user, "websprix_number")
	if not agent:
		return None

	settings = frappe.get_single("CRM WebSprix Settings")
	url = f"{BASE_URL}/onboard//get_ip_info/{settings.organization_id}/{agent}/1"
	headers = {"x-api-key": settings.api_key}

	try:
		resp = requests.get(url, headers=headers)
		if resp.status_code in [200, 201]:
			return resp.json()
	except requests.exceptions.RequestException as e:
		frappe.log_error(str(e), "WebSprix get_user_settings")
	return None


@frappe.whitelist()
def fetch_users_to_transfer():
	settings = frappe.get_single("CRM WebSprix Settings")
	url = f"{BASE_URL}/cust_ext/{settings.organization_id}/cust"
	headers = {"x-api-key": settings.api_key}
	try:
		resp = requests.get(url, headers=headers)
		if resp.status_code in [200, 201]:
			return resp.json()
	except requests.exceptions.RequestException as e:
		frappe.log_error(str(e), "WebSprix fetch_users_to_transfer")
	return None


@frappe.whitelist()
def get_contact_info(phone_number):
	return get_contact_by_phone_number(phone_number)
