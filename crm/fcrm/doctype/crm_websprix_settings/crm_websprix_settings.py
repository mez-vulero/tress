try:
    import requests
except Exception:  # pragma: no cover - library is optional in test env
    class requests:  # type: ignore
        """Fallback requests stub so tests can patch `requests.get`."""

        def get(*args, **kwargs):  # pragma: no cover - should be patched in tests
            raise NotImplementedError

class CRMWebsprixSettings:
    """Simplified WebSprix settings doctype for testing."""

    def __init__(self, *, enabled=False, account_id="", client_id="", client_secret="", base_url="https://api.websprix.com"):
        self.enabled = enabled
        self.account_id = account_id
        self.client_id = client_id
        self._client_secret = client_secret
        self.base_url = base_url

    def get_password(self, fieldname: str):
        if fieldname == "client_secret":
            return self._client_secret
        return None

    def verify_credentials(self) -> None:
        """Validate credentials by making a basic API request."""
        if not self.enabled:
            return

        response = requests.get(
            f"{self.base_url}/v1/accounts/{self.account_id}",
            auth=(self.client_id, self.get_password("client_secret")),
        )
        if response.status_code != 200:
            raise Exception(f"Invalid credentials: {response.reason}")

    def validate(self) -> None:
        self.verify_credentials()
