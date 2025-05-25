import unittest
from unittest.mock import Mock, patch

from crm.fcrm.doctype.crm_websprix_settings.crm_websprix_settings import CRMWebsprixSettings


class TestCRMWebsprixSettings(unittest.TestCase):
    def test_verify_credentials_when_enabled_valid(self):
        doc = CRMWebsprixSettings(enabled=True, account_id="acc", client_id="cid", client_secret="secret")
        with patch("crm.fcrm.doctype.crm_websprix_settings.crm_websprix_settings.requests.get") as mock_get:
            mock_get.return_value = Mock(status_code=200)
            doc.verify_credentials()
            mock_get.assert_called_once_with(
                "https://api.websprix.com/v1/accounts/acc",
                auth=("cid", "secret"),
            )

    def test_verify_credentials_when_enabled_invalid(self):
        doc = CRMWebsprixSettings(enabled=True, account_id="acc", client_id="cid", client_secret="secret")
        with patch("crm.fcrm.doctype.crm_websprix_settings.crm_websprix_settings.requests.get") as mock_get:
            mock_get.return_value = Mock(status_code=401, reason="Unauthorized")
            with self.assertRaises(Exception):
                doc.verify_credentials()
            mock_get.assert_called_once()

    def test_verify_credentials_disabled_no_call(self):
        doc = CRMWebsprixSettings(enabled=False, account_id="acc", client_id="cid", client_secret="secret")
        with patch("crm.fcrm.doctype.crm_websprix_settings.crm_websprix_settings.requests.get") as mock_get:
            doc.verify_credentials()
            mock_get.assert_not_called()

    def test_validate_calls_verify(self):
        doc = CRMWebsprixSettings(enabled=True, account_id="acc", client_id="cid", client_secret="secret")
        with patch.object(doc, "verify_credentials") as mock_verify:
            doc.validate()
            mock_verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
