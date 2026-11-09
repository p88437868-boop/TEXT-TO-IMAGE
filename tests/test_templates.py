from __future__ import annotations

from pathlib import Path

import pytest

from textpic.services.database import Database
from textpic.services.template_repo import TemplateRepository
from textpic.ui.dialogs import fill_placeholders, placeholder_keys


def test_placeholder_helpers() -> None:
    body = "Hi {name}, the {product} is {price}. Thanks {name}!"
    assert placeholder_keys(body) == ["name", "product", "price"]
    assert (
        fill_placeholders(body, {"name": "Maya", "product": "Pro plan"})
        == "Hi Maya, the Pro plan is {price}. Thanks Maya!"
    )


def test_seed_and_crud(tmp_path: Path) -> None:
    database = Database(tmp_path / "templates.db")
    templates = TemplateRepository(database)
    try:
        templates.seed_defaults()
        assert templates.count() == 6
        with pytest.raises(ValueError):
            templates.create("Duplicate", "Text", "Ctrl+Alt+1")
        created = templates.create("Greeting", "Hello {name}", None)
        updated = templates.update(
            created.id, "Greeting 2", "Hello {name}!", "Ctrl+Alt+7"
        )
        assert updated.title == "Greeting 2"
        assert updated.hotkey == "Ctrl+Alt+7"
        templates.delete(created.id)
        assert templates.get(created.id) is None
    finally:
        database.close()
