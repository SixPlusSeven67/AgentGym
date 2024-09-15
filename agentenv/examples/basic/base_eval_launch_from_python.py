import os

from base_eval import EvalArguments, main

os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"

args = EvalArguments(
    # model_path="/cpfs01/shared/public/guohonglin/agentenv_scripts/Qwen2-72B-Instruct",
    model_path="/cpfs01/shared/public/guohonglin/agentenv_scripts/output/Qwen2-1.5B-Instruct/checkpoint-369",
    # inference_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/webshop_test_1.json",
    inference_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/AgentEval/webshop_test.json",
    # output_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/tmp.jsonl",
    # output_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/webshop_test_result_test_qwen2_72b_inst_no_train.jsonl",
    output_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/webshop_test_result_test_qwen2_1.5b_inst.jsonl",
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
