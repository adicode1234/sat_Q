"""Optional 470 MB general pretrained VQA checkpoint, cached inside this repo."""
from pathlib import Path
import json,hashlib,requests
def main():
    root=Path(__file__).resolve().parents[1];folder=root/'models/checkpoints/vilt';folder.mkdir(parents=True,exist_ok=True)
    base='https://huggingface.co/dandelin/vilt-b32-finetuned-vqa/resolve/main/'
    files=['config.json','preprocessor_config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt','pytorch_model.bin'];manifest={}
    for name in files:
        path=folder/name
        if not path.exists():
            with requests.get(base+name,stream=True,timeout=180) as r:
                r.raise_for_status()
                with path.with_suffix(path.suffix+'.part').open('wb') as f:
                    for chunk in r.iter_content(1024*1024):f.write(chunk)
            path.with_suffix(path.suffix+'.part').replace(path)
        manifest[name]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        print(name,manifest[name]['bytes'],flush=True)
    (folder/'download_manifest.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
