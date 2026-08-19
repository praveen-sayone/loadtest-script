# Loadtest Script (Locust)

Quick guide to run the locust web UI and configure requests.

1. Create and activate your Python virtual environment (adjust the path as needed):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install Locust if you haven't already:

```bash
pip install locust
```

3. Start Locust from this folder (it will look for `locustfile.py`):

```bash
locust
```

4. Open the web UI in your browser:

```
http://localhost:8089
```

5. Usage notes:

- Enter the target `Host` in the web UI (for example `https://example.com`).
- To configure HTTP method, request path, headers, URL parameters, and JSON body,
    click the **Request Config** button in the Locust web UI header. A modal will open with fields for:
    method, path, headers (editable key/value rows), URL parameters (key/value
    rows), and a JSON body editor. Click Save to write the configuration.

- Persisted configuration: the saved request configuration is written to
    `locust_config.json` in this folder. Settings are saved immediately and will
    be loaded when you start Locust next time. To reset to defaults, stop Locust
    and delete `locust_config.json`.

- Developer endpoints: the web UI uses two JSON endpoints exposed by the
    running Locust process:
    - `/_custom_config`  (POST) — save a configuration payload (used by the modal)
    - `/_custom_config_state`  (GET) — return the current configuration as JSON

- Manual edits: you can edit `locust_config.json` directly; it uses the shape
    {"method":"GET","path":"/","headers":{...},"params":{...},"json":null}.
- Set the number of users and spawn rate in the main web UI and click Start.

Example: to POST JSON to `/api/items` set:

- Method: `POST`
- Path: `/api/items`
- Headers (JSON): `{ "Content-Type": "application/json" }`
- JSON Body: `{ "name": "test", "qty": 3 }`

That's it — the `WebsiteUser` will perform the configured request repeatedly,
with a random wait between 1 and 3 seconds between requests.
