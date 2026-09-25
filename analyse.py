from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config


MODELE = "mlx-community/gemma-4-e4b-it-4bit"

model, processor = load(MODELE)
config = load_config(MODELE)


prompt = apply_chat_template(processor, config, "Décris cette image. Combien de personne? Quel contexte?", num_images=1)
resultat = generate(model, processor, prompt, ["photo2.jpg"], max_tokens=300)
print(resultat.text)