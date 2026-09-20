"""Download the Apache-2.0 Grounding DINO tiny checkpoint for local inference."""
from pathlib import Path
import requests
FILES=['config.json','preprocessor_config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt','added_tokens.json','model.safetensors']

def main():
    folder=Path(__file__).resolve().parents[1]/'models/checkpoints/grounding_dino';folder.mkdir(parents=True,exist_ok=True)
    for name in FILES:
        path=folder/name
        if path.exists():continue
        with requests.get(f'https://huggingface.co/IDEA-Research/grounding-dino-tiny/resolve/main/{name}',stream=True,timeout=120) as response:
            response.raise_for_status()
            with path.with_suffix('.part').open('wb') as f:
                for chunk in response.iter_content(1024*1024):f.write(chunk)
        path.with_suffix('.part').replace(path);print(name,path.stat().st_size,flush=True)
if __name__=='__main__':main()
