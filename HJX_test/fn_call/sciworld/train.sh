exp_name="function_call_webshop_tiny_Llama"

n_epochs='1'

# accelerator config
num_processes='4'
main_process_port='8897'
config_file="default_config.yaml"

# training arguments
train_file="/mnt/data/user/huang_jixuan/agentgym/AgentTraj-L/webshop_train.json"
model_path="/mnt/data/user/huang_jixuan/models/TinyLlama/TinyLlama_v1.1"
batch_size="1"
gradient_accumulation_steps="4"
max_input_length="4096"
model_save_path="outputs/${exp_name}/"

num_workers="8"
learning_rate="1e-5"

saving_epoch_freq="1"


mkdir -p "${model_save_path}"
accelerate launch \
        --config_file "${config_file}" \
        --num_processes "${num_processes}" \
        --main_process_port "${main_process_port}" \
    train.py \
        --train_file "${train_file}" \
        --model_path "${model_path}" \
        --model_save_path "${model_save_path}" \
        --batch_size "${batch_size}" \
        --n_epochs "${n_epochs}" \
        --num_workers "${num_workers}" \
        --learning_rate "${learning_rate}" \
        --saving_epoch_freq "${saving_epoch_freq}" \
        --max_input_length "${max_input_length}" \
        --gradient_accumulation_steps "${gradient_accumulation_steps}" \