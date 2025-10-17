# quick_test.py
from github_ops import create_github_repo, push_directory_to_repo, enable_pages
import os, sys

local_dir = "/tmp/demo_app"   # change to your demo path
if not os.path.isdir(local_dir):
    print("Local dir not found:", local_dir); sys.exit(1)

repo_info = create_github_repo("test-deploy-xyz1")
repo_full = f"{repo_info['owner']['login']}/{repo_info['name']}"
sha = push_directory_to_repo(local_dir, repo_full)
pages = enable_pages(repo_full)
print("github:", repo_info["html_url"])
print("commit:", sha)
print("pages:", pages)
