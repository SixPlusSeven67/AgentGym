from base_eval import EvalArguments, main

args = EvalArguments(
    model_path="/home/share/models/Qwen2.5-7B-Instruct",
    inference_file="/home/kyln24/agentenv_scripts/AgentEval/webshop_test.json",
    output_file="/home/kyln24/agentenv_scripts/Qwen2.5-7B-Instruct_webshop_test_code_as_action_910b.jsonl",
    task_name="webshop",
    seed=42,
    max_round=10,
    env_server_base="http://127.0.0.1:8000",
    chat_template="chatml",
    use_vllm=True,
    action_format="code_as_action",
)

if __name__ == "__main__":
    main(vars(args))
