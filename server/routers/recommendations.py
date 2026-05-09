"""
Weekly recommendation endpoints — Phase 2 placeholder.

Endpoints will be implemented when the recommender service is built.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# TODO (Phase 2): implement GET /recommendations/current
# TODO (Phase 2): implement GET /recommendations/history
# TODO (Phase 2): implement POST /recommendations/{rec_id}/accept
# TODO (Phase 2): implement POST /recommendations/{rec_id}/skip
