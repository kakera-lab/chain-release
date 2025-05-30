import os
import random
import subprocess
import sys
from pathlib import Path


class Setup:
    @classmethod
    def set_seed(cls, seed: int) -> int:
        os.environ["PYTHONHASHSEED"] = str(seed)
        random.seed(seed)

        try:
            import numpy as np

            np.random.seed(seed)
        except ImportError:
            pass

        try:
            import torch

            torch.manual_seed(seed)
            torch.use_deterministic_algorithms(True)
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = True
        except ImportError:
            pass

        try:
            from lightning.fabric.utilities.seed import seed_everything

            seed_everything(seed)
        except ImportError:
            pass

        return seed

    @classmethod
    def get_version(cls) -> str:
        cmd = ["python", "-V"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)  # noqa
        output = result.stdout.strip()
        return output

    @classmethod
    def get_env(cls, path: Path) -> str:
        cmd = ["uv", "pip", "freeze"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)  # noqa
        output = result.stdout
        path.write_text(output, encoding="utf-8")
        return output

    @classmethod
    def get_command(cls, path: Path) -> str:
        cmd = "python " + " ".join(sys.argv)
        output = cmd.rstrip()
        path.write_text(output, encoding="utf-8")
        return output


if __name__ == "__main__":
    pass
