import frappe
import requests
from frappe import _


class WebsprixPBX:

    """Connector for WebSprix PBX API."""

    def __init__(self, settings):
        self.settings = settings
        self.base_url = getattr(settings, "base_url", "https://pbx.websprix.com/api").rstrip("/")
        self.api_key = settings.api_key
        self.organization_id = settings.organization_id
        self.extension = settings.extension

    @classmethod
    def connect(cls):
        settings = frappe.get_doc("CRM Websprix Settings")
        if not (settings and getattr(settings, "enabled", False)):
            return None
        return cls(settings)

    def request(self, endpoint: str, params: dict | None = None):
        params = params or {}
        params.setdefault("organization_id", self.organization_id)
        params.setdefault("extension", self.extension)
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()

    def get_user_settings(self):
        return self.request("user/settings")

    def fetch_users_to_transfer(self):
        return self.request("users")

    def get_contact_info(self, phone_number: str):
        return self.request("contact", params={"phone_number": phone_number})


@frappe.whitelist()
def get_user_settings():
    """Return PBX settings for the logged-in user's extension."""
    websprix = WebsprixPBX.connect()
    if not websprix:
        return {}
    try:
        return websprix.get_user_settings()
    except Exception:
        frappe.log_error(title=_("Failed to fetch WebSprix user settings"))
        return {}


@frappe.whitelist()
def fetch_users_to_transfer():

    """Return available extensions to transfer a call."""
    websprix = WebsprixPBX.connect()
    if not websprix:
        return {}
    try:
        return websprix.fetch_users_to_transfer()
    except Exception:
        frappe.log_error(title=_("Failed to fetch WebSprix transfer users"))
        return {}


@frappe.whitelist()
def get_contact_info(phone_number: str):
    """Return contact information for a phone number from PBX."""
    websprix = WebsprixPBX.connect()
    if not websprix:
        return {}
    try:
        return websprix.get_contact_info(phone_number)
    except Exception:
        frappe.log_error(title=_("Failed to fetch contact info from WebSprix"))
        return {}
