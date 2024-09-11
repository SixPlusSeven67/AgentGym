import json
from typing import Any, Mapping

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

from agentenv.controller import BaseEnvClient, BaseTask, ConversationMessage, StepOutput


ALFWORLD_FUNCTION_DESCRIPTION = [
        {
        "name":"goto",
        "description":"Move towards a specific receptacle or to a specific location.",
        "parameters":{
            "type":"object",
            "properties":{
                "recep":{
                    "type":"object",
                    "description":"The receptacle you want to move towards or the location you want to arrive at.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle or the location. It should be choose based on the previous obervation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the receptacle or the location. It should be choose based on the previous obervation."
                        }
                    }
                },  
            },
            "additionalProperties": "false",
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
                    "type":"object",
                    "description":"The object you want to pick up.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the object you want to pick up. It should be choose based on the previous obervation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the object you want to pick up. It should be choose based on the previous obervation."
                        },
                    }
                },
                "recep":{
                    "type":"object",
                    "description":"The receptacle you want to pick up object from.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle you want to pick up object from. It should be choose based on the previous obervation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the receptacle you want to pick up object from. It should be choose based on the previous obervation."
                        },
                    }
                }
            },
            "additionalProperties": "false",
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
                    "type":"object",
                    "description":"The object you want to place.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the object you want to place. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the object you want to place. It should be choose based on the previous observation."
                        },
                    }
                },
                "recep":{
                    "type":"object",
                    "description":"The receptacle you want to put object on.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle you want to put object on. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the receptacle you want to put object on. It should be choose based on the previous observation."
                        },
                    }
                }
            },
            "additionalProperties": "false",
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
                    "type":"object",
                    "description":"The receptacle you want to open.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle you want to open. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the receptacle you want to open. It should be choose based on the previous observation."
                        },
                    }
                }
            },
            "additionalProperties": "false",
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
                    "type":"object",
                    "description":"The receptacle you want to close.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle you want to close. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the receptacle you want to close. It should be choose based on the previous observation."
                        },
                    }
                }
            },
            "additionalProperties": "false",
            "required":["recep"]
        }
    },
    {
        "name":"toggle",
        "description":"Switches an object on or off.",
        "parameters":{
            "type":"object",
            "properties":{
                "obj":{
                    "type":"object",
                    "description":"The object you want to toggle.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the object you want to toggle. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the object you want to toggle. It should be choose based on the previous observation."
                        },
                    }
                },
                "recep":{
                    "type":"object",
                    "description":"The receptacle where the object you want to toggle locate.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the receptacle. It should be choose based on the previous observation."
                        },
                    }
                },
            },
            "additionalProperties": "false",
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
                    "type":"object",
                    "description":"The object you want to heat.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the object you want to heat. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the object you want to heat. It should be choose based on the previous observation."
                        },
                    }
                },
                "recep":{
                    "type":"object",
                    "description":"The receptacle you want to use to heat object.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle you want to heat object with. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the receptacle you want to heat object with. It should be choose based on the previous observation."
                        },
                    }
                }
            },
            "additionalProperties": "false",
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
                    "type":"object",
                    "description":"The object you want to cool.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the object you want to cool. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the object you want to cool. It should be choose based on the previous observation."
                        },
                    }
                },
                "recep":{
                    "type":"object",
                    "description":"The receptacle you want to use to cool object.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle you want to use to cool object. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the receptacle you want to use to cool object. It should be choose based on the previous observation."
                        },
                    }
                }
            },
            "additionalProperties": "false",
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
                    "type":"object",
                    "description":"The object you want to clean.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the object you want to clean. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the object you want to clean. It should be choose based on the previous observation."
                        },
                    }
                },
                "recep":{
                    "type":"object",
                    "description":"The receptacle you want to use to clean object.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle you want to use to clean object. It should be choose based on the previous observation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of the receptacle you want to use to clean object. It should be choose based on the previous observation."
                        },
                    }
                }
            },
            "additionalProperties": "false",
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
                    "type":"object",
                    "description":"The receptacle you want to get more information.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the receptacle you want to get more information. It should be choose based on the previous obervation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of receptacle you want to get more information. It should be choose based on the previous obervation."
                        }
                    }
                },  
                "obj":{
                    "type":"object",
                    "description":"The object(like a desklamp in order to look clearly) you want use to examine a receptacle.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the object you want to use. It should be choose based on the previous obervation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of object you want to use. It should be choose based on the previous obervation."
                        }
                    }
                },  
            },
            "additionalProperties": "false",
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
                    "type":"object",
                    "description":"The object(like a desklamp in order to look clearly) you want use to examine a receptacle.",
                    "properties":{
                        "name":{
                            "type":"string",
                            "description":"The type of the object you want to use. It should be choose based on the previous obervation."
                        },
                        "id":{
                            "type":"int",
                            "description":"The specific id of object you want to use. It should be choose based on the previous obervation."
                        }
                    }
                },  
            },
            "additionalProperties": "false",
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

class AlfworldAdapter(BaseAdapter):
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
                    "value": f'Interact with a household to solve a task. Imagine you are an intelligent agent in a household environment and your target is to perform actions to complete the task goal. At the beginning of your interactions, you will be given the detailed description of the current environment and your goal to accomplish. For each of your turn, you will be given a list of actions which you can choose one to perform in this turn. An action should be done by invoking an function.\n\n {format_function_call_prompt(ALFWORLD_FUNCTION_DESCRIPTION)}\n\n\nAfter your each turn, the environment will give you immediate feedback based on which you plan your next few steps. if the envrionment output "Nothing happened", that means the previous action is invalid and you should try more options.\n Reminder: \n1. the action must be chosen from the given available actions. Any actions except provided available actions will be regarded as illegal. \n2. Think when necessary, try to act directly more in the process.',
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

    valid_functions = {
    'goto', 'take', 'put', 'toggle', 'open', 'close', 'heat', 'cool', 'clean', 'examine', 'inventory', 'use'
    }

    @staticmethod
    def parse_function_calling(text: str) -> ActionWithTought:
        _fn_call = json.loads(
            "{" + text.split("{", 1)[-1].rsplit("}", 1)[0] + "}", strict=False
        )
        thought = _fn_call["thought"]
        fn_name = _fn_call["function_name"]
        args = _fn_call["arguments"]
        if fn_name not in AlfworldAdapter.valid_functions:
            raise ValueError("Invalid function name.")
        if fn_name == "goto":
            action = f'go to {args["recep"].name} {args["recep"].id}'
        elif fn_name == "take":
            action = f'take {args["obj"].name} {args["obj"].id} from {args["recep"].name} {args["recep"].id}'
        elif fn_name == "put":
            action = f'put {args["obj"].name} {args["obj"].id} in/on {args["recep"].name} {args["recep"].id}'
        elif fn_name == "toggle":
            if "recep" not in args:
                action = f'toggle {args["obj"].name} {args["obj"].id}'
            else:
                action = f'toggle {args["obj"].name} {args["obj"].id} {args["recep"].name} {args["recep"].id}'
        elif fn_name == "open":
            action = f'open {args["recep"].name} {args["recep"].id}'
        elif fn_name == "close":
            action = f'open {args["recep"].name} {args["recep"].id}'
        elif fn_name == "heat":
            action = f'heat {args["obj"].name} {args["obj"].id} with {args["recep"].name} {args["recep"].id}'
        elif fn_name == "cool":
            action = f'cool {args["obj"].name} {args["obj"].id} with {args["recep"].name} {args["recep"].id}'
        elif fn_name == "clean":
            action = f'clean {args["obj"].name} {args["obj"].id} with {args["recep"].name} {args["recep"].id}'
        elif fn_name == "examine":
            if "obj" not in args:
                action = f'examine {args["recep"].name} {args["recep"].id}'
            else:
                action = f'examine {args["recep"].name} {args["recep"].id} with {args["obj"].name} {args["obj"].id}'
        else: # inventory
            action = "inventory"
        return ActionWithTought(thought=thought, action=action)
    
    @staticmethod
    def to_function_calling(action_with_thought: ActionWithTought) -> str:
        if action_with_thought.action.startswith("go to"):
            # goto desk 1
            fn_name = "goto"
            args_ls = action_with_thought.action.split(" ", 2)[-1].split(" ")
            # desk 1
            recep_name = args_ls[0]
            recep_id = args_ls[1]
            args = {
                "recep": recep(name=recep_name, id=recep_id)
            }
        elif action_with_thought.action.startswith("take"):
            # take mug 1 from desk 1
            fn_name = "take"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            # mug 1 from desk 1
            obj_name = args_ls[0]
            obj_id = args_ls[1]
            recep_name = args_ls[3]
            recep_id = args_ls[4]
            args = {
                "obj": obj(name=obj_name, id=obj_id),
                "recep": recep(name=recep_name, id=recep_id)
            }
        elif action_with_thought.action.startswith("put"):
            # put mug 1 in/on draw 1
            fn_name = "put"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            # mug 1 in/on desk 1
            obj_name = args_ls[0]
            obj_id = args_ls[1]
            recep_name = args_ls[3]
            recep_id = args_ls[4]
            args = {
                "obj": obj(name=obj_name, id=obj_id),
                "recep": recep(name=recep_name, id=recep_id)
            }
        elif action_with_thought.action.startswith("toggle"):
            # toggle switch 1 / toggle desklamp 1 desk 1
            fn_name = "toggle"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            obj_name = args_ls[0]
            obj_id = args_ls[1]
            if len(args_ls) > 2:
                recep_name = args_ls[2]
                recep_id = args_ls[3]
                args = {
                    "obj": obj(name=obj_name, id=obj_id),
                    "recep": recep(name=recep_name, id=recep_id)
                }
            else:
                args = {
                    "obj": obj(name=obj_name, id=obj_id)
                }
        elif action_with_thought.action.startswith("open"):
            # open cabinet 1
            fn_name = "open"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            recep_name = args_ls[0]
            recep_id = args_ls[1]
            args = {
                "recep": recep(name=recep_name, id=recep_id)
            }
        elif action_with_thought.action.startswith("close"):
            # close cabinet 1
            fn_name = "close"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            recep_name = args_ls[0]
            recep_id = args_ls[1]
            args = {
                "recep": recep(name=recep_name, id=recep_id)
            }
        elif action_with_thought.action.startswith("heat"):
            # heat mug 1 with microwave 2
            fn_name = "heat"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            # mug 1 with microwave 1
            obj_name = args_ls[0]
            obj_id = args_ls[1]
            recep_name = args_ls[3]
            recep_id = args_ls[4]
            args = {
                "obj": obj(name=obj_name, id=obj_id),
                "recep": recep(name=recep_name, id=recep_id)
            }
        elif action_with_thought.action.startswith("cool"):
            # cool mug 1 with microwave 2
            fn_name = "cool"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            # mug 1 with microwave 1
            obj_name = args_ls[0]
            obj_id = args_ls[1]
            recep_name = args_ls[3]
            recep_id = args_ls[4]
            args = {
                "obj": obj(name=obj_name, id=obj_id),
                "recep": recep(name=recep_name, id=recep_id)
            }
        elif action_with_thought.action.startswith("clean"):
            # clean mug 1 with microwave 2
            fn_name = "clean"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            # mug 1 with microwave 1
            obj_name = args_ls[0]
            obj_id = args_ls[1]
            recep_name = args_ls[3]
            recep_id = args_ls[4]
            args = {
                "obj": obj(name=obj_name, id=obj_id),
                "recep": recep(name=recep_name, id=recep_id)
            }
        elif action_with_thought.action.startswith("examine"):
            # examine desk 1/ examine alarmclock 2 with desk 1
            fn_name = "examine"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            recep_name = args_ls[0]
            recep_id = args_ls[1]
            if len(args_ls) > 2:
                obj_name = args_ls[3]
                obj_id = args_ls[4]
                args = {
                    "obj": obj(name=obj_name, id=obj_id),
                    "recep": recep(name=recep_name, id=recep_id)
                }
            else:
                args = {
                    "recep": recep(name=obj_name, id=obj_id)
                }
        elif action_with_thought.action.startswith("use"):
            # use desklamp 1
            fn_name = "use"
            args_ls = action_with_thought.action.split(" ", 1)[-1].split(" ")
            obj_name = args_ls[0]
            obj_id = args_ls[1]
            args = {
                "obj": obj(name=obj_name, id=recep_id)
            }
        else:
            raise ValueError("Invalid action")
        return json.dumps(
            {
                "thought": action_with_thought.thought,
                "function_name": fn_name,
                "arguments": args,
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
    adapter_cls = AlfworldAdapter
    
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
        
        self._conversation_start = self.adapter_cls.conversation_start_dict[
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
        if action.endswith("<|im_end|>"):
            action = action[:-11]
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
