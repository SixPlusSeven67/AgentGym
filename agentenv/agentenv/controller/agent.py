from transformers import PreTrainedModel, PreTrainedTokenizerBase
from typing import Any, Callable, Mapping, Optional, Sequence, TypedDict
import transformers
from abc import ABCMeta, abstractmethod


ConversationMessage = TypedDict(
    "ConversationMessage", {"from": str, "loss": Optional[bool], "value": str}
)
TokenizedConversationOutput = TypedDict(
    "TokenizedConversationOutput",
    {
        "text": str,
        "input_ids": list[int],
        "action_mask": list[int],
    },
)

class BaseChatTemplate(metaclass=ABCMeta):
        
    @abstractmethod
    def tokenize_conversation(
        self,
        conversation: list[ConversationMessage],
        tokenizer: PreTrainedTokenizerBase,
        ) -> TokenizedConversationOutput:
        """
        tokenizer a converssation
        """
    def checklist(self, l1, l2, tk):
        if len(l1) != len(l2):
            print("Length not equal")
            l=min(len(l1),len(l2))
        else:
            l=len(l1)
        for i in range(l):
            if l1[i] != l2[i]:
                print("Right: "+tk.decode([l1[i]]))
                print("Wrong: "+tk.decode([l2[i]]))
                print("Preword: "+tk.decode(l1[:i]))
                return False
        return True

class Agent:

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizerBase,
        chattemplate : BaseChatTemplate
    ) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.chattemplate =chattemplate


class ChatMLTemplate(BaseChatTemplate):
    def __init__(self):
        self.templatename = "chatml"
        super().__init__()

    def _tokenize_conversation_one(
        self,
        message: ConversationMessage,
        tokenizer: PreTrainedTokenizerBase,
        idx:int
    ) -> TokenizedConversationOutput:
        """
        This function applied Llama Chat template on the given vicuna-styled conversation message.
        You can provide your own _tokenize_conversation_one to adapt to your own task.
        """
        if(idx==0 and message['from']!="system"):
            text="<|im_start|>system\nYou are a helpful assistant<|im_end|>\n"
        else:
            text="\n"
        if message["from"] == "human":                
            text += f"<|im_start|>{message['from']}\n{message['value']}<|im_end|>"
            input_ids = tokenizer.encode(text, add_special_tokens=False)
        else:
            text += f"<|im_start|>{message['from']}\n{message['value']}<|im_end|>"
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
        self,
        conversation: list[ConversationMessage],
        tokenizer: PreTrainedTokenizerBase,
    ) -> TokenizedConversationOutput:
        text = ""
        input_ids = []
        action_mask = []

        for idx, message in enumerate(conversation):
            message_out = self._tokenize_conversation_one(message, tokenizer, idx)
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


    def check_one(self, message: ConversationMessage) -> bool:
        def tochat(message):
            return[{"role":message["from"],"content":message["value"]}]
        tk=transformers.AutoTokenizer.from_pretrained("/root/AgentGym/Qwen")
        cht=tochat(message)
        res1=tk.apply_chat_template(cht)
        res2=self.tokenize_conversation_one(message,tk)["input_ids"]
        dec1=tk.decode(res1)
        dec2=tk.decode(res2)
        # print(dec1,dec2)
        return res1 == res2
        
    def check_whole(self, conv) -> bool:
        def tochat(conv):
            return[{"role":message["from"],"content":message["value"]} for message in conv]

        tk=transformers.AutoTokenizer.from_pretrained("/root/AgentGym/Qwen")
        cht=tochat(conv)
        res1=tk.apply_chat_template(cht)
        res2=self.tokenize_conversation(conv,tk)["input_ids"]
        dec1=tk.decode(res1)
        dec2=tk.decode(res2)
        print(dec1+"\n\n\n\n")
        print(dec2)
        return self.checklist(res1, res2, tk)
        
class Llama3Template(BaseChatTemplate):
    def  __init__(self):
        self.templatename="llama3"
        super().__init__()


    def _tokenize_conversation_one(
        self,
        message: ConversationMessage,
        tokenizer: PreTrainedTokenizerBase,
        idx: int,
    ) -> TokenizedConversationOutput:
        val=message["value"]
        while len(val) and val[-1] in [" ","\n", "\t"]:
            val=val[:-1]
        if idx == 0:
            text = f"<|begin_of_text|><|start_header_id|>{message['from']}<|end_header_id|>\n\n{val}<|eot_id|>"
        else:
            text = f"<|start_header_id|>{message['from']}<|end_header_id|>\n\n{val}<|eot_id|>"
        # text+=""
        input_ids = tokenizer.encode(text, add_special_tokens=False)
        if(message["loss"]):
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
        self,
        conversation: list[ConversationMessage],
        tokenizer: PreTrainedTokenizerBase,
    ) -> TokenizedConversationOutput:
        
        text=""
        input_ids=[]
        action_mask=[]
        for idx, message in enumerate(conversation):
            res=self._tokenize_conversation_one(message,tokenizer,idx)
            text+=res["text"]
            input_ids+=res["input_ids"]
            action_mask+=res["action_mask"]
        return TokenizedConversationOutput(
            {
                "text": text,
                "input_ids": input_ids,
                "action_mask": action_mask,
            }
        )
    
    def check_whole(self, message: ConversationMessage) -> None:
        def tochat(conv):
            return[{"role":message["from"],"content":message["value"]} for message in conv]
        tk=transformers.AutoTokenizer.from_pretrained("/mnt/data/models/pretrain_models/Meta-Llama-3/Meta-Llama-3-8B-Instruct")
        cht=tochat(message)
        res1=tk.apply_chat_template(cht)
        res2=self.tokenize_conversation(message,tk)["input_ids"]
        # dec1=tk.decode(res1)
        # dec2=tk.decode(res2)
        # print(dec1+"\n\n\n\n")
        # print(dec2)
        return self.checklist(res1, res2, tk)

                
        

            
if __name__ == "__main__":
    import json
    from tqdm import tqdm
    with open("/root/AgentGym/dataset/alfworld_train.json") as f:
        data=json.load(f)
    
    ct = Llama3Template()
    res=[]
    for item in tqdm(data):
        conv=item["conversations"]
        if(ct.check_whole(conv)):
            pass
        else:
            print("error")
            break
        res.append(ct.check_whole(conv))
    pass
            


