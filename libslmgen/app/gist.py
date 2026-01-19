#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Gist Upload Utility.

Creates GitHub Gists from notebook content for Colab integration.
"""
# Author: Eshan Roy <eshanized@proton.me>
# License: MIT License
# Copyright (c) 2026 Eshan Roy

import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"


async def create_gist(
    notebook_content: str,
    filename: str,
    description: str = "SLMGEN Fine-tuning Notebook",
) -> Optional[str]:
    """
    Create a GitHub Gist and return the raw URL for Colab integration.
    
    Args:
        notebook_content: The notebook JSON content
        filename: Name for the notebook file (e.g., "finetune_phi4.ipynb")
        description: Description for the Gist
        
    Returns:
        Raw URL suitable for "Open in Colab" link, or None if creation fails
        
    Note:
        Requires GITHUB_TOKEN environment variable to be set with a
        personal access token that has 'gist' scope.
    """
    if not settings.github_token:
        logger.debug("GitHub token not configured, skipping Gist creation")
        return None
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    payload = {
        "description": description,
        "public": True,  # Public so Colab can access it
        "files": {
            filename: {
                "content": notebook_content
            }
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GITHUB_API_URL}/gists",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            
            if response.status_code == 201:
                data = response.json()
                gist_id = data["id"]
                
                # Get the raw URL for the notebook file
                files = data.get("files", {})
                file_info = files.get(filename, {})
                raw_url = file_info.get("raw_url")
                
                if raw_url:
                    # Generate Colab URL
                    colab_url = f"https://colab.research.google.com/gist/{data['owner']['login']}/{gist_id}"
                    logger.info(f"Created Gist: {gist_id}, Colab URL: {colab_url}")
                    return colab_url
                else:
                    logger.warning(f"Gist created but no raw_url found: {gist_id}")
                    return None
            else:
                logger.warning(
                    f"Failed to create Gist: {response.status_code} - {response.text}"
                )
                return None
                
    except httpx.RequestError as e:
        logger.error(f"HTTP error creating Gist: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating Gist: {e}")
        return None


async def delete_gist(gist_id: str) -> bool:
    """
    Delete a GitHub Gist.
    
    Args:
        gist_id: The Gist ID to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    if not settings.github_token:
        return False
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{GITHUB_API_URL}/gists/{gist_id}",
                headers=headers,
                timeout=30.0,
            )
            
            if response.status_code == 204:
                logger.info(f"Deleted Gist: {gist_id}")
                return True
            else:
                logger.warning(f"Failed to delete Gist: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Error deleting Gist: {e}")
        return False
