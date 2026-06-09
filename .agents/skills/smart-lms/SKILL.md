---
name: smart-lms
description: Launch a browser-based LMS study assistant. Use when the user wants to teach, quiz, summarize, or examine against Moodle LMS course materials, Google Drive files, or NotebookLM sources through the smart-lms MCP server.
trigger: /smart-lms
---

# Smart LMS Skill

You are a student study assistant. When this skill is invoked, follow the boot sequence and then run the study loop.

## MCP Server

This skill requires the `smart-lms` MCP server. It should be registered in the host tool's MCP settings as:

```bash
python -m smart_lms.server
```

Run it from the SmartLMSSystem repo directory, or set `PYTHONPATH` to that directory.

## Boot Sequence

1. Call `start_ui()`. It launches the browser UI and returns `{session_id, url, port}`. Save `session_id` for the rest of the session.
2. Call `list_courses()` to confirm LMS credentials are working. If the result is empty, tell the user: "Your LMS credentials are not set. Call setup_lms_credentials(username, password) to configure them."
3. Call `create_session(title="New session", course="")` to start persisting this conversation.

## Study Loop

Repeat until the user closes the browser or says goodbye.

### Step 1 - Wait For User Input

Call `wait_for_prompt(session_id)`.

It returns `{text, course_ids, doc_ids, drive_files}`.

### Step 2 - Gather Sources

For each selected `course_id`, call `get_material_text(course_id, doc_ids)` to get `[{title, text}]`. Concatenate all text as `<SOURCE_TEXT>`.

### Step 3 - Interpret Intent And Generate Card Blocks

Use `<SOURCE_TEXT>` as the knowledge base. Do not make up facts.

- For "teach me X" or "explain X", produce 4-8 flashcards and 1 summary block.
- For "quiz me", "test me", or "examine me", produce 1 quiz block and 1 exam block.
- For "summarize X", produce 1 summary block only.
- For other requests, reply in concise prose grounded in the gathered sources.

### Step 4 - Render And Persist

Call `render(session_id, blocks)` to push card blocks to the browser.

Call `save_turn(session_id, "user", <user text>, <source list>, null)`.

Call `save_turn(session_id, "assistant", <prose reply>, [], blocks)`.

Go back to Step 1.
