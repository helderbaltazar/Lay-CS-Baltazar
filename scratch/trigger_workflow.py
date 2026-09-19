import os
import requests

def trigger():
    token = os.getenv("GITHUB_TOKEN") or ""
    # I don't have GITHUB_TOKEN locally, so I can't trigger it via API.
    pass
