from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config


MODEL = "mlx-community/gemma-4-e4b-it-4bit"

model, processor = load(MODEL)
config = load_config(MODEL)


prompt = apply_chat_template(processor, config, "Describe this image. How many people? What is the context?", num_images=1)
result = generate(model, processor, prompt, ["photo2.jpg"], max_tokens=300)
print(result.text)
