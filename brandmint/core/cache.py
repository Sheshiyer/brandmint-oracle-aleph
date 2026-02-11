"""
Prompt and asset caching for brandmint.

Implements intelligent caching to avoid redundant API calls:
- Hash-based prompt caching
- Asset metadata storage
- Expiration handling
- Cache invalidation
"""
import hashlib
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, Any
import yaml


# Default cache directory
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "brandmint"

# Cache expiration (default: 7 days)
DEFAULT_EXPIRATION_DAYS = 7


@dataclass
class CacheEntry:
    """A single cache entry."""
    key: str
    value: Any
    created_at: str
    expires_at: str
    metadata: dict = None
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return datetime.fromisoformat(self.expires_at) < datetime.now()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        return cls(**data)


class PromptCache:
    """
    Cache for prompts and their generated outputs.
    
    Uses content hash as key to detect identical prompts.
    """
    
    def __init__(
        self, 
        cache_dir: Optional[Path] = None,
        expiration_days: int = DEFAULT_EXPIRATION_DAYS,
    ):
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expiration_days = expiration_days
        self._index_path = self.cache_dir / "index.yaml"
        self._index = self._load_index()
    
    def _load_index(self) -> dict:
        """Load cache index from disk."""
        if self._index_path.exists():
            with open(self._index_path) as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _save_index(self):
        """Save cache index to disk."""
        with open(self._index_path, "w") as f:
            yaml.safe_dump(self._index, f)
    
    def _hash_prompt(self, prompt: str, provider: str = "", model: str = "") -> str:
        """Generate hash key for a prompt."""
        content = f"{provider}:{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _entry_path(self, key: str) -> Path:
        """Get path for a cache entry."""
        return self.cache_dir / f"{key}.yaml"
    
    def get(self, prompt: str, provider: str = "", model: str = "") -> Optional[Any]:
        """
        Get cached result for a prompt.
        
        Returns None if not found or expired.
        """
        key = self._hash_prompt(prompt, provider, model)
        
        if key not in self._index:
            return None
        
        entry_path = self._entry_path(key)
        if not entry_path.exists():
            del self._index[key]
            self._save_index()
            return None
        
        with open(entry_path) as f:
            data = yaml.safe_load(f)
        
        entry = CacheEntry.from_dict(data)
        
        if entry.is_expired():
            self.invalidate(prompt, provider, model)
            return None
        
        return entry.value
    
    def set(
        self, 
        prompt: str, 
        value: Any,
        provider: str = "",
        model: str = "",
        metadata: Optional[dict] = None,
        expiration_days: Optional[int] = None,
    ):
        """Cache a prompt result."""
        key = self._hash_prompt(prompt, provider, model)
        exp_days = expiration_days or self.expiration_days
        
        now = datetime.now()
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(days=exp_days)).isoformat(),
            metadata=metadata or {},
        )
        
        with open(self._entry_path(key), "w") as f:
            yaml.safe_dump(entry.to_dict(), f)
        
        self._index[key] = {
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
            "provider": provider,
            "model": model,
            "created_at": entry.created_at,
        }
        self._save_index()
    
    def invalidate(self, prompt: str, provider: str = "", model: str = ""):
        """Remove a cached entry."""
        key = self._hash_prompt(prompt, provider, model)
        
        entry_path = self._entry_path(key)
        if entry_path.exists():
            entry_path.unlink()
        
        if key in self._index:
            del self._index[key]
            self._save_index()
    
    def clear_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        removed = 0
        keys_to_remove = []
        
        for key in list(self._index.keys()):
            entry_path = self._entry_path(key)
            if entry_path.exists():
                with open(entry_path) as f:
                    data = yaml.safe_load(f)
                entry = CacheEntry.from_dict(data)
                if entry.is_expired():
                    entry_path.unlink()
                    keys_to_remove.append(key)
                    removed += 1
            else:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._index[key]
        
        if keys_to_remove:
            self._save_index()
        
        return removed
    
    def clear_all(self):
        """Clear entire cache."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._index = {}
        self._save_index()
    
    def stats(self) -> dict:
        """Get cache statistics."""
        total_entries = len(self._index)
        total_size = sum(
            f.stat().st_size 
            for f in self.cache_dir.glob("*.yaml")
            if f.name != "index.yaml"
        )
        
        expired_count = 0
        for key in self._index:
            entry_path = self._entry_path(key)
            if entry_path.exists():
                with open(entry_path) as f:
                    data = yaml.safe_load(f)
                if CacheEntry.from_dict(data).is_expired():
                    expired_count += 1
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "valid_entries": total_entries - expired_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(self.cache_dir),
        }


class AssetCache:
    """
    Cache for generated image assets.
    
    Stores asset metadata and file paths.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path.cwd() / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path = self.output_dir / ".asset-manifest.yaml"
        self._manifest = self._load_manifest()
    
    def _load_manifest(self) -> dict:
        """Load asset manifest."""
        if self._manifest_path.exists():
            with open(self._manifest_path) as f:
                return yaml.safe_load(f) or {}
        return {"assets": {}, "metadata": {"created_at": datetime.now().isoformat()}}
    
    def _save_manifest(self):
        """Save asset manifest."""
        self._manifest["metadata"]["updated_at"] = datetime.now().isoformat()
        with open(self._manifest_path, "w") as f:
            yaml.safe_dump(self._manifest, f)
    
    def has_asset(self, asset_id: str, prompt_hash: Optional[str] = None) -> bool:
        """
        Check if asset exists.
        
        If prompt_hash provided, also verifies the prompt hasn't changed.
        """
        if asset_id not in self._manifest["assets"]:
            return False
        
        asset = self._manifest["assets"][asset_id]
        
        # Check file exists
        if not Path(asset["file_path"]).exists():
            return False
        
        # If hash provided, check it matches
        if prompt_hash and asset.get("prompt_hash") != prompt_hash:
            return False
        
        return True
    
    def get_asset_path(self, asset_id: str) -> Optional[Path]:
        """Get path to cached asset."""
        if asset_id not in self._manifest["assets"]:
            return None
        
        path = Path(self._manifest["assets"][asset_id]["file_path"])
        return path if path.exists() else None
    
    def register_asset(
        self,
        asset_id: str,
        file_path: Path,
        prompt: str,
        provider: str,
        metadata: Optional[dict] = None,
    ):
        """Register a generated asset in the cache."""
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        
        self._manifest["assets"][asset_id] = {
            "file_path": str(file_path.absolute()),
            "prompt_hash": prompt_hash,
            "provider": provider,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self._save_manifest()
    
    def list_assets(self) -> list[str]:
        """List all cached asset IDs."""
        return list(self._manifest["assets"].keys())
    
    def clear(self):
        """Clear asset manifest (doesn't delete files)."""
        self._manifest = {"assets": {}, "metadata": {"created_at": datetime.now().isoformat()}}
        self._save_manifest()


# Global cache instances (lazy loaded)
_prompt_cache: Optional[PromptCache] = None
_asset_cache: Optional[AssetCache] = None


def get_prompt_cache() -> PromptCache:
    """Get global prompt cache instance."""
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = PromptCache()
    return _prompt_cache


def get_asset_cache(output_dir: Optional[Path] = None) -> AssetCache:
    """Get global asset cache instance."""
    global _asset_cache
    if _asset_cache is None or output_dir:
        _asset_cache = AssetCache(output_dir)
    return _asset_cache


# Convenience functions

def cached_prompt(prompt: str, provider: str = "", model: str = "") -> Optional[Any]:
    """Quick access to get cached prompt result."""
    return get_prompt_cache().get(prompt, provider, model)


def cache_prompt(prompt: str, value: Any, provider: str = "", model: str = "", **kwargs):
    """Quick access to cache a prompt result."""
    get_prompt_cache().set(prompt, value, provider, model, **kwargs)


__all__ = [
    "PromptCache",
    "AssetCache", 
    "CacheEntry",
    "get_prompt_cache",
    "get_asset_cache",
    "cached_prompt",
    "cache_prompt",
]
