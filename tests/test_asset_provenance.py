"""Tests for brandmint.core.asset_provenance — AF-04."""

import json
import os
import tempfile

import pytest

from brandmint.core.asset_provenance import (
    AssetProvenance,
    AssetRecord,
    AssetSource,
)


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def provenance(tmp_dir):
    return AssetProvenance(tmp_dir)


class TestAssetProvenance:
    def test_register_provided(self, provenance):
        rec = provenance.register_provided("logo-primary", "/path/to/logo.png")
        assert rec.asset_id == "logo-primary"
        assert rec.source == AssetSource.PROVIDED
        assert rec.file_path == "/path/to/logo.png"
        assert rec.original_path == "/path/to/logo.png"

    def test_register_generated(self, provenance):
        rec = provenance.register_generated(
            "2A", "/out/2A-bento.png", model="nano-banana-pro", provider="fal", seed=42
        )
        assert rec.source == AssetSource.GENERATED
        assert rec.model_used == "nano-banana-pro"
        assert rec.seed == 42

    def test_register_composited(self, provenance):
        layers = ["/out/2A-bento.png", "/logos/brand-logo.png"]
        rec = provenance.register_composited(
            "2A-composited", "/out/2A-composited.png", layers=layers, model="nano-banana-pro"
        )
        assert rec.source == AssetSource.COMPOSITED
        assert rec.composite_layers == layers

    def test_get(self, provenance):
        provenance.register_provided("logo", "/logo.png")
        rec = provenance.get("logo")
        assert rec is not None
        assert rec.asset_id == "logo"

    def test_get_nonexistent(self, provenance):
        assert provenance.get("nonexistent") is None

    def test_get_with_seed(self, provenance):
        provenance.register_generated("2A", "/2a-v1.png", seed=42)
        provenance.register_generated("2A", "/2a-v2.png", seed=137)
        assert provenance.get("2A", seed=42).file_path == "/2a-v1.png"
        assert provenance.get("2A", seed=137).file_path == "/2a-v2.png"

    def test_list_all(self, provenance):
        provenance.register_provided("logo", "/logo.png")
        provenance.register_generated("2A", "/2A.png")
        assert len(provenance.list_all()) == 2

    def test_list_by_source(self, provenance):
        provenance.register_provided("logo", "/logo.png")
        provenance.register_generated("2A", "/2A.png")
        provenance.register_generated("3B", "/3B.png")
        assert len(provenance.list_provided()) == 1
        assert len(provenance.list_generated()) == 2

    def test_persistence(self, tmp_dir):
        # Write
        prov1 = AssetProvenance(tmp_dir)
        prov1.register_provided("logo", "/logo.png")
        prov1.register_generated("2A", "/2A.png", model="flux", seed=42)

        # Read in new instance
        prov2 = AssetProvenance(tmp_dir)
        assert len(prov2.list_all()) == 2
        logo = prov2.get("logo")
        assert logo.source == AssetSource.PROVIDED

    def test_clear(self, provenance):
        provenance.register_provided("logo", "/logo.png")
        assert len(provenance.list_all()) == 1
        provenance.clear()
        assert len(provenance.list_all()) == 0

    def test_json_file_format(self, tmp_dir):
        prov = AssetProvenance(tmp_dir)
        prov.register_provided("logo", "/logo.png")
        store_path = os.path.join(tmp_dir, ".brandmint/asset-provenance.json")
        assert os.path.exists(store_path)
        with open(store_path) as f:
            data = json.load(f)
        assert data["version"] == 1
        assert "assets" in data
        assert "logo" in data["assets"]

    def test_created_at_auto_set(self, provenance):
        rec = provenance.register_provided("logo", "/logo.png")
        assert rec.created_at != ""
        assert "T" in rec.created_at  # ISO format
