#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for BilleterApp
"""


def clean_tags(tags: str) -> tuple | None:
    """
    Clean up tag string by removing empty segments and extra spaces.

    Args:
        tags: Raw tag string (e.g., "hi,,yes, , no")

    Returns:
        Cleaned tag tuple (e.g., ("hi", "yes", "no")) or None if empty

    Examples:
        "hi,,yes, , no" -> ("hi", "yes", "no")
        "  tag1  ,  tag2  " -> ("tag1", "tag2")
        "" -> None
        "single" -> ("single",)
    """
    if not tags:
        return None

    # Split by comma and strip whitespace from each segment
    segments = [tag.strip() for tag in tags.split(",")]

    # Filter out empty segments
    clean_segments = tuple([tag for tag in segments if tag])

    return clean_segments if clean_segments else None
