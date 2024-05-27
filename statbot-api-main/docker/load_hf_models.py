from transformers import AutoConfig, AutoTokenizer,AutoModelForCausalLM
import os

hf_auth='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'
# Get the model name from the environment variable
model_name = os.environ["MODEL_NAME"]

# Load the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=hf_auth)
model_config = AutoConfig.from_pretrained(
    model_name,
    use_auth_token=hf_auth
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    config=model_config,
    trust_remote_code=True,
    # quantization_config=bnb_config,
    device_map='auto',
    use_auth_token=hf_auth,
)
# Use the model for inference
