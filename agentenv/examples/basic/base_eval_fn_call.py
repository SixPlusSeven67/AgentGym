import json
import time
from dataclasses import dataclass, field

import jsonlines
import transformers
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

from agentenv.controller import (
    Agent,
    ChatGLM4Template,
    ChatMLTemplate,
    Evaluator,
    Llama2Template,
    Llama3Template,
)
from agentenv.envs import WebshopTask


@dataclass
class EvalArguments:
    model_path: str
    inference_file: str = field(metadata={"help": "Test dataset."})
    output_file: str
    task_name: str = field(
        default="webshop", metadata={"help": "Task name for evaluation"}
    )
    seed: int = field(default=42)

    # conversation rounds
    max_round: int = field(
        default=6,
        metadata={"help": "Interaction rounds between agents and environment"},
    )

    # environment parameters
    env_server_base: str = field(default=None)
    data_len: int = field(default=200)
    timeout: int = field(default=2400)
    chat_template: str = field(default="llama2")
    use_vllm: bool = field(default=False)


def main():
    parser = transformers.HfArgumentParser(EvalArguments)
    (args,) = parser.parse_args_into_dataclasses()
    args = vars(args)
    print(args)
    print(json.dumps(args, indent=2, ensure_ascii=False))

    MODEL_PATH = args["model_path"]
    DATA_PATH = args["inference_file"]

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH, device_map="auto", trust_remote_code=True
    ).eval()

    template_classes = {
        "chatglm4": ChatGLM4Template,
        "chatml": ChatMLTemplate,
        "llama2": Llama2Template,
        "llama3": Llama3Template,
    }
    chat_template = template_classes[args["chat_template"]]()

    # task_name - task dict
    task_classes = {
        "webshop": WebshopTask,
    }
    # adapter_classes = {"webshop": WebshopAdapter}

    # select task according to the name
    task_class = task_classes.get(args["task_name"].lower(), None)
    if task_class is None:
        raise ValueError(f"Unsupported task name: {args.task_name}")
    # adapter_class = adapter_classes.get(args["task_name"].lower(), None)

    # set environment parameters
    env_args = {
        "env_server_base": args["env_server_base"],
        "data_len": args["data_len"],
        "timeout": args["timeout"],
        "action_format": "function_calling",
    }

    # set env client
    evaluator = Evaluator(
        Agent(
            model,
            tokenizer,
            inference_engine="vllm" if args["use_vllm"] else "default",
            chat_template=chat_template,
        ),
        [task_class(client_args=env_args, n_clients=1)],
    )

    with open(DATA_PATH, "r") as file:
        test_data = json.load(file)

    data_idxs = [[int(item["item_id"].split("_")[-1])] for item in test_data]

    total_score = 0.0
    total_success = 0.0
    start_time = time.time()
    for data_idx in tqdm(data_idxs, total=len(data_idxs), desc="[Evaluation Loop]"):
        exps = evaluator.eval(
            generation_config=GenerationConfig(
                max_length=4096,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=(
                    tokenizer.pad_token_id
                    if tokenizer.pad_token_id is not None
                    else tokenizer.unk_token_id
                ),
            ),
            max_rounds=args["max_round"],
            idxs=data_idx,
        )
        total_score += exps.score
        total_success += exps.success

        cur_experiences = exps.experiences
        # write inference results to file
        with jsonlines.open(args["output_file"], mode="a") as f:
            for exp in cur_experiences:
                conversation = exp.conversation
                cur_reward = exp.reward
                cur_success = 1 if exp.reward == 1 else 0
                item_id = f"{args['task_name']}_{data_idx}"
                f.write(
                    {
                        "conversations": conversation,
                        "item_id": item_id,
                        "reward": cur_reward,
                        "success": cur_success,
                    }
                )
    process_time = time.time() - start_time

    Score = total_score / len(data_idxs)
    Success = total_success / len(data_idxs)
    print("\n\n==== EVALUATION ====\n")
    print(f"Score: {Score}")
    print(f"Success: {Success}")
    print(f"Time: {process_time} seconds")


if __name__ == "__main__":
    main()
