"""
Review request models.
"""

from .review_actions_request import (
    AcceptSuggestionRequest,
    RejectSuggestionRequest,
    AdjustGradeRequest,
    FinalizeReviewRequest
)

__all__ = [
    "AcceptSuggestionRequest",
    "RejectSuggestionRequest",
    "AdjustGradeRequest",
    "FinalizeReviewRequest"
]
