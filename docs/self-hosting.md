# Self-hosting SideTrack

[Back to the user guide](../README.md)

## Run on your own computer

You need to install SideTrack only if you want to run your own copy. To use the hosted website, follow the [user guide](../README.md).

You need **Python 3.12**, [Git](https://git-scm.com/downloads), and an internet connection. Check Python with `python3.12 --version` on macOS/Linux or `py -3.12 --version` on Windows. Install Python 3.12 if that command is unavailable.

The commands below download SideTrack into your home folder and create a separate Python environment called `.venv`. Already cloned it? Open the existing project folder and start at the `venv` command.

### macOS or Linux — Terminal

```sh
cd ~
git clone https://github.com/IcebergSnow/SideTrack.git
cd SideTrack
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m sidetrack
```

### Windows — Command Prompt

Open **Command Prompt** from the Start menu and run:

```bat
cd /d "%USERPROFILE%"
git clone https://github.com/IcebergSnow/SideTrack.git
cd SideTrack
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m sidetrack
```

### Open the app

Keep the terminal running and open **[http://localhost:8000](http://localhost:8000)** in your browser. You should see SideTrack's URL field and **Generate** button. Try the example song from [First use](../README.md#try-it-with-one-song).

**No `.env` file, API key, Google credentials, Node.js, or frontend build is required to run SideTrack.** [`.env.example`](../.env.example) documents this. Google setup is only needed if you separately choose the CLI importer.

Press **Ctrl+C** in the terminal to stop the local server. To start again later, open the project folder, activate `.venv` with the command for your operating system, and run `python -m sidetrack`.

## Deploy your own copy on Vercel

Use this if you want your own public URL. You need GitHub and Vercel accounts; you do not need to configure Google OAuth for the SideTrack website.

1. **Fork this repository** into your GitHub account using GitHub's **Fork** button. A fork is your own copy that Vercel can deploy.
2. Sign in to [Vercel](https://vercel.com/new) with GitHub. Choose **Add New → Project** and import your SideTrack fork. If it is missing, grant the Vercel GitHub integration access to that repository.
3. Check these settings:

   | Setting | Value |
   | --- | --- |
   | Framework Preset | **FastAPI** |
   | Root Directory | Repository root (`./`) |
   | Build Command | Leave the override off |
   | Output Directory | Leave the override off |
   | Install Command | Leave the override off |
   | Environment Variables | None |

4. Click **Deploy** and wait for it to finish. The repository includes the Python version, dependencies, and FastAPI entrypoint Vercel needs. You do not need to enter a server start command or a `dist` folder.
5. Open the production `.vercel.app` URL. Generate recommendations from the example song, browse to another page, and download a CSV. A successful build alone does not confirm that recommendations work from Vercel.
6. Future pushes to the connected production branch, usually `main`, redeploy your copy.

Deployment follows Vercel's [FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi) and [Python runtime documentation](https://vercel.com/docs/functions/runtimes/python). Hosting usage is subject to your Vercel plan's limits.

If the page loads but recommendations fail, open the Vercel deployment's **Logs** and reproduce the request. YouTube Music can block, throttle, or change the unofficial endpoint. A song working locally does not guarantee it will work from a hosting provider's IP address.

### Optional: enable visitor analytics

The repository already includes Vercel's plain-HTML analytics integration.

1. Open your Vercel project's **Analytics** tab and click **Enable** if needed.
2. Redeploy the project, visit its production URL, then check the dashboard.
3. If Vercel shows framework setup instructions, choose **HTML**. You do not need to add a React component or npm package.

See [Vercel's analytics setup guide](https://vercel.com/docs/analytics/quickstart). Analytics is skipped on localhost, and blockers can prevent visits from appearing. SideTrack adds no custom song or download events; [see the privacy notes](../README.md#privacy-and-limitations).

## Update a local copy

To update a Git checkout, stop the local server, open the repository folder, activate `.venv`, and run:

```sh
git pull --ff-only
python -m pip install -r requirements.txt
python -m sidetrack
```

## Troubleshooting

| What happens | What to try |
| --- | --- |
| The local page will not open | Keep `python -m sidetrack` running and use `http://localhost:8000`, not an HTML file opened directly from disk. Check the terminal for errors. |
| `python3.12`, `py -3.12`, or `git` is not found | Install the missing prerequisite, reopen the terminal, and check its version. |
| Python says `No module named sidetrack` or a dependency is missing | Open the SideTrack project folder, activate `.venv`, and run `python -m pip install -r requirements.txt` before starting it. |
| PowerShell blocks environment activation | Use **Command Prompt** with the Windows instructions, or run `.\.venv\Scripts\python.exe -m sidetrack` from the project folder after installing the dependencies into that environment. |
| Port 8000 is already in use | Stop the other local server if it is yours, or run `python -m uvicorn sidetrack.app:app --host 127.0.0.1 --port 8001` and open `http://localhost:8001`. |
| Vercel's build fails | Check the build logs, select **FastAPI**, and use the repository root. Leave build/output/install overrides off. |
| A Vercel link asks me to sign in | You may be using a protected preview deployment. Use your public production URL when sharing the app, or check the project's deployment-protection settings. |
