import datasets
import torch
from agentenv.controller import (
    ActionFormat,
    ConversationMessage,
    TokenizedConversationOutput,
)
from agentenv.envs import AlfWorldAdapter
from transformers import (
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    AutoModelForCausalLM,
    LlamaForCausalLM,
    PreTrainedTokenizerBase,
    Trainer,
    TrainingArguments,
)

def tokenize_conversation_one(
    message: ConversationMessage,
    tokenizer: PreTrainedTokenizerBase,
) -> TokenizedConversationOutput:
    if message["from"] == "human":
        text = f"<s>[INST] {message['value']} [/INST]"
        input_ids = tokenizer.encode(text, add_special_tokens=False)
    else:
        text = f"{message['value']}</s>"
        input_ids = tokenizer.encode(text, add_special_tokens=False)
        text = f" {text}"
    if message["loss"]:
        action_mask = [1] * len(input_ids)
    else:
        action_mask = [0] * len(input_ids)

    return TokenizedConversationOutput(
        {
            "text": text,
            "input_ids": input_ids,
            "action_mask": action_mask,
        }
    )

def tokenize_conversation(
    conversation: list[ConversationMessage],
    tokenizer: PreTrainedTokenizerBase,
) -> TokenizedConversationOutput:
    text = ""
    input_ids = []
    action_mask = []

    for message in conversation:
        message_out = tokenize_conversation_one(message, tokenizer)
        text += message_out["text"]
        input_ids += message_out["input_ids"]
        action_mask += message_out["action_mask"]

    return TokenizedConversationOutput(
        {
            "text": text,
            "input_ids": input_ids,
            "action_mask": action_mask,
        }
    )

def main():
    model_path = "/mnt/data/user/huang_jixuan/models/TinyLlama/TinyLlama_v1.1"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = LlamaForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.float16,
        attn_implementation="flash_attention_2",
    )

    def react_traj_to_fn_call(example):
        conversations = example["conversations"]
        conversations[0], conversations[1] = AlfWorldAdapter.conversation_start_dict[
            ActionFormat.FUNCTION_CALLING
        ]
        for i in range(2, len(conversations)):
            if conversations[i]["from"] == "gpt":
                try:
                    conversations[i]["value"] = AlfWorldAdapter.to_function_calling(
                        AlfWorldAdapter.parse_react(conversations[i]["value"])
                    )
                except Exception as e:
                    print(e)
                    conversations[i]["value"] = AlfWorldAdapter.parse_react(conversations[i]["value"])    # 该怎么处理比较好？
        tokenized = tokenize_conversation(conversations, tokenizer)
        return {
            "input_ids": tokenized["input_ids"],
            "labels": [
                ids if mask == 1 else -100
                for ids, mask in zip(tokenized["input_ids"], tokenized["action_mask"])
            ],
        }

    dataset = datasets.load_dataset(
        "json",
        data_files="/mnt/data/user/huang_jixuan/agentgym/AgentTraj-L/alfworld_train.json",
    ).map(
        react_traj_to_fn_call, num_proc=8, remove_columns=["conversations", "item_id"], load_from_cache_file=False
    )

    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir="/root/AgentGym/HJX_test/fn_call/outputs/model/alfworld_tiny_Llama",
            do_train=True,
            per_device_train_batch_size=1,
            gradient_accumulation_steps=1,
            learning_rate=1e-5,
            weight_decay=1e-2,
            num_train_epochs=3,
            lr_scheduler_type="cosine",
            warmup_ratio=0.1,
            logging_dir="/root/AgentGym/HJX_test/fn_call/outputs/logs/alfworld_tiny_Llama",
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
                    "stage": 1,
                },
                "zero_allow_untested_optimizer": True,
            },
            report_to="tensorboard",
            ddp_find_unused_parameters=True,
            # gradient_checkpointing=True,
            full_determinism=True,
        ),
        data_collator=DataCollatorForSeq2Seq(
            tokenizer, padding="longest", max_length=4096
        ),
        train_dataset=dataset["train"],
        tokenizer=tokenizer,
    )

    trainer.train()

if __name__ == "__main__":
    main()
