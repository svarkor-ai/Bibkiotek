"""Bibliotek — FastAPI entry point."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Bibliotek", version="0.1.0")

# TODO: wire routers, static files, templates
# TODO: startup: create tables, seed admin
