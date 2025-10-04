import os
import tempfile
from pathlib import Path
from typing import Optional

def _ensure_azure():
    try:
        from azure.storage.blob import ContainerClient  
    except Exception as e:
        raise RuntimeError("Install azure-storage-blob: pip install azure-storage-blob") from e

def _container_client_from_sas(container_sas_url: str):
    from azure.storage.blob import ContainerClient 
    return ContainerClient.from_container_url(container_sas_url)

def sync_container_to_dir(container_sas_url: str, local_dir: str, overwrite: bool = False) -> str:
    _ensure_azure()
    dest = Path(local_dir)
    dest.mkdir(parents=True, exist_ok=True)
    cc = _container_client_from_sas(container_sas_url)
    for blob in cc.list_blobs():
        target = dest / blob.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and not overwrite:
            continue
        bc = cc.get_blob_client(blob)
        with open(target, "wb") as f:
            f.write(bc.download_blob().readall())
    return str(dest)

def choose_chroma_dir(env_var_dir: str, env_var_sas: str, subdir_name: str, default_dir: str) -> str:
    """
    Priority:
    1) If ENV[env_var_dir] points to an existing directory (mount), use it.
    2) Else if ENV[env_var_sas] present, mirror container to cache dir and use that.
    3) Else use default_dir.
    """
    mounted = os.getenv(env_var_dir)
    if mounted and os.path.isdir(mounted):
        print(f"Using mounted directory for {subdir_name}: {mounted}")
        return mounted

    sas_url = os.getenv(env_var_sas)
    if sas_url:
        cache_root = os.getenv("CHROMA_CACHE_DIR", os.path.join(tempfile.gettempdir(), "lexi_chroma_cache"))
        local_dir = str(Path(cache_root) / subdir_name)
        print(f"Using Azure Blob Storage (SAS URL) for {subdir_name}. Mirroring to: {local_dir}")
        force = os.getenv("CHROMA_FORCE_SYNC", "0") == "1"
        already_has_files = any(Path(local_dir).rglob("*")) if Path(local_dir).exists() else False
        if force or not already_has_files:
            overwrite = os.getenv("CHROMA_OVERWRITE", "0") == "1"
            sync_container_to_dir(sas_url, local_dir, overwrite=overwrite)
        return local_dir

    print(f"Using local directory for {subdir_name}: {default_dir}")
    return default_dir