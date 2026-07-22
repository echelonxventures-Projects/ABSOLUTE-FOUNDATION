"""Tests for engine.knowledge.store — KnowledgeBase + KnowledgeStore (Part 04/13)."""

from __future__ import annotations

import json

import pytest

from engine.knowledge.errors import (
    DuplicateKnowledgeError,
    KnowledgeNotFoundError,
    KnowledgeSourceError,
)
from engine.knowledge.model import KnowledgeAuthority, KnowledgeKind, Lifecycle
from engine.knowledge.store import (
    CANON_FILE,
    DECISIONS_FILE,
    KnowledgeBase,
    KnowledgeStore,
    default_store_dir,
)

from .conftest import make_cko, make_decision


def test_base_rejects_duplicate_ids():
    with pytest.raises(DuplicateKnowledgeError):
        KnowledgeBase([make_cko("A"), make_cko("A")])
    with pytest.raises(DuplicateKnowledgeError):
        KnowledgeBase([], [make_decision("D"), make_decision("D")])


def test_base_lookups_and_queries():
    base = KnowledgeBase(
        [
            make_cko(
                "A",
                kind=KnowledgeKind.PRINCIPLE,
                authority=KnowledgeAuthority.CONSTITUTIONAL,
                lifecycle=Lifecycle.RATIFIED,
                universe="U1",
            ),
            make_cko("B", owner="OTHER", universe="U2"),
        ],
        [make_decision("D1")],
    )
    assert base.require_object("A").cko_id == "A"
    assert base.require_decision("D1").decision_id == "D1"
    assert base.get_object("missing") is None
    assert base.has_object("A") and base.has_decision("D1")
    assert base.object_ids() == ("A", "B")
    assert base.decision_ids() == ("D1",)
    assert len(base) == 3
    assert base.by_kind(KnowledgeKind.PRINCIPLE)[0].cko_id == "A"
    assert base.by_authority(KnowledgeAuthority.CONSTITUTIONAL)[0].cko_id == "A"
    assert base.by_lifecycle(Lifecycle.RATIFIED)[0].cko_id == "A"
    assert base.by_universe("U2")[0].cko_id == "B"
    assert base.by_owner("OTHER")[0].cko_id == "B"
    assert base.active_objects()[0].cko_id == "A"
    assert base.graph() is not None
    with pytest.raises(KnowledgeNotFoundError):
        base.require_object("nope")
    with pytest.raises(KnowledgeNotFoundError):
        base.require_decision("nope")


def test_base_authoring_immutability():
    base = KnowledgeBase([make_cko("A")])
    grown = base.with_object(make_cko("B"))
    assert grown.object_ids() == ("A", "B")
    assert base.object_ids() == ("A",)  # original unchanged
    with pytest.raises(DuplicateKnowledgeError):
        base.with_object(make_cko("A"))
    with_dec = base.with_decision(make_decision("D"))
    assert with_dec.decision_ids() == ("D",)
    with pytest.raises(DuplicateKnowledgeError):
        with_dec.with_decision(make_decision("D"))


def test_base_replace_object():
    base = KnowledgeBase([make_cko("A", title="old")])
    updated = base.replace_object(make_cko("A", title="new"))
    assert updated.require_object("A").title == "new"
    with pytest.raises(KnowledgeNotFoundError):
        base.replace_object(make_cko("Z"))


def test_store_roundtrip_is_byte_identical(store_dir):
    base = KnowledgeBase([make_cko("A", dependencies=("B",)), make_cko("B")], [make_decision("D")])
    store = KnowledgeStore(store_dir)
    assert not store.exists()
    store.save(base)
    assert store.exists()
    first = (store_dir / CANON_FILE).read_text()
    reloaded = store.load()
    store.save(reloaded)
    assert (store_dir / CANON_FILE).read_text() == first
    assert reloaded.object_ids() == ("A", "B")
    assert reloaded.decision_ids() == ("D",)


def test_store_load_missing_file_errors(store_dir):
    store = KnowledgeStore(store_dir)
    with pytest.raises(KnowledgeSourceError):
        store.load()


def test_store_rejects_bad_json_and_shape(store_dir):
    store_dir.mkdir(parents=True)
    (store_dir / CANON_FILE).write_text("{not json", encoding="utf-8")
    with pytest.raises(KnowledgeSourceError):
        KnowledgeStore(store_dir).load()
    (store_dir / CANON_FILE).write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(KnowledgeSourceError):
        KnowledgeStore(store_dir).load()
    (store_dir / CANON_FILE).write_text(json.dumps({"schema": "x"}), encoding="utf-8")
    with pytest.raises(KnowledgeSourceError):
        KnowledgeStore(store_dir).load()


def test_store_decisions_optional(store_dir):
    store = KnowledgeStore(store_dir)
    store.save(KnowledgeBase([make_cko("A")]))
    (store_dir / DECISIONS_FILE).unlink()
    loaded = store.load()
    assert loaded.decisions() == ()


def test_store_path_escape_rejected(store_dir):
    store = KnowledgeStore(store_dir)
    with pytest.raises(KnowledgeSourceError):
        store._path("../escape.json")


def test_store_refuses_frozen_corpus_write():
    store = KnowledgeStore(default_store_dir().parent / "00-BOOK")
    with pytest.raises(KnowledgeSourceError):
        store.save(KnowledgeBase([make_cko("A")]))


def test_default_store_dir_is_repo_knowledge():
    assert default_store_dir().name == "knowledge"
