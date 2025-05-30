import logging

from python_on_whales import docker

from . import settings

logger = logging.getLogger(__name__)


def main() -> None:
    builder = None  # 初期化して finally ブロックでの参照を安全にする
    try:
        builder = docker.buildx.create(
            platforms=settings.platforms,
            name=f"builder_{settings.prj_name}",
            use=True,
        )
        for name, cfg in settings.dockerfiles.items():
            build_args = {"VERSION": settings.version}
            tag = f"{settings.registry}/{name}"

            if isinstance(cfg, str):
                dockerfile = cfg
                target = None

            elif isinstance(cfg, dict):
                try:
                    dockerfile = cfg.pop("FILE")
                except KeyError as err:
                    raise ValueError(f"Missing 'FILE' key in config for {name}") from err
                target = cfg.pop("TARGET", None)
                build_args |= cfg  # 他のビルド引数を追加

            else:
                raise TypeError(f"Invalid type for dockerfile config: {type(cfg)}")

            docker.buildx.build(
                builder=builder,
                context_path=".",
                file=dockerfile,
                tags=[tag],
                cache=settings.cache,
                platforms=settings.platforms,
                push=settings.push,
                build_args=build_args,
                target=target,
            )
            logger.info(f"✅ Built and pushed: {tag}")

    except Exception as e:
        logger.error(f"❌ Error during build: {e}", exc_info=True)

    finally:
        if builder is not None:
            try:
                docker.buildx.remove(builder)
                logger.info(f"🧹 Removed builder: {builder.name}")
            except Exception as cleanup_err:
                logger.warning(f"⚠️ Failed to clean up builder: {cleanup_err}", exc_info=True)


if __name__ == "__main__":
    main()
