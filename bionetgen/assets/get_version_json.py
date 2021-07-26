import time, json, urllib, sys
import urllib.request

# GH API has rate exceeded issues if more than 60
# within an hour. To avoid this entirely, we'll
# download and save the JSON and have setup.py
# work on that instead

# let's pull URLs for each distribution
# in the latest distribution
rls_url = "https://api.github.com/repos/RuleWorld/bionetgen/releases/latest"
# sometimes we exceed the rate, we want to
# ensure this doesn't happen, but we also
# _must_ get the response. We'll slap it into
# a loop and break if need be
ctr = 0
while ctr < 100:
    ctr += 1
    try:
        time.sleep(5)
        rls_resp = urllib.request.urlopen(rls_url)
        print(f"success: {ctr}")
        break
    except urllib.error.HTTPError:
        time.sleep(5)
        print(f"failed: {ctr}")
if ctr >= 100:
    print("Connection to GitHub couldn't be established, quitting")
    sys.exit(1)
rls_json_txt = rls_resp.read()
rls_json = json.loads(rls_json_txt)

with open("ghapi.json", "w") as f:
    json.dump(rls_json, f)
