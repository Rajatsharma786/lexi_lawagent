from __future__ import annotations
from typing import Literal, TypedDict, List, Optional, Dict, Any, Annotated
from dataclasses import dataclass
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command, interrupt
import logging

from langchain_core.documents import Document


import redis # type: ignore
import json
import hashlib

import re
from PIL import Image as PILImage, ImageOps, ImageFilter

import os
from dotenv import load_dotenv
load_dotenv()

class RedisCache:
    """Redis caching utility for managing extracted text and memory usage."""

    def __init__(self):
        """Initialize Redis client and handle missing environment variables."""
        self.redis_host = os.environ.get("REDIS_HOST", "localhost")
        self.redis_port = int(os.environ.get("REDIS_PORT"))
        self.redis_password = os.environ.get("REDIS_PASSWORD")
        self.redis_expiration = int(os.environ.get("REDIS_EXPIRATION"))  # Default: 1 day
        self.memory_threshold_mb = int(os.environ.get("REDIS_MEMORY_THRESHOLD_MB", 25))  # Default: 25 MB

        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                decode_responses=True
            )
        except redis.ConnectionError as e:
            raise Exception(f"Failed to connect to Redis: {e}")

    def check_memory_usage(self) -> float:
        """Monitor Redis memory usage and return used memory in MB."""
        try:
            info = self.redis_client.info(section="memory")
            used_memory_mb = info["used_memory"] / 1024 / 1024
            if used_memory_mb > self.memory_threshold_mb:
                print(f"High memory usage: {used_memory_mb:.1f} MB")
                self.clear_old_cache()
            return used_memory_mb
        except Exception as e:
            print(f"Error checking Redis memory: {e}")
            return 0.0

    def clear_old_cache(self, days_old: int = 1):
        """Clear cache entries older than the specified number of days."""
        try:
            pattern = "extracted_text:*"
            keys = self.redis_client.keys(pattern)
            count = 0
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl is not None and ttl < (days_old * 24 * 60 * 60):  # Less than 1 day left
                    self.redis_client.delete(key)
                    count += 1
            print(f"Cleared {count} old cache entries")
        except Exception as e:
            print(f"Error clearing old cache: {e}")

    def get_query_hash(self, query: str) -> str:
        """Generate a hash for the query."""
        return hashlib.md5(query.encode()).hexdigest()

    def get_file_hash(self, file_path: str) -> str:
        """Generate a unique hash for a file based on content and modification time."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            mod_time = str(os.path.getmtime(file_path))
            return hashlib.md5(content + mod_time.encode()).hexdigest()
        except Exception as e:
            print(f"Error generating file hash: {e}")
            return ""

    def get_cached_extraction(self, file_path: str) -> Optional[str]:
        """Get cached extracted text if available."""
        try:
            file_hash = self.get_file_hash(file_path)
            return self.redis_client.get(f"extracted_text:{file_hash}")
        except Exception as e:
            print(f"Error retrieving cached extraction: {e}")
            return None

    def cache_extraction(self, file_path: str, extracted_text: str):
        """Cache extracted text with the file hash as key."""
        try:
            if self.check_memory_usage() > self.memory_threshold_mb:
                self.clear_old_cache()
            file_hash = self.get_file_hash(file_path)
            self.redis_client.setex(
                f"extracted_text:{file_hash}",
                self.redis_expiration,
                extracted_text
            )
        except Exception as e:
            print(f"Error caching extraction: {e}")