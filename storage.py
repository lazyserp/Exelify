# storage.py
# -----------
# This module is your tiny persistence layer:
# - Gives each uploaded dataset a unique id (doc_id)
# - Saves the *current* DataFrame to disk in Parquet format
# - Loads the current DataFrame back when an operation is requested
# - Keeps a simple, single-level UNDO snapshot

import os
import uuid
import pandas as pd

# Where we store all parquet files on disk
TMP_DIR = "tmp"

# Make sure the folder exists when this module is imported
os.makedirs(TMP_DIR, exist_ok=True)


def new_doc_id() -> str:
    """
    Create a globally unique id for an uploaded dataset/session.
    Example: '3f2b2a64-9f1c-4e74-9d7c-6a07d0f1b1dc'
    We return str(UUID) so it's easy to embed into HTML as a hidden field.
    """
    return str(uuid.uuid4())


def _path(doc_id: str) -> str:
    """
    Build the file path for the *current* DataFrame for this doc_id.
    Example: tmp/<doc_id>.parquet
    """
    return os.path.join(TMP_DIR, f"{doc_id}.parquet")


def _undo_path(doc_id: str) -> str:
    """
    Build the file path for the single-level UNDO snapshot.
    Example: tmp/<doc_id>_undo.parquet
    """
    return os.path.join(TMP_DIR, f"{doc_id}_undo.parquet")


def save_df(doc_id: str, df: pd.DataFrame) -> None:
    """
    Persist the *current* DataFrame for this doc_id to disk in Parquet format.
    - Parquet is fast, compact, and preserves types better than CSV.
    - index=False means we don't store the pandas index column.
    """
    df.to_parquet(_path(doc_id), index=False)


def load_df(doc_id: str) -> pd.DataFrame:
    """
    Load the *current* DataFrame for this doc_id from disk.
    - Raises if the file doesn't exist; caller can catch and handle.
    """
    return pd.read_parquet(_path(doc_id))


def push_undo(doc_id: str, df: pd.DataFrame) -> None:
    """
    Save a single UNDO snapshot for this doc_id.
    - We overwrite any previous snapshot (single-level undo).
    - Call this *before* applying a mutating operation.
    """
    df.to_parquet(_undo_path(doc_id), index=False)


def pop_undo(doc_id: str) -> pd.DataFrame | None:
    """
    Return the UNDO snapshot if it exists; otherwise return None.
    - In this simple version we DO NOT delete the undo file after reading,
      so pressing 'Undo' repeatedly will keep restoring the same snapshot.
      (You can choose to delete after reading for one-shot undo.)
    """
    upath = _undo_path(doc_id)
    if os.path.exists(upath):
        return pd.read_parquet(upath)
    return None
