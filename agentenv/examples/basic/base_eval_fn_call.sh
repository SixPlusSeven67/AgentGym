export VLLM_USE_MODELSCOPE=0
export VLLM_WORKER_MULTIPROC_METHOD=spawn

# model_path="/cpfs01/shared/public/guohonglin/agentenv_scripts/output/CodeLlama-7b-Instruct-hf/checkpoint-369"
# model_path="/cpfs01/shared/public/guohonglin/agentenv_scripts/output/Llama-2-7b-chat-hf/checkpoint-369"
model_path="/cpfs01/shared/public/guohonglin/agentenv_scripts/output/Qwen2-0.5B-Instruct"
# inference_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/AgentEval/webshop_test.json"
inference_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/webshop_test_1.json"
# output_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/webshop_test_result_test_codellama7b.jsonl"
output_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/tmp.jsonl"
task_name="webshop"
chat_template="chatml"
seed="42"

# environment parameters
max_round="10"
env_server_base="http://127.0.0.1:8000"

python -u base_eval_fn_call.py \
        --model_path "${model_path}" \
        --inference_file "${inference_file}" \
        --output_file "${output_file}" \
        --task_name "${task_name}" \
        --seed "${seed}" \
        --max_round "${max_round}" \
        --env_server_base "${env_server_base}" \
        --chat_template "${chat_template}" \
        --use_vllm \
