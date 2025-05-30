import logging
from pathlib import Path

import toml  # type: ignore
from python_on_whales import docker

logger = logging.getLogger(__name__)


def main() -> None:
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    pyproject = toml.load(pyproject_path)
    try:
        builder = docker.buildx.create(
            platforms=pyproject["tool"]["docker"]["platforms"],
            name=f"builder_{pyproject['project']['name']}",
            use=True,
        )
        for name, cfg in pyproject["tool"]["docker"]["dockerfiles"].items():
            build_args = {"VERSION": pyproject["project"]["version"]}
            tag = f"{pyproject['tool']['docker']['registry']}/{name}"
            if isinstance(cfg, str):
                dockerfile = cfg
                target = None
            elif isinstance(cfg, dict):
                dockerfile = cfg.pop("FILE")
                target = cfg.pop("TARGET", None)
                build_args |= cfg
            else:
                raise TypeError

            docker.buildx.build(
                builder=builder,
                context_path=".",
                file=dockerfile,
                tags=[tag],
                cache=pyproject["tool"]["docker"]["cache"],
                platforms=pyproject["tool"]["docker"]["platforms"],
                push=pyproject["tool"]["docker"]["push"],
                build_args=build_args,
                target=target,
            )

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        docker.buildx.remove(builder)


if __name__ == "__main__":
    main()
