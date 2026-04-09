# Description: Pydantic response models for study note API payloads.
# This file is part of the SprintStudy project.

from pydantic import BaseModel, Field


class StudyNoteSummaryResponse(BaseModel):
    note_id: str = Field(..., description="Unique id of uploaded study note")
    filename: str = Field(..., description="Original uploaded filename")
    chunks: int = Field(..., description="Number of chunks extracted from document")
    stored_to_pinecone: bool = Field(
        ..., description="Whether chunks and embeddings were stored in Pinecone"
    )
    summary: str = Field(..., description="Generated summary markdown")
