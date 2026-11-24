"""Prepare the cloud CPU baseline script without changing the frozen workspace."""
import ast
import json
from pathlib import Path
from stage_run import stage_run


def main():
    root = Path(__file__).resolve().parent.parent
    folder = root/'artifacts/kaggle-cpu-baselines'
    stage_run(folder,'eda','charlotte4306/soa-cpu-baselines',
              [root/'artifacts/offline-wheels/rank_bm25-0.2.2-py3-none-any.whl'])
    path = folder/'run_experiment.py'
    prefix = path.read_text(encoding='utf-8').rsplit("if __name__ == '__main__':",1)[0]
    code = prefix+(root/'kaggle/cpu_baseline_tail.py').read_text(encoding='utf-8')
    ast.parse(code)
    path.write_text(code,encoding='utf-8')
    path = folder/'kernel-metadata.json'
    metadata = json.loads(path.read_text(encoding='utf-8'))
    metadata.update(title='SOA CPU Baselines',enable_gpu=False,enable_internet=False)
    path.write_text(json.dumps(metadata,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
