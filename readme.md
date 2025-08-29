# PhishNet — Quick Start (Backend + Frontend)

> **First do this:** create a `.env` file in **`/Backend`** *before* installing anything.
>
> ```ini
> # /Backend/.env
> OPENAI_API_KEY=YOUR_OPENAI_API_KEY_HERE
> ```

---

## Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**
- Two terminals (run backend and frontend separately)

---

## 1) Backend (Django)

```bash
cd Backend

# Install dependencies
pip install -r requirements.txt

# Run the server
python manage.py runserver 0.0.0.0:8000
```
The API will be available at **http://localhost:8000/api/**.

---

## 2) Frontend (React)

Open a new terminal:

```bash
cd Frontend
npm install
```

Run the dev server:
```bash
npm run dev
```
Open the printed URL (commonly **http://localhost:3000**).

> Optional build:
```bash
npm run build
npm run preview
```

---

## 3) Using the App
- **Demo**: sends 3 sample emails to `/api/processEmail` and renders the results.
- **Compose** (to the right of Demo): opens a modal; on **Send** it POSTs your custom email to the same endpoint and appends the analyzed result to the inbox.

---