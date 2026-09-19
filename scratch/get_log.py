import requests
import json

def get_log():
    # To get logs without auth, we might not be able to if the repo disables public logs, but it's public.
    # Actually, fetching logs via API requires auth for actions. Let's try.
    url = "https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/jobs/35337417475/logs"
    # Actually we need the job id. Let's get the job id first.
    jobs_url = "https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/runs/35337417475/jobs"
    resp = requests.get(jobs_url).json()
    job_id = resp["jobs"][0]["id"]
    
    log_url = f"https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/jobs/{job_id}/logs"
    # Note: public repos allow log downloads.
    log_resp = requests.get(log_url)
    if log_resp.status_code == 200:
        print(log_resp.text[-2000:])
    else:
        print("Failed to get log:", log_resp.status_code)

if __name__ == "__main__":
    get_log()
