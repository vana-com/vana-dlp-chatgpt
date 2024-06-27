from pydantic import BaseModel, Field
from typing import Optional


class ScoreParts(BaseModel):
    authenticity: Optional[float] = 0
    ownership: Optional[float] = 0
    quality: Optional[float] = 0
    uniqueness: Optional[float] = 0


class Contribution(BaseModel):
    file_id: int
    is_valid: bool
    scores: ScoreParts = Field(default_factory=ScoreParts)

    def score(self):
        return (0.0 * self.scores.authenticity +
                0.0 * self.scores.ownership +
                1.0 * self.scores.quality +  # We are currently only assessing quality
                0.0 * self.scores.uniqueness)
