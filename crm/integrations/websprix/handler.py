import bleach
import frappe
import requests
from frappe import _
from frappe.integrations.utils import create_request_log

from crm.integrations.api import get_contact_by_phone_number


@frappe.whitelist(allow_guest=True)
def handle_request(**kwargs):
    """Handle incoming requests from WebSprix."""
    validate_request()
    if not is_integration_enabled():
        return

    request_log = create_request_log(
        kwargs,
        request_description="WebSprix Call",
        service_name="WebSprix",
        request_headers=frappe.request.headers,
        is_remote_request=1,
    )

    try:
        request_log.status = "Completed"
        settings = get_websprix_settings()
        if not settings.enabled:
            return

        call_payload = kwargs

        frappe.publish_realtime("websprix_call", call_payload)
        status = call_payload.get("status")
        if status == "free":
            return

        if call_log := get_call_log(call_payload):
            update_call_log(call_payload, call_log=call_log)
        else:
            create_call_log(
                call_id=call_payload.get("call_id"),
                from_number=call_payload.get("from"),
                to_number=call_payload.get("to"),
                medium="WebSprix",
                status=get_call_log_status(call_payload),
                agent=call_payload.get("agent"),
            )
    except Exception:
        request_log.status = "Failed"
        request_log.error = frappe.get_traceback()
        frappe.db.rollback()
        frappe.log_error(title="Error while creating/updating call record")
        frappe.db.commit()
    finally:
        request_log.save(ignore_permissions=True)
        frappe.db.commit()


@frappe.whitelist()
def make_a_call(to_number, from_number=None):
    if not is_integration_enabled():
        frappe.throw(_("Please setup WebSprix integration"), title=_("Integration Not Enabled"))

    endpoint = get_websprix_endpoint("call")

    if not from_number:
        from_number = frappe.get_value("CRM Telephony Agent", {"user": frappe.session.user}, "mobile_no")

    if not from_number:
        frappe.throw(
            _("You do not have mobile number set in your Telephony Agent"), title=_("Mobile Number Missing")
        )

    try:
        response = requests.post(
            endpoint,
            json={"from": from_number, "to": to_number},
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if exc := response.json().get("error"):
            frappe.throw(bleach.linkify(exc), title=_("WebSprix Exception"))
    else:
        res = response.json()
        call_payload = res.get("call", {})
        create_call_log(
            call_id=call_payload.get("id"),
            from_number=from_number,
            to_number=to_number,
            medium="WebSprix",
            call_type="Outgoing",
            agent=frappe.session.user,
        )

    call_details = response.json()
    call_details["call_id"] = call_details.get("id", "")
    return call_details


def get_websprix_endpoint(action=None):
    settings = get_websprix_settings()
    base = settings.base_url.rstrip("/") + "/api/"
    if action:
        base += action
    return base


def get_websprix_settings():
    return frappe.get_single("CRM WebSprix Settings")


@frappe.whitelist(allow_guest=True)
def is_integration_enabled():
    return frappe.db.get_single_value("CRM WebSprix Settings", "enabled", True)


# Call Log Functions
def create_call_log(
    call_id,
    from_number,
    to_number,
    medium,
    agent,
    status="Ringing",
    call_type="Incoming",
):
    call_log = frappe.new_doc("CRM Call Log")
    call_log.id = call_id
    call_log.to = to_number
    call_log.medium = medium
    call_log.type = call_type
    call_log.status = status
    call_log.telephony_medium = "WebSprix"
    setattr(call_log, "from", from_number)

    if call_type == "Incoming":
        call_log.receiver = agent
    else:
        call_log.caller = agent

    contact_number = from_number if call_type == "Incoming" else to_number
    link(contact_number, call_log)

    call_log.save(ignore_permissions=True)
    frappe.db.commit()
    return call_log


def link(contact_number, call_log):
    contact = get_contact_by_phone_number(contact_number)
    if contact.get("name"):
        doctype = "Contact"
        docname = contact.get("name")
        if contact.get("lead"):
            doctype = "CRM Lead"
            docname = contact.get("lead")
        elif contact.get("deal"):
            doctype = "CRM Deal"
            docname = contact.get("deal")
        call_log.link_with_reference_doc(doctype, docname)


def get_call_log(call_payload):
    call_log_id = call_payload.get("call_id")
    if frappe.db.exists("CRM Call Log", call_log_id):
        return frappe.get_doc("CRM Call Log", call_log_id)


def get_call_log_status(call_payload):
    status = call_payload.get("status")
    if status == "completed":
        return "Completed"
    elif status == "in-progress":
        return "In Progress"
    elif status == "busy":
        return "Ringing"
    elif status == "no-answer":
        return "No Answer"
    elif status == "failed":
        return "Failed"
    return status


def update_call_log(call_payload, status="Ringing", call_log=None):
    call_log = call_log or get_call_log(call_payload)
    status = get_call_log_status(call_payload)
    try:
        if call_log:
            call_log.status = status
            call_log.to = call_payload.get("to")
            call_log.duration = call_payload.get("duration") or 0
            call_log.recording_url = call_payload.get("recording_url") or ""
            call_log.start_time = call_payload.get("start_time")
            call_log.end_time = call_payload.get("end_time")
            if call_payload.get("agent"):
                call_log.receiver = call_payload.get("agent")
            call_log.save(ignore_permissions=True)
            frappe.db.commit()
            return call_log
    except Exception:
        frappe.log_error(title="Error while updating call record")
        frappe.db.commit()


def validate_request():
    webhook_verify_token = frappe.db.get_single_value("CRM WebSprix Settings", "webhook_verify_token")
    key = frappe.request.args.get("key")
    is_valid = key and key == webhook_verify_token

    if not is_valid:
        frappe.throw(_("Unauthorized request"), exc=frappe.PermissionError)
