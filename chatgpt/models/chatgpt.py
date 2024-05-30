# The MIT License (MIT)
# Copyright © 2024 Corsali, Inc. dba Vana

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

"""
Contains the Pydantic models for the ChatGPT JSON data structure
"""
from typing import List, Dict, Optional, Any

from pydantic import BaseModel


class Author(BaseModel):
    role: str
    name: Optional[str]
    metadata: Dict


class Content(BaseModel):
    content_type: str
    parts: Optional[List[Any]] = None


class Message(BaseModel):
    id: str
    author: Author
    create_time: float | None
    update_time: float | None
    content: Content
    status: str
    end_turn: bool | None
    weight: float
    metadata: dict
    recipient: str


class Node(BaseModel):
    id: str
    message: Optional[Message]
    parent: Optional[str]
    children: List[str]


class ChatGPTData(BaseModel):
    title: str | None
    create_time: float
    update_time: float
    mapping: dict[str, Node]
    moderation_results: List
    current_node: str
    plugin_ids: List | None
    conversation_id: str
    conversation_template_id: str | None
    gizmo_id: str | None
    is_archived: bool
    safe_urls: List
    id: str
