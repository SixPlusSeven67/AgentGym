import datasets
import torch
import os
import json
from accelerate import Accelerator
from dataclasses import dataclass, field
from tqdm.auto import tqdm
from agentenv.controller import (
    ActionFormat,
    ConversationMessage,
    TokenizedConversationOutput,
)
from agentenv.envs import SciWorldAdapter
import transformers
from transformers import (
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    AutoModelForCausalLM,
    LlamaForCausalLM,
    PreTrainedTokenizerBase,
    Trainer,
    TrainingArguments,
    AdamW,
    get_linear_schedule_with_warmup,
)
from torch.utils.data import DataLoader

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


@dataclass
class TrainingArguments:
    train_file: str = field(metadata={"help": "Training dataset."})
    # model path
    model_path: str = field(
        default="TinyLlama/TinyLlama_v1.1",
        metadata={"help": "Path of initial train model"},
    )
    model_save_path: str = field(
        default="outputs/model",
        metadata={"help": "Directory to save the trained model."},
    )
    batch_size: int = field(
        default=4,
        metadata={"help": "Batch size for training."},
    )
    n_epochs: int = field(default=40)
    num_workers: int = field(
        default=8, metadata={"help": "Number of subprocesses to use for data loading."}
    )
    learning_rate: float = field(default=2e-5, metadata={"help": "Learning rate."})
    gradient_accumulation_steps: int = field(default=1)
    saving_epoch_freq: int = field(default=1)
    max_input_length: int = field(default=700)



class Trainer:
    def __init__(self, args) -> None:
        self.args = args
        self.num_epoch = args["n_epochs"]
        self.accelerator = Accelerator(
        gradient_accumulation_steps=args["gradient_accumulation_steps"]
        )
        self.tokenizer = AutoTokenizer.from_pretrained(args["model_path"])
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            args["model_path"],
            torch_dtype=torch.float16
        )
        self._init_train_stuff()

    def save_model(self, save_path):
        os.makedirs(save_path, exist_ok=True)

        unwrapped_model = self.accelerator.unwrap_model(self.model)
        unwrapped_model.save_pretrained(
            save_path,
            is_main_process=self.accelerator.is_main_process,
            save_function=self.accelerator.save,
            state_dict=self.accelerator.get_state_dict(self.model),
        )
        self.tokenizer.save_pretrained(save_path)
    
    
    def _init_train_stuff(self):
        def react_traj_to_fn_call(example, tokenizer):
            conversations = example["conversations"]
            conversations[0], conversations[1] = SciWorldAdapter.conversation_start_dict[
                ActionFormat.FUNCTION_CALLING
            ]
            for i in range(2, len(conversations)):
                if conversations[i]["from"] == "gpt":
                    conversations[i]["value"] = SciWorldAdapter.to_function_calling(
                        SciWorldAdapter.parse_react(conversations[i]["value"])
                    )
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
            data_files=self.args["train_file"],
        ).map(
            react_traj_to_fn_call, 
            fn_kwargs={
                "tokenizer": self.tokenizer
            },
            num_proc=self.args["num_workers"], 
            remove_columns=["conversations", "item_id"]
        )
        self.data_collator=DataCollatorForSeq2Seq(
            self.tokenizer, padding="longest", max_length=self.args["max_input_length"]
        )
        self.train_dataloader = DataLoader(
            dataset["train"], shuffle=True, batch_size=self.args["batch_size"], collate_fn=self.data_collator
        )
        
        self.optimizer = AdamW(self.model.parameters(), lr=self.args["learning_rate"], eps=1e-8)

        self.train_dataloader, self.model, self.optimizer = self.accelerator.prepare(
            self.train_dataloader, self.model, self.optimizer
        )

        num_training_steps = ( 
            len(self.train_dataloader) 
            // self.accelerator.num_processes
            * self.num_epoch
            ) // self.args["gradient_accumulation_steps"]
        self.lr_scheduler = get_linear_schedule_with_warmup(
            optimizer=self.optimizer,
            num_warmup_steps = int(0.1 * num_training_steps),
            num_training_steps=num_training_steps,
        )

    def train(self):
        self.model.train()

        for epoch in range(self.num_epoch):
            with tqdm(
            enumerate(self.train_dataloader),
            disable=not self.accelerator.is_main_process,
            total=len(self.train_dataloader),
            desc=f"Train Loop | Epoch {epoch}",
            ) as t:
                with self.accelerator.accumulate(self.model):
                    for idx, batch in t:
                        outputs = self.model(**batch)
                        loss = outputs[0]
                        self.accelerator.backward(loss)
                        self.optimizer.step()
                        self.optimizer.zero_grad()
                        if self.accelerator.sync_gradients:
                            self.lr_scheduler.step()
                        t.set_postfix(loss = loss.item())
            if self.args["saving_epoch_freq"] is not None and epoch % self.args["saving_epoch_freq"] == 0:
                # if is_best:
                save_path = os.path.join(self.args["model_save_path"], f"train_epoch_{epoch}")
                self.save_model(save_path)
                self.model = self.accelerator.unwrap_model(self.model)


def main():
    # parser = transformers.HfArgumentParser(TrainingArguments)
    # (args,) = parser.parse_args_into_dataclasses()
    # args = vars(args)
    # print(json.dumps(args, indent=2, ensure_ascii=False))
    args = {
        "train_file": "/mnt/data/user/huang_jixuan/agentgym/AgentTraj-L/sciworld_train.json",
        "model_path": "/mnt/data/user/huang_jixuan/models/TinyLlama/TinyLlama_v1.1",
        "model_save_path": "outputs/function_call_webshop_tiny_Llama",
        "batch_size": 1,
        "n_epochs": 3,
        "num_workers": 8,
        "learning_rate": 1e-05,
        "gradient_accumulation_steps": 4,
        "saving_epoch_freq": 1,
        "max_input_length": 4096
        }

    fn_trainer = Trainer(args=args)

    fn_trainer.train()


if __name__ == "__main__":
    main()


