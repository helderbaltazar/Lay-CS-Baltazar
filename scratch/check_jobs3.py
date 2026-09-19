import requests
def get_jobs():
    url = "https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/runs/35338583815/jobs"
    resp = requests.get(url).json()
    for job in resp.get("jobs", []):
        for step in job.get("steps", []):
            if step["conclusion"] == "failure":
                print(f"Failed Step: {step['name']}")
if __name__ == "__main__":
    get_jobs()
