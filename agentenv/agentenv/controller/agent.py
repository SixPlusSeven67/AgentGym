from enum import Enum

import torch
from transformers import GenerationConfig, PreTrainedModel, PreTrainedTokenizerBase


class InferenceEngine(Enum):
    DEFAULT = "default"
    VLLM = "vllm"


class Agent:

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizerBase,
        inference_engine: InferenceEngine = "default",
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.inference_engine = InferenceEngine(inference_engine)

    @torch.no_grad()
    def generate(
        self,
        inputs: torch.Tensor,
        generation_config: GenerationConfig,
    ):
        if self.inference_engine == InferenceEngine.DEFAULT:
            return self.model.generate(
                inputs=inputs, generation_config=generation_config
            )
