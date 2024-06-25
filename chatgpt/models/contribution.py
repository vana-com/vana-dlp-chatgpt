from typing import Optional

from pydantic import BaseModel, Field


class ScoreParts(BaseModel):
    authenticy: Optional[float] = 0
    ownership: Optional[float] = 0
    quality: Optional[float] = 0
    uniqueness: Optional[float] = 0


class Contribution(BaseModel):
    file_id: int
    is_valid: bool
    scores: ScoreParts = Field(default_factory=ScoreParts)

    def score(self):
        return (0.1 * self.scores.authenticy +
                0.2 * self.scores.ownership +
                0.5 * self.scores.quality +
                0.2 * self.scores.uniqueness)
