import pytest
from musigate.gateway.selector import Selector

def test_selector_first():
    s = Selector()
    buttons = [[{"text": "A"}], [{"text": "B"}]]
    res = s.select(buttons, strategy="first")
    assert res["text"] == "A"

def test_selector_last():
    s = Selector()
    buttons = [[{"text": "A"}], [{"text": "B"}]]
    res = s.select(buttons, strategy="last")
    assert res["text"] == "B"

def test_selector_match_title():
    s = Selector()
    buttons = [[{"text": "Numb - Linkin Park"}], [{"text": "Numb - Jay-Z"}]]
    res = s.select(buttons, strategy="match_title", query="Numb Linkin Park")
    assert res["text"] == "Numb - Linkin Park"

def test_selector_match_index():
    s = Selector()
    buttons = [[{"text": "A"}], [{"text": "B"}], [{"text": "C"}]]
    res = s.select(buttons, strategy="match_index 1")
    assert res["text"] == "B"

def test_selector_match_text_index():
    s = Selector()
    buttons = [[{"text": "1"}], [{"text": "2"}], [{"text": "3"}]]
    response_text = "1. Numb - Demo\n2. In The End - Linkin Park\n3. Faint - Linkin Park"
    res = s.select(
        buttons,
        strategy="match_text_index",
        query="In The End Linkin Park",
        response_text=response_text,
    )
    assert res["text"] == "2"
