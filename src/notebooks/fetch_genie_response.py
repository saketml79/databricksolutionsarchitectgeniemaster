# Databricks notebook source
import json
import time

from databricks.sdk import WorkspaceClient

dbutils.widgets.text("space_id", "")
dbutils.widgets.text("message", "")
dbutils.widgets.text("conversation_id", "")
dbutils.widgets.text("message_id", "")

space_id = dbutils.widgets.get("space_id").strip()
message = dbutils.widgets.get("message").strip()
conversation_id = dbutils.widgets.get("conversation_id").strip()
message_id = dbutils.widgets.get("message_id").strip()

if not space_id or (not message and not (conversation_id and message_id)):
    raise ValueError("space_id and either message or both conversation_id and message_id are required")

workspace = WorkspaceClient()
if conversation_id and message_id:
    message_path = f"/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}"
elif conversation_id:
    start_path = f"/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages"
    started = workspace.api_client.do("POST", start_path, body={"content": message})
    message_id = started["message_id"]
    message_path = f"/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}"
else:
    started = workspace.api_client.do("POST", f"/api/2.0/genie/spaces/{space_id}/start-conversation", body={"content": message})
    conversation_id = started["conversation_id"]
    message_id = started["message_id"]
    message_path = f"/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}"

for _ in range(120):
    message_result = workspace.api_client.do("GET", message_path)
    status = message_result.get("status")
    if status == "COMPLETED":
        break
    if status in {"FAILED", "CANCELLED"}:
        raise RuntimeError(json.dumps(message_result.get("error") or {"status": status}))
    time.sleep(1)
else:
    raise TimeoutError("The deployed Genie space did not complete within 120 seconds")

content = "\n\n".join(
    attachment.get("text", {}).get("content", "")
    for attachment in message_result.get("attachments", [])
    if attachment.get("text", {}).get("content")
).strip() or message_result.get("content", "")

if not content:
    raise RuntimeError("The deployed Genie space completed without a text response")

dbutils.notebook.exit(json.dumps({
    "content": content,
    "conversation_id": conversation_id,
    "message_id": message_id,
    "space_id": space_id,
}))