# app.py
import os, tempfile, shutil, uuid, time, requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# local modules
from generator import generate_minimal_app
from github_ops import create_github_repo, push_directory_to_repo, enable_pages, clone_repo_to_tmp, update_repo_with_dir
import db

load_dotenv()

app = Flask(__name__)
db.init_db()

EXPECTED_SECRET = os.getenv("EXPECTED_SECRET", "my_expected_secret_value_123")

def post_evaluation_with_backoff(evaluation_url, payload, max_attempts=6):
    delay = 1
    headers = {"Content-Type":"application/json"}
    for attempt in range(1, max_attempts+1):
        try:
            r = requests.post(evaluation_url, json=payload, headers=headers, timeout=10)
            if r.status_code == 200:
                return True
            print(f"Eval attempt {attempt} status {r.status_code}")
        except Exception as exc:
            print("Notify error:", exc)
        time.sleep(delay)
        delay *= 2
    return False

@app.route("/api-endpoint", methods=["POST"])
def api_endpoint():
    data = request.get_json(force=True)
    print("Received:", data)

    if data.get("secret") != EXPECTED_SECRET:
        return jsonify({"error":"invalid secret"}), 403

    email = data.get("email")
    task = data.get("task")
    brief = data.get("brief","")
    round_idx = int(data.get("round",1))
    nonce = data.get("nonce")
    attachments = data.get("attachments", [])
    evaluation_url = data.get("evaluation_url")

    # immediate ack per spec
    resp = {"status":"accepted","task":task,"round":round_idx}

    try:
        if round_idx == 1:
            tmp = tempfile.mkdtemp(prefix="genapp_")
            generate_minimal_app(task, brief, attachments, tmp)

            # create repo
            repo_name = f"{task}-{uuid.uuid4().hex[:6]}"
            repo_info = create_github_repo(repo_name)
            repo_full = f"{repo_info['owner']['login']}/{repo_info['name']}"

            # push files
            commit_sha = push_directory_to_repo(tmp, repo_full)

            # enable pages
            pages_url = enable_pages(repo_full)

            # save mapping in DB
            db.save_repo_record(email, task, round_idx, nonce, repo_full, repo_info.get("html_url"), commit_sha, pages_url)

            # notify evaluator
            payload = {"email": email, "task": task, "round": round_idx, "nonce": nonce,
                       "repo_url": repo_info.get("html_url"), "commit_sha": commit_sha, "pages_url": pages_url}
            post_evaluation_with_backoff(evaluation_url, payload)

            shutil.rmtree(tmp)
            return jsonify(resp), 200

        elif round_idx == 2:
            # find existing repo by student + task
            rec = db.get_latest_repo(email, task)
            if not rec:
                return jsonify({"error":"no repo found for this email+task; round1 likely not done"}), 400

            # optional: verify nonce matches (if instructor expects same nonce)
            # if nonce != rec["nonce"]:
            #     return jsonify({"error":"nonce mismatch"}), 400

            # generate updated app (new tmp dir)
            tmp2 = tempfile.mkdtemp(prefix="updateapp_")
            generate_minimal_app(task, brief, attachments, tmp2)

            # clone existing repo
            clone_tmp = tempfile.mkdtemp(prefix="clonerepo_")
            clone_dir = clone_repo_to_tmp(rec["repo_full"], clone_tmp)

            # apply update and push
            new_sha = update_repo_with_dir(clone_dir, tmp2, commit_message="Round 2 automated update")

            # re-enable pages (optional) and get pages url from DB or API
            pages_url = enable_pages(rec["repo_full"])

            # record round2 update
            db.save_repo_record(email, task, round_idx, nonce, rec["repo_full"], rec["repo_url"], new_sha, pages_url)

            # notify evaluator
            payload = {"email": email, "task": task, "round": round_idx, "nonce": nonce,
                       "repo_url": rec["repo_url"], "commit_sha": new_sha, "pages_url": pages_url}
            post_evaluation_with_backoff(evaluation_url, payload)

            # cleanup
            shutil.rmtree(tmp2)
            shutil.rmtree(clone_tmp)
            return jsonify(resp), 200

        else:
            return jsonify({"error":"unsupported round"}), 400

    except Exception as e:
        print("Error:", e)
        return jsonify({"status":"error","message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
