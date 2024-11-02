export VLLM_USE_MODELSCOPE=0
export VLLM_WORKER_MULTIPROC_METHOD=spawn

model_path="/root/AgentGym/HJX_test/fn_call/outputs/model/webshop_tiny_Llama/checkpoint-369"
inference_file="/mnt/data/user/huang_jixuan/agentgym/AgentEval/webshop_test.json"
output_file="webshop_fncall.jsonl"
task_name="webshop"
chat_template="llama2"
seed="42"
use_vllm="False"

# environment parameters
max_round="10"
env_server_base="http://127.0.0.1:36001"

python -u base_eval_fn_call.py \
        --model_path "${model_path}" \
        --inference_file "${inference_file}" \
        --output_file "${output_file}" \
        --task_name "${task_name}" \
        --seed "${seed}" \
        --max_round "${max_round}" \
        --env_server_base "${env_server_base}" \
        --chat_template "${chat_template}" \
        --use_vllm "${use_vllm}"\
