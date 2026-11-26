## Installation instructions

```bash
git clone https://github.com/unnamant/cybersecuritybase.git
```
```bash
cd cybersecuritybase/mysite
```
```bash
python3 -m venv venv
```
```bash
source venv/bin/activate
```
```bash
pip install -r requirements.txt
```
```bash
python manage.py migrate
```
```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/polls/ and sign up to create a user.

## Features

With this poll application, users can:

- Sign up
- Log in and log out
- Create polls
- Vote
- See their own polls
- Delete their own polls
- Search polls
