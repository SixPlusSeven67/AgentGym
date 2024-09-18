export VLLM_USE_MODELSCOPE=0
export VLLM_WORKER_MULTIPROC_METHOD=spawn

seed="42"

model_path="/root/AgentGym/HJX_test/code_as_action/outputs/models/alfworld_qwen2_0.5b_instruct/checkpoint-1815"

inference_file="/mnt/data/user/huang_jixuan/agentgym/AgentEval/alfworld_test.json"

# output_file="/cpfs01/shared/public/guohonglin/agentenv_scripts/webshop_test_result_test_codellama7b.jsonl"
output_file="alfworld_code_as_action.jsonl"

chat_template="chatml"
action_format="code_as_action"

# environment parameters
task_name="alfworld"
max_round="30"
env_server_base="http://127.0.0.1:36001"

rm ${output_file}

export CUDA_VISIBLE_DEVICES=2,4
python -u base_eval.py \
        --model_path "${model_path}" \
        --inference_file "${inference_file}" \
        --output_file "${output_file}" \
        --task_name "${task_name}" \
        --seed "${seed}" \
        --max_round "${max_round}" \
        --env_server_base "${env_server_base}" \
        --chat_template "${chat_template}" \
        --action_format "${action_format}" \
        --use_vllm
