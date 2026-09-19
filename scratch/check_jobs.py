import requests
import os
import json

def get_jobs():
    url = "https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/runs/35337417475/jobs"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        for job in data.get("jobs", []):
            print(f"Job: {job['name']} | Status: {job['status']} | Conclusion: {job['conclusion']}")
            for step in job.get("steps", []):
                if step["conclusion"] == "failure":
                    print(f"  -> Failed Step: {step['name']}")
    else:
        print(f"Error {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    get_jobs()
