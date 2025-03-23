import json
import os

PAGES_FILE = "pages.json"  # File to store pages data


def load_pages():
    if not os.path.exists(PAGES_FILE):
        return []  # Return an empty list if the file doesn't exist
    with open(PAGES_FILE, "r") as file:
        return json.load(file)


def save_pages(pages):
    with open(PAGES_FILE, "w") as file:
        json.dump(pages, file, indent=4)


def add_page(page):
    pages = load_pages()
    pages.append(page)
    save_pages(pages)
