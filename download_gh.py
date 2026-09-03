import urllib.request
import tarfile
import io

url = "https://github.com/cli/cli/releases/download/v2.54.0/gh_2.54.0_macOS_amd64.tar.gz"
response = urllib.request.urlopen(url)
tar = tarfile.open(fileobj=io.BytesIO(response.read()), mode="r:gz")
tar.extractall()
tar.close()
print("Extracted!")
