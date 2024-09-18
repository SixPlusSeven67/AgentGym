# CUDA_VISIBLE_DEVICES=0,1,2,4 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True torchrun --nproc_per_node=gpu code_as_action_from_react_traj.py

import datasets
import torch
from agentenv.controller import ChatMLTemplate
from agentenv.controller.types import ActionFormat
from agentenv.envs import WebshopAdapter
from transformers import (
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Qwen2ForCausalLM,
    Trainer,
    TrainingArguments,
)


def main():
    model_path = "/mnt/data/user/huang_jixuan/models/Qwen/Qwen2_0.5B_Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = Qwen2ForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )

    template = ChatMLTemplate()

    def react_traj_to_fn_call(example):
        conversations = example["conversations"]
        conversations[0], conversations[1] = WebshopAdapter.conversation_start_dict[
            ActionFormat.CODE_AS_ACTION
        ]
        for i in range(2, len(conversations)):
            if conversations[i]["from"] == "gpt":
                conversations[i]["value"] = WebshopAdapter.to_code_as_action(
                    WebshopAdapter.parse_react(conversations[i]["value"])
                )
        tokenized = template.tokenize_conversation(
            conversations, tokenizer, add_generation_prompt=True
        )
        return {
            "input_ids": tokenized["input_ids"],
            "labels": [
                ids if mask == 1 else -100
                for ids, mask in zip(tokenized["input_ids"], tokenized["action_mask"])
            ],
        }

    dataset = datasets.load_dataset(
        "json",
        data_files="/mnt/data/user/huang_jixuan/agentgym/AgentTraj-L/webshop_train.json",
    ).map(
        react_traj_to_fn_call, num_proc=8, remove_columns=["conversations", "item_id"]
    )

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir="/root/AgentGym/HJX_test/code_as_action/outputs/models/webshop_qwen2_0.5b_instruct",
            do_train=True,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=2,
            learning_rate=1e-5,
            weight_decay=1e-2,
            num_train_epochs=3,
            lr_scheduler_type="cosine",
            warmup_ratio=0.1,
            logging_dir="/root/AgentGym/HJX_test/code_as_action/outputs/logs/webshop_qwen2_0.5b_instruct",
            logging_strategy="steps",
            logging_steps=1,
            save_strategy="epoch",
            seed=100745534,
            data_seed=100745534,
            bf16=True,
            tf32=True,
            deepspeed={
                "train_micro_batch_size_per_gpu": "auto",
                "train_batch_size": "auto",
                "gradient_accumulation_steps": "auto",
                "bf16": {"enabled": True},
                "zero_optimization": {
                    "stage": 2,
                },
                "zero_allow_untested_optimizer": True,
            },
            report_to="tensorboard",
            ddp_find_unused_parameters=True,
            full_determinism=True,
        ),
        data_collator=DataCollatorForSeq2Seq(
            tokenizer, padding="longest", max_length=8192
        ),
        train_dataset=dataset["train"],
        tokenizer=tokenizer,
    )

    trainer.train()


if __name__ == "__main__":
    main()