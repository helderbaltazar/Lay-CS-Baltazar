import requests
import zipfile
import io

# We need the job log. 
# Job ID: 98584819458
# Wait, GitHub actions logs require a token to download the zip, or we can just fetch the raw job logs if public?
# The URL for raw job log: https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/jobs/98584819458/logs
r = requests.get("https://api.github.com/repos/helderbaltazar/Lay-CS-Baltazar/actions/jobs/98584819458/logs")
if r.status_code == 200:
    with open("job_log.txt", "w") as f:
        f.write(r.text)
    print("Logs fetched successfully.")
else:
    print(f"Failed: {r.status_code} {r.text}")
