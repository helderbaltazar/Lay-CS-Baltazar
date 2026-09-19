import requests
import os
import json

def get_runs():
    url = "https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/runs"
    # Try to use a github token if available, but public repos might not need it, though rate limits apply.
    # We can also just fetch the first page.
    resp = requests.get(url, params={"branch": "main", "event": "push", "per_page": 1})
    if resp.status_code == 200:
        data = resp.json()
        runs = data.get("workflow_runs", [])
        if runs:
            run = runs[0]
            print(f"Run ID: {run['id']}")
            print(f"Name: {run['name']}")
            print(f"Status: {run['status']}")
            print(f"Conclusion: {run['conclusion']}")
            print(f"URL: {run['html_url']}")
            print(f"Created At: {run['created_at']}")
        else:
            print("No runs found.")
    else:
        print(f"Error {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    get_runs()
