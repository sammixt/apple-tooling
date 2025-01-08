import os
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Google OAuth flow
flow = Flow.from_client_config(
    client_config={
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "project_id": "turing-dev",  # Replace with your actual project ID
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": [GOOGLE_REDIRECT_URI],
        }
    },
    scopes=[
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_uri=GOOGLE_REDIRECT_URI,
)

def get_google_auth_url():
    """Generate the Google OAuth URL."""
    auth_url, _ = flow.authorization_url(prompt="consent")
    return auth_url

def get_google_user_info(code: str):
    """Fetch user info from Google after successful OAuth."""
    flow.fetch_token(code=code)
    credentials = flow.credentials
    idinfo = id_token.verify_oauth2_token(
        credentials.id_token,
        Request(),
        audience=GOOGLE_CLIENT_ID,
    )
    return {
        "id": idinfo["sub"],
        "email": idinfo["email"],
        "name": idinfo.get("name", ""),
        "picture": idinfo.get("picture", ""),
    }
