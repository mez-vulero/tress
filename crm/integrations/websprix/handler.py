import bleach
import frappe
import requests
from frappe import _
from frappe.integrations.utils import create_request_log

from crm.integrations.api import get_contact_by_phone_number

@frappe.whitelist(allow_guest=True)
def handle_request(**kwargs):
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
        websprix_settings = get_websprix_settings()
        if not websprix_settings.enabled:
            return

        call_payload = kwargs

        frappe.publish_realtime("websprix_call", call_payload)
        status = call_payload.get("CallStatus")
        if status == "free":
            return

        if call_log := get_call_log(call_payload):
            update_call_log(call_payload, call_log=call_log)
        else:
            create_call_log(
                call_id=call_payload.get("CallUUID"),
                from_number=call_payload.get("From"),
                to_number=call_payload.get("To"),
                medium="WebSprix",  # placeholder
                status=get_call_log_status(call_payload),
                agent=call_payload.get("AgentEmail"),
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
def make_a_call(to_number, from_number=None, caller_id=None):
    if not is_integration_enabled():
        frappe.throw(_("Please setup WebSprix integration"), title=_("Integration Not Enabled"))

    endpoint = get_websprix_endpoint("Call/")

    if not from_number:
        from_number = frappe.get_value("CRM Telephony Agent", {"user": frappe.session.user}, "mobile_no")

    if not caller_id:
        caller_id = frappe.get_value("CRM Telephony Agent", {"user": frappe.session.user}, "websprix_number")

    if not from_number:
        frappe.throw(
            _("You do not have mobile number set in your Telephony Agent"), title=_("Mobile Number Missing")
        )

    record_call = frappe.db.get_single_value("CRM WebSprix Settings", "record_call")

    headers = {"x-api-key": get_websprix_settings().api_key}
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            data={
                "from": caller_id or from_number,
                "to": to_number,
                "answer_url": get_status_updater_url(),
            },
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if exc := response.json().get("error"):
            frappe.throw(bleach.linkify(exc), title=_("WebSprix Exception"))
    else:
        res = response.json()
        call_payload = res.get("", {})
        create_call_log(
            call_id=call_payload.get("request_uuid"),
            from_number=from_number,
            to_number=to_number,
            medium="WebSprix",
            call_type="Outgoing",
            agent=frappe.session.user,
        )

    call_details = response.json()
    call_details["CallUUID"] = call_details.get("request_uuid", "")
    return call_details


def get_websprix_endpoint(action=None, version="v1"):
    settings = get_websprix_settings()
    base = (
        f"https://etw-pbx-cloud1.websprix.com/api/{version}/Account/{settings.customer_id}/"
    )
    if action:
        base += action
    return base


def get_status_updater_url():
    from frappe.utils.data import get_url
    return get_url("api/method/crm.integrations.websprix.handler.handle_request")


def get_websprix_settings():
    return frappe.get_single("CRM WebSprix Settings")


def validate_request():
    pass


@frappe.whitelist()
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
    call_log_id = call_payload.get("CallUUID")
    if frappe.db.exists("CRM Call Log", call_log_id):
        return frappe.get_doc("CRM Call Log", call_log_id)


def get_call_log_status(call_payload):
    status = call_payload.get("CallStatus")
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
            call_log.to = call_payload.get("To")
            call_log.duration = call_payload.get("Duration") or 0
            call_log.recording_url = call_payload.get("RecordingUrl") or ""
            call_log.start_time = call_payload.get("StartTime")
            call_log.end_time = call_payload.get("EndTime")
            if call_payload.get("AgentEmail"):
                call_log.receiver = call_payload.get("AgentEmail")
            call_log.save(ignore_permissions=True)
            frappe.db.commit()
            return call_log
    except Exception:
        frappe.log_error(title="Error while updating call record")
        frappe.db.commit()
