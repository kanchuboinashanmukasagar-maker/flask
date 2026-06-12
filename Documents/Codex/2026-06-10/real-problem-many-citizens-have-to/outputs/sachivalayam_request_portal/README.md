# Sachivalayam Request Portal

A Flask website for registering citizen applications and complaints, generating a unique tracking ID, showing assigned officers, tracking missing documents, and helping officials manage pending and completed work.

## Run

```powershell
python -m pip install -r requirements.txt
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

If your system does not have `python` on PATH, use the Python executable installed on your machine in place of `python`.

## Pages

- `/` - citizen overview
- `/register` - submit a new request or complaint
- `/track` - track by application or complaint ID
- `/officer/login` - Sachivalayam officer login
- `/dashboard` - officer dashboard with search and filters
- `/request/<tracking_id>` - officer-only status, officer, and document updates

## Demo Officer Login

```text
Username: officer
Password: sachivalayam123
```
