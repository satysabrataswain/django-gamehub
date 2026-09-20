# GameHub frontend pack

This frontend is designed for the existing Django GameHub API.

## Copy / replace these paths

- Replace: `config/urls.py`
- Add: `games/templates/games/index.html`
- Add: `games/static/games/gamehub.css`
- Add: `games/static/games/gamehub.js`

No Node.js, React, npm, or CORS package is required.

## Run

From the project folder with the virtual environment active:

```bat
python manage.py check
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

## Features

- Register and login with JWT
- Automatic JWT refresh where supported
- Tic-Tac-Toe vs computer
- Tic-Tac-Toe PVP rooms
- Bingo vs computer
- Bingo PVP rooms
- Waiting-room browser
- Recent-games list
- Live PVP polling
- Responsive phone/desktop design

## Expected API routes

Games:
- `GET/POST /api/games/`
- `GET /api/games/waiting/`
- `GET /api/games/<id>/`
- `POST /api/games/<id>/join/`
- `POST /api/games/<id>/move/`

Auth:
The frontend automatically tries common routes below so it can work with
slightly different account URL configurations.

Login:
- `/api/auth/token/`
- `/api/auth/login/`
- `/api/token/`

Register:
- `/api/auth/register/`
- `/api/accounts/register/`
- `/api/register/`

Refresh:
- `/api/auth/token/refresh/`
- `/api/auth/refresh/`
- `/api/token/refresh/`

## Important

Use the security / Bingo backend fixes from the previous pack as well,
especially the Bingo serializer change that hides the opponent board.
