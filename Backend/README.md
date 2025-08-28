
# Ultra-Minimal Django API

**No security, no storage, no templates.** Just one middleware and one endpoint.

## Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

## Try it
```bash
curl -i http://localhost:8000/api/ping/
```
You should see a JSON body:
```json
{"status":"ok","note":"processed-by-middleware"}
```
and a response header:
```
X-Example: demo
```
