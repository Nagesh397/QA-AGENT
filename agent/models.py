from typing import List, Literal
from pydantic import BaseModel, Field


class TestCase(BaseModel):
    title: str = Field(description="Short, descriptive test case title")
    linked_ac: str = Field(description="Acceptance criterion ID this covers, e.g. AC1")
    test_type: Literal["Positive", "Negative", "Boundary", "Edge"]
    priority: Literal["High", "Medium", "Low"]
    preconditions: str
    steps: List[str] = Field(description="Ordered, atomic test steps")
    test_data: str = Field(description="Concrete input values to use")
    expected_result: str


class TestSuite(BaseModel):
    test_cases: List[TestCase]
