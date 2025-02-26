from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence, TypedDict

ConversationMessage = TypedDict(
    "ConversationMessage", {"from": str, "loss": Optional[bool], "value": str}
)

TokenizedConversationOutput = TypedDict(
    "TokenizedConversationOutput",
    {
        "text": str,
        "input_ids": Sequence[int],
        "action_mask": Sequence[int],
    },
)


class ActionFormat(Enum):
    REACT = "react"
    FUNCTION_CALLING = "function_calling"
    CODE_AS_ACTION = "code_as_action"


class InferenceEngine(Enum):
    DEFAULT = "default"
    VLLM = "vllm"


@dataclass
class StepOutput:
    state: str
    reward: float
    done: bool


@dataclass
class ExperienceOutput:
    conversation: list[ConversationMessage]
    reward: float
    text: str | None
    seq_ids: list[int] | None
    attention_mask: list[int] | None
    action_mask: list[int] | None


@dataclass
class ActionWithTought:
    thought: str
    action: str


@dataclass
class EvaluationOutput:
    experiences: list[ExperienceOutput]
    score: float
    success: float
