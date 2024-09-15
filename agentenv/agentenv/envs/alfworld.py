import json
from typing import Any, Mapping
import re

import requests
from requests.exceptions import RequestException

from agentenv.controller import (
    ActionFormat,
    ActionWithTought,
    BaseAdapter,
    BaseEnvClient,
    BaseTask,
    ConversationMessage,
    StepOutput,
    format_function_call_prompt,
)

from agentenv.controller import BaseEnvClient, BaseTask
from agentenv.controller.types import ConversationMessage, StepOutput


ALFWORLD_FUNCTION_DESCRIPTION = [
        {
        "name":"goto",
        "description":"Move towards a specific receptacle or to a specific location.",
        "parameters":{
            "type":"object",
            "properties":{
                "recep":{
                    "type":"string",
                    "description":"The receptacle you want to move towards or the location you want to arrive at.",
                },  
            },
            "required":["recep"],
        }
    },
    {
        "name":"take",
        "description":"Picks up an object from a specified receptacle.",
        "parameters":{
            "type":"object",
            "properties":{
                "obj":{
                    "type":"string",
                    "description":"The object you want to pick up.",
                },
                "recep":{
                    "type":"string",
                    "description":"The receptacle you want to pick up object from.",
                }
            },
            "required":["obj","recep"],
        }
    },
    {
        "name":"put",
        "description":"Puts an object on a specified receptacle.",
        "parameters":{
            "type":"object",
            "properties":{
                "obj":{
                    "type":"string",
                    "description":"The object you want to place.",
                },
                "recep":{
                    "type":"string",
                    "description":"The receptacle you want to put object on.",
                }
            },
            "required":["obj","recep"],
        }
    },
    {
        "name":"open",
        "description":"Opens a receptacle to reveal its contents.",
        "parameters":{
            "type":"object",
            "properties":{
                "recep":{
                    "type":"string",
                    "description":"The receptacle you want to open.",
                }
            },
            "required":["obj"]
        }
    },
    {
        "name":"close",
        "description":"Closes a receptacle.",
        "parameters":{
            "type":"object",
            "properties":{
                "recep":{
                    "type":"string",
                    "description":"The receptacle you want to close.",
                }
            },
            "required":["recep"]
        }
    },
    {
        "name": "look",
        "description": "Describe the current situation. Provide information such as what you are facing and what are things next to it.",
        "parameters":{
            "type": "object",
            "properties":{},
            "required": ["obj"]
        },
    },
    {
        "name":"toggle",
        "description":"Switches an object on or off.",
        "parameters":{
            "type":"object",
            "properties":{
                "obj":{
                    "type":"string",
                    "description":"The object you want to toggle.",
                },
            },
            "required":["obj"]
        }
    },
    {
        "name":"heat",
        "description":"Heats an object using a specified receptacle.",
        "parameter":{
            "type":"object",
            "properties":{
                "obj":{
                    "type":"string",
                    "description":"The object you want to heat.",
                },
                "recep":{
                    "type":"string",
                    "description":"The receptacle you want to use to heat object.",
                }
            },
            "required":["obj","recep"]
        }
    },
    {
        "name":"cool",
        "description":"Cools an object using a specified receptacle.",
        "parameter":{
            "type":"object",
            "properties":{
                "obj":{
                    "type":"string",
                    "description":"The object you want to cool.",
                },
                "recep":{
                    "type":"string",
                    "description":"The receptacle you want to use to cool object.",
                }
            },
            "required":["obj","recep"]
        }
    },
    {
        "name":"clean",
        "description":"Cleans an object using a specified receptacle.",
        "parameter":{
            "type":"object",
            "properties":{
                "obj":{
                    "type":"string",
                    "description":"The object you want to clean.",
                },
                "recep":{
                    "type":"string",
                    "description":"The receptacle you want to use to clean object.",
                }
            },
            "required":["obj","recep"]
        }
    },
    {
        "name":"inventory",
        "description":"Displays the list of objects currently being carried by you.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": "false"
        }
    },
    {
        "name":"examine",
        "description":"Provides a description of the objects present on or in a receptacle.",
        "parameters":{
            "type":"object",
            "properties":{
                "recep":{
                    "type":"string",
                    "description":"The receptacle you want to get more information.",
                },  
                "obj":{
                    "type":"string",
                    "description":"The object(like a desklamp in order to look clearly) you want use to examine a receptacle.",
                },  
            },
            "required":["recep"],
        }
    },
    {
        "name":"use",
        "description":"Uses an object as a tool to accomplish a certain goal.",
        "parameters":{
            "type": "object",
            "properties":{
                "obj":{
                    "type":"string",
                    "description":"The object(like a desklamp in order to look clearly) you want use to examine a receptacle.",
                },  
            },
            "required":["obj"],
        }
    }
]

class recep:
    def __init__(self, name: str, id: int) -> None:
        self.name = name
        self.id = id

class obj:
    def __init__(self, name: str, id: int) -> None:
        self.name = name
        self.id = id

class AlfWorldAdapter(BaseAdapter):
    conversation_start_dict = {
        ActionFormat.REACT:(
            ConversationMessage(
                {
                    "from": "human",
                    "loss": None,
                    "value": 'Interact with a household to solve a task. Imagine you are an intelligent agent in a household environment and your target is to perform actions to complete the task goal. At the beginning of your interactions, you will be given the detailed description of the current environment and your goal to accomplish. For each of your turn, you will be given a list of actions which you can choose one to perform in this turn. You should choose from two actions: "THOUGHT" or "ACTION". If you choose "THOUGHT", you should first think about the current condition and plan for your future actions, and then output your action in this turn. Your output must strictly follow this format:"Thought:\nyour thoughts.\n\nAction:\nyour next action"; If you choose "ACTION", you should directly output the action in this turn. Your output must strictly follow this format:"Action:\nyour next action". After your each turn, the environment will give you immediate feedback based on which you plan your next few steps. if the envrionment output "Nothing happened", that means the previous action is invalid and you should try more options.\n Reminder: \n1. the action must be chosen from the given available actions. Any actions except provided available actions will be regarded as illegal. \n2. Think when necessary, try to act directly more in the process.',
                }
            ),
            ConversationMessage(
                {
                    "from": "gpt",
                    "loss": False,
                    "value": "OK. I'll follow your instructions and try my best to solve the task.",
                }
            ),
        ),
        ActionFormat.FUNCTION_CALLING:(
            ConversationMessage(
                {
                    "from": "human",
                    "loss": None,
                    "value": f'Interact with a household to solve a task. Imagine you are an intelligent agent in a household environment and your target is to perform actions to complete the task goal. At the beginning of your interactions, you will be given the detailed description of the current environment and your goal to accomplish. For each of your turn, you will be given a list of actions which you can choose one to perform in this turn. Note that you should not choose actions and objects/receptacles not listed in the first turn. An action should be done by invoking an function.\n\n {format_function_call_prompt(ALFWORLD_FUNCTION_DESCRIPTION)}\n\n\nAfter your each turn, the environment will give you immediate feedback based on which you plan your next few steps. if the envrionment output \"Nothing happened\", that means the previous action is invalid and you should try more options.\n Reminder: \n1. the action must be chosen from the given available actions. Any actions except provided available actions will be regarded as illegal. \n2. Think when necessary, try to act directly more in the process.',
                }
            ),
            ConversationMessage(
                {
                    "from": "gpt",
                    "loss": False,
                    "value": "OK. I'll follow your instructions and try my best to solve the task.",
                }
            ),
        ),
        ActionFormat.CODE_AS_ACTION: (
            ConversationMessage(
                {
                    "from": "human",
                    "loss": None,
                    "value": "TODO: Add instructions for code as action",
                }
            ),
            ConversationMessage({"from": "gpt", "loss": False, "value": "Ok."}),
        ),
    }

    valid_functions_args = {
        'goto': ["recep"], 
        'take': ["obj", "recep"], 
        'put': ["obj", "recep"], 
        'toggle': ["obj"], 
        'open': ["recep"], 
        'close': ["recep"], 
        'heat': ["obj", "recep"], 
        'cool': ["obj", "recep"], 
        'clean': ["obj", "recep"], 
        'examine': ["recep", "obj"], 
        'inventory': [], 
        "look": [],
        'use':["obj"]
    }

    function_to_name = {
        'goto': 'go to', 
        'take': 'take', 
        'put': 'put', 
        'toggle': 'toggle', 
        'open': 'open', 
        'close': 'close', 
        'heat': 'heat', 
        'cool': 'cool', 
        'clean': 'clean', 
        'examine': 'examine', 
        "look": "look",
        'inventory': 'inventory', 
        'use':'use'
    }

    conjunction_words = {
        "take": "from",
        "put": "in/on",
        "heat": "with",
        "cool": "with",
        "clean": "with",
        "examine": "with"
    }

    @staticmethod
    def parse_function_calling(text: str) -> ActionWithTought:
        _fn_call = json.loads(
            "{" + text.split("{", 1)[-1].rsplit("}", 1)[0] + "}", strict=False
        )
        thought = _fn_call["thought"]
        fn_name = _fn_call["function_name"]
        args = _fn_call["arguments"]

        if fn_name not in AlfWorldAdapter.valid_functions_args:
            raise ValueError("Invalid function name.")
        arg_ls = AlfWorldAdapter.valid_functions_args[fn_name]
        if len(args) > len(arg_ls):
            raise TypeError(f"Got unexpected arguments. Function {fn_name} has {len(arg_ls)} argument(s) but got {len(args)}.")
        if len(args) == 1:
            # open door
            action_name = AlfWorldAdapter.function_to_name[fn_name]
            arg = args[arg_ls[0]]
            action = f'{action_name} {arg}'
        elif len(args) == 0:
            # inventory
            action = f'{AlfWorldAdapter.function_to_name[fn_name]}'
        else:  # two arguments
            # take mug from desk
            action_name = AlfWorldAdapter.function_to_name[fn_name]
            conjunction = AlfWorldAdapter.conjunction_words[fn_name]
            action = f'{action_name} {args[arg_ls[0]]} {conjunction} {args[arg_ls[1]]}'
        return ActionWithTought(thought=thought, action=action)
    
    @staticmethod
    def to_function_calling(action_with_thought: ActionWithTought) -> str:
        valid_action_flag = False
        fn_name = ''
        action_name = ''
        for k, v in AlfWorldAdapter.function_to_name.items():
            if action_with_thought.action.startswith(v):
                valid_action_flag = True
                fn_name = k
                action_name = v
                break
        if not valid_action_flag:
            raise ValueError(f"{action_with_thought.action}: Invalid action.")
        # inventory
        # open door to kitchen / toggle switch wall
        # heat mug with microwave 
        arg_ls = AlfWorldAdapter.valid_functions_args[fn_name]
        str_arg = action_with_thought.action.replace(action_name, '', 1).strip()
        if fn_name in AlfWorldAdapter.conjunction_words:
            separator = AlfWorldAdapter.conjunction_words[fn_name]
            str_arg_ls = re.split(fr'\s+{separator}\s+', str_arg)
            str_arg_ls = [s.strip() for s in str_arg_ls]
        else:
            str_arg_ls = [str_arg.strip()] if len(str_arg) else []
        
        if len(str_arg_ls) > len(arg_ls):
            raise TypeError(f"Got unexpected arguments. Function {fn_name} has {len(arg_ls)} argument(s) but got {len(str_arg_ls)}.")

        if len(str_arg_ls) > len(arg_ls):
            raise TypeError(f"Got unexpected arguments. function {fn_name} expected {len(arg_ls)} but got {len(str_arg_ls)}.")

        if len(str_arg_ls) == 0:
            args = {}
        elif len(str_arg_ls) == 1:
            args = {
                arg_ls[0]: str_arg_ls[0]
            }
        else:
            args = {
                arg_ls[0]: str_arg_ls[0],
                arg_ls[1]: str_arg_ls[1]
            }
        return json.dumps(
            {
                "thought": action_with_thought.thought,
                "function_name": fn_name,
                "arguments": args
            },
            ensure_ascii=False,
            indent=2,
        )
    
    # @staticmethod
    # def parse_code_as_action(text: str) -> ActionWithTought:
    #     pass

    # @staticmethod
    # def to_code_as_action(action_with_thought: ActionWithTought) -> str:
    #     pass


class AlfWorldEnvClient(BaseEnvClient):
    adapter_cls = AlfWorldAdapter
    
    def __init__(
        self,
        env_server_base: str,
        data_len: int,
        *args,
        timeout: int = 300,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.env_server_base = env_server_base
        self.timeout = timeout
        self.data_len = data_len

        ok = requests.post(f"{self.env_server_base}/create", timeout=self.timeout)
        if ok.status_code != 200:
            raise requests.RequestException(f"Failed to create environment: {ok}")
        
        self.conversation_start = self.adapter_cls.conversation_start_dict[
            self.action_format
        ]
        
        ok = ok.json()
        # print(ok)
        self.env_id = ok["id"]
        self.info = None

    def __len__(self):
        return self.data_len

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = self.env_id
        res = requests.post(
            f"{self.env_server_base}/{path}",
            json=data,
            timeout=self.timeout,
        )
        assert res.status_code == 200
        return res.json()

    def _get(self, path: str) -> dict[str, Any]:
        res = requests.get(
            f"{self.env_server_base}/{path}?id={self.env_id}",
            timeout=self.timeout,
        )
        assert res.status_code == 200
        return res.json()

    def observe(self) -> str:
        return f"{self.info['observation']}\nAVAILABLE ACTIONS: {','.join(self.info['available_actions'])}"

    def step(self, action: str) -> StepOutput:
        if action.endswith("</s>"):
            action = action[:-5]
        try:
            self.adapter_cls.action_parser(action, self.action_format)
        except Exception as e:
            print(e, action)
            return StepOutput(
                state="Invalid Action.\n\n" + self.observe(), reward=0.0, done=False
            )
        # print(f"Action: {action}")
        response = self._post("step", {"action": action})
        # print(response)
        self.info = {
            "observation": response["observation"],
            "available_actions": response["available_actions"],
            "reward": response["reward"],
            "done": response["done"],
        }
        return StepOutput(
            state=response["observation"],
            reward=response["reward"],
            done=response["done"],
        )

    def reset(self, game: int, world_type: str = "Text") -> dict[str, Any]:
        response = self._post("reset", {"game": game, "world_type": world_type})
        self.info = {
            "observation": response["observation"],
            "available_actions": response["available_actions"],
            "reward": 0,
            "done": False,
        }
        return response


class AlfWorldTask(BaseTask):
    env_client_cls = AlfWorldEnvClient
    env_name = "AlfWorld"

    def __init__(
        self, client_args: Mapping[str, Any], *args, n_clients: int = 1, **kwargs
    ) -> None:
        super().__init__(client_args, n_clients, *args, **kwargs)
