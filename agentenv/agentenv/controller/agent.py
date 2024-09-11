import gc
import random
import shutil
from enum import Enum
from pathlib import Path

import torch
from torch.nn.parallel import DistributedDataParallel
from transformers import GenerationConfig, PreTrainedModel, PreTrainedTokenizerBase
from transformers.generation.utils import GenerateOutput


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
        self._vllm = None

    @torch.no_grad()
    def generate(
        self,
        input_ids: list[int],
        generation_config: GenerationConfig,
        refresh_engine: bool = False,
    ) -> torch.Tensor:
        if isinstance(self.model, DistributedDataParallel):
            model = self.model.module
        else:
            model = self.model
        if self.inference_engine == InferenceEngine.VLLM:
            from vllm import LLM, SamplingParams

            if not refresh_engine and self._vllm is not None:
                llm = self._vllm
            else:
                del self._vllm
                gc.collect()
                if model.device != torch.cpu:
                    model.to("cpu")

                while shm_path := Path(
                    f"/dev/shm/agentgym/inference_model_cache/{str(random.randint(0, 2**32))}"
                ):
                    if not shm_path.exists():
                        break
                model.save_pretrained(shm_path)
                self.tokenizer.save_pretrained(shm_path)
                tp_size = torch.cuda.device_count()

                torch.cuda.empty_cache()
                llm = LLM(
                    shm_path,
                    tensor_parallel_size=tp_size,
                    enable_prefix_caching=True,
                    use_v2_block_manager=True,
                    disable_custom_all_reduce=True,
                )
                self._vllm = llm
                shutil.rmtree(shm_path)

            INF = float("inf")
            max_tokens = generation_config.max_new_tokens or INF
            if generation_config.max_length:
                max_length = generation_config.max_length - len(input_ids)
            else:
                max_length = INF
            max_tokens = min(max_tokens, max_length)
            if max_tokens == INF:
                max_tokens = None

            generation_config = {
                "repetition_penalty": generation_config.repetition_penalty,
                "temperature": generation_config.temperature,
                "top_p": generation_config.top_p,
                "top_k": generation_config.top_k,
                "min_p": generation_config.min_p,
                "length_penalty": generation_config.length_penalty,
                "early_stopping": generation_config.early_stopping,
                "stop_strings": generation_config.stop_strings,
                "max_tokens": max_tokens,
                "min_new_tokens": generation_config.min_new_tokens,
            }
            generation_config = {k: v for k, v in generation_config.items() if v}

            sampling_params = SamplingParams.from_optional(
                **generation_config,
                detokenize=False,
            )

            output = llm.generate(
                prompt_token_ids=input_ids,
                sampling_params=sampling_params,
                use_tqdm=False,
            )
            generated_tokens = [o.outputs[0].token_ids.tolist() for o in output]

        else:
            output = model.generate(
                inputs=torch.tensor(input_ids, device=model.device),
                generation_config=generation_config,
            )
            if isinstance(output, GenerateOutput):
                output = output.sequences
            generated_tokens = [
                o[len(input_ids[0]) :].cpu().numpy().tolist() for o in output
            ]

        return generated_tokens
