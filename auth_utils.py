from dotenv import load_dotenv
import os
import secrets
import hashlib
import base64
import webbrowser
import requests

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

class PKCEManager:
    def __init__(self):
        self.code_verifier = None
        self.code_challenge = None

    def generate_pkce(self):
        """Generate a PKCE code_verifier and code_challenge"""
        self.code_verifier = secrets.token_urlsafe(64)[:128]  # Max 128 characters
        hashed = hashlib.sha256(self.code_verifier.encode()).digest()
        self.code_challenge = base64.urlsafe_b64encode(hashed).decode().rstrip("=")  # Remove padding

def twitter_auth(pkce_obj):
    SCOPES = "tweet.write+tweet.read+users.read+media.write+offline.access"  # Adjust as needed

    code_challenge = pkce_obj.code_challenge

    auth_url = (
        f"https://twitter.com/i/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
        f"&scope={SCOPES}"
        f"&state=random_string"
    )

    webbrowser.open(auth_url)
    print(f"Go to this URL and authorize: {auth_url}")

def twitter_token(pkce_obj):
    CODE = input("Enter the code from Twitter: ")  # Paste the code from Twitter

    # Encode CLIENT_ID and CLIENT_SECRET in Base64
    client_creds = f"{CLIENT_ID}:{CLIENT_SECRET}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()

    payload = {
        "grant_type": "authorization_code",
        "code": CODE,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": pkce_obj.code_verifier
    }

    headers = {
        "Authorization": f"Basic {client_creds_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(TOKEN_URL, data=payload, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        ACCESS_TOKEN = token_data["access_token"]
        REFRESH_TOKEN = token_data.get("refresh_token")  # Save this for later
        return ACCESS_TOKEN,REFRESH_TOKEN
    else:
        
        print("Error getting token:", response.json())

def refresh_access_token(refresh_token):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        new_access_token = response.json().get('access_token')
        new_refresh_token = response.json().get('refresh_token')  # Optional
        print("Access token refreshed successfully.")
        return new_access_token, new_refresh_token
    else:
        print("Failed to refresh access token:", response.json())
        return None, None