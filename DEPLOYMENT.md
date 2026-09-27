# ParkSmart Deployment

## Architecture

- Source control: GitHub repositories `Abh234/smart-parking-system` (full project) and `Abh234/smart-parking-system-backend` (backend-only).
- Frontend: static hosting such as Netlify. Publish the `frontend/` directory; no build command is needed.
- API: Render Web Service, using `backend/` as the root directory and Gunicorn as the WSGI server.
- Database: managed MySQL with a network endpoint reachable from Render.

## Current deployment

- Frontend: https://neon-gingersnap-8f54e4.netlify.app/
- API: https://smart-parking-system-backend-uudr.onrender.com
- API health check: https://smart-parking-system-backend-uudr.onrender.com/test
- Render is configured to allow requests from the Netlify origin above.
- The API service is live, but no MySQL connection is configured yet. Database-backed endpoints currently return a database connection error until `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` are set in Render and the schema is imported into that MySQL database.
- Netlify was deployed with Netlify Drop, so it is not connected to GitHub for automatic deploys. Upload the `frontend/` folder again after frontend changes, or connect the site to the GitHub repository in Netlify for continuous deployment.

## Before deployment

1. Create an empty MySQL database named `parksmart` on your database provider.
2. Import `Database/schema.sql` into that database. This file contains schema only. The existing `parksmart_*.sql` exports contain personal records and plaintext passwords and are intentionally excluded from Git. Do not use or upload those exports to a public repository.
3. Use a dedicated database account with only the permissions the app needs. Store credentials as Render environment variables, never in source files.
4. This app is not safe for real users or payments yet. It stores passwords in plaintext, does not consistently authenticate/authorize API requests, and the manual UPI confirmation route records payment as paid based on a browser request. Keep any deployment private/test-only until those issues are fixed; do not accept real payments or personal data.

## Push the full project to GitHub

The project folder is not currently a Git working tree. Clone the existing destination first so its current history is preserved:

```powershell
git clone https://github.com/Abh234/smart-parking-system.git
```

Copy the project files into the cloned folder, excluding its `.git` directory. Review `git status`, then:

```powershell
git add .
git status --short
git diff --cached --check
git commit -m "Deploy ParkSmart full project"
git push origin main
```

Do not stage `.env` files or the `Database/parksmart_*.sql` exports. The root `.gitignore` excludes them; verify the staged file list before committing.

## Push the backend-only repository

Clone the existing backend destination to preserve its history:

```powershell
git clone https://github.com/Abh234/smart-parking-system-backend.git
```

Copy the contents of this project's `backend/` directory into that clone, excluding `.env`, `__pycache__/`, and `.pyc` files. Copy `Database/schema.sql` to a `Database/` subdirectory in the backend repository so its database setup remains documented. Review and push:

```powershell
git add .
git status --short
git diff --cached --check
git commit -m "Deploy ParkSmart Flask API"
git push origin main
```

The GitHub repositories already have a `main` branch. Never use `--force` for these pushes.

## Deploy the API on Render

1. In Render, create a Web Service from `Abh234/smart-parking-system` (or use the backend-only repository).
2. For the full-project repository set **Root Directory** to `backend`; for the backend-only repository leave it as `.`.
3. Set **Build Command** to `pip install -r requirements.txt`.
4. Set **Start Command** to `gunicorn --bind 0.0.0.0:$PORT app:app`.
5. Add these environment variables in the Render service settings:

   ```text
   DB_HOST=<managed MySQL hostname>
   DB_USER=<database username>
   DB_PASSWORD=<database password>
   DB_NAME=parksmart
   FRONTEND_ORIGIN=<deployed frontend origin>
   ```

   Set `FRONTEND_ORIGIN` to the exact origin only, for example `https://your-site.netlify.app` (no path). Render supplies `PORT`; do not hard-code it. The current app does not use Razorpay credentials, despite old documentation claiming otherwise.
6. Deploy and open `https://<render-service>.onrender.com/test`. It should return `API WORKING`. Check `/` for `ParkSmart Backend Running`.

## Deploy the frontend on Netlify

1. Create a site from the full-project GitHub repository.
2. Set the **Base directory** to `frontend`, leave the build command empty, and set the **Publish directory** to `.`.
3. Before deploying, update `frontend/api-config.js` to the Render service URL:

   ```js
   window.PARKSMART_API_BASE = "https://<render-service>.onrender.com";
   ```

4. Commit and push the URL change to GitHub, then trigger/retry the Netlify deployment.
5. Update Render's `FRONTEND_ORIGIN` to the final Netlify URL and redeploy the API.

The shared API config is used by the UI pages that call the backend, so the hosted URL is changed in one place. For local development set it back to `http://127.0.0.1:5000`.

## Local smoke test

From the repository root, in two PowerShell terminals:

```powershell
# Terminal 1
$env:DB_HOST = "127.0.0.1"
$env:DB_USER = "your_mysql_user"
$env:DB_PASSWORD = "your_mysql_password"
$env:DB_NAME = "parksmart"
Set-Location backend
python -m pip install -r requirements.txt
python app.py
```

```powershell
# Terminal 2
Set-Location frontend
python -m http.server 8080
```

Open `http://127.0.0.1:8080` for the frontend and `http://127.0.0.1:5000/test` for the API. Database-backed features require a reachable MySQL instance with `Database/schema.sql` imported. A successful `/test` response only confirms the web process is up, not that MySQL is configured.

## Known incomplete frontend flows

The Contact and forgot-password pages call `/api/contact` and `/api/reset-password`, which are not implemented in the current Flask app. They will not work until those routes are implemented. Do not advertise these features as operational.
