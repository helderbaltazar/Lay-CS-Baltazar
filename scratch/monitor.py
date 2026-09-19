import requests
import time
import zipfile
import io

def get_latest_run():
    url = "https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/runs"
    resp = requests.get(url, params={"branch": "main", "event": "push", "per_page": 1}).json()
    return resp["workflow_runs"][0] if resp.get("workflow_runs") else None

def get_artifacts(run_id):
    url = f"https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/runs/{run_id}/artifacts"
    return requests.get(url).json().get("artifacts", [])

def main():
    run = get_latest_run()
    if not run: return
    run_id = run["id"]
    print(f"Monitoring Run {run_id}")
    while True:
        r = requests.get(f"https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/runs/{run_id}").json()
        status = r["status"]
        if status == "completed":
            print(f"Finished with conclusion: {r['conclusion']}")
            break
        print(f"Status: {status}...")
        time.sleep(10)
    
    if r['conclusion'] == "failure":
        artifacts = get_artifacts(run_id)
        for a in artifacts:
            if "pytest" in a["name"]:
                print(f"Artifact found: {a['name']}")
                # We can't download artifact without auth if it's GitHub Actions artifact API.
                print(f"Artifact URL: {a['archive_download_url']}")
main()
