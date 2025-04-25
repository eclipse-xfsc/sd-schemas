
import requests
import subprocess
import zipfile
import re

# Reference for tagged versions: "ref" doesn't contain "/" and "source" == "push" and "status" == "success"

# 1. Download old artifacts
# 2. Write them into the correspoding folder structure
#
# - public
#   - version1
#   - version2
#   ...
#   - versionx
#   - versionlatest (already created)
#   index.html <-- contains redirect

PROJECT_ID = ""
ACCESS_TOKEN = ""

tag_pipeline_list = []
pipeline_list = []

tag_list = []

# Get all tags
resp = requests.get(
    f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/repository/tags",
    headers={"PRIVATE-TOKEN": ACCESS_TOKEN}
)
tags = resp.json()
for t in tags:
    tag_list += [t["name"]]

# Get all pipelines
i = 1
while True:
    resp = requests.get(
            f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/pipelines?page={i}&per_page=100",
            headers={"PRIVATE-TOKEN": ACCESS_TOKEN}
        )
    json = resp.json()
    if len(json) == 0:
        break
    else:
        pipeline_list += json
        if len(json) < 100:
            break
    i += 1

# Filter the pipeline list by the Tag list and if it was successful
for ppl in pipeline_list:
    if ppl["ref"] in tag_list and \
       ppl["source"] == "push" and \
       ppl["status"] == "success":
        tag_pipeline_list.append(ppl)

# We only use the first pipeline of this list
tp = tag_pipeline_list[0]
resp = requests.get(
    f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/pipelines/{tp['id']}/jobs",
    headers={"PRIVATE-TOKEN": ACCESS_TOKEN}
)
jobs = resp.json()
job = None
for j in jobs:
    if j["name"] == "generate-html":
        job = j
        break
if job is None:
    print("There wasn't a job with the correct name in the tagged pipeline.")

process = subprocess.Popen(['curl', '-o', f'{tp["ref"]}.tmp', '--header', f'"PRIVATE-TOKEN: {ACCESS_TOKEN}"',
                            f'https://gitlab.com/api/v4/projects/{PROJECT_ID}/jobs/{job["id"]}/artifacts'])
stdout, stderr = process.communicate()

URL = ""
with open( tp["ref"] + ".tmp", "r") as f:
    tmp = f.read()
    match = re.search("(?P<url>https?://[^\s]+)", tmp)
    if match is not None:
        URL = match.group("url")
        URL = URL.strip('"').strip("'").strip(".")
    b = 1

# resp = requests.get(
#     f"https://gitlab.com/api/v4/projects/{PROJECT_ID}/jobs/{job['id']}/artifacts",
#     headers={"PRIVATE-TOKEN": ACCESS_TOKEN}
# )
# with open( tp["ref"] + ".zip", "w") as f:
#     f.write(resp.text)

process = subprocess.Popen(['curl', '-o', f'{tp["ref"]}.zip', #'--header', f'"PRIVATE-TOKEN: {ACCESS_TOKEN}"',
                            f"{URL}"])
stdout, stderr = process.communicate()


with zipfile.ZipFile(f'{tp["ref"]}.zip', 'r') as zip_f:
    zip_f.extractall(".")

# !!! IMPORTANT INCREASE EXPIRE IN TIME OF ARTIFACTS !!!

# Developement on this script is stalled, but I think it could be used again in the future,
# since the variant of storing a zip in public folder has some problems