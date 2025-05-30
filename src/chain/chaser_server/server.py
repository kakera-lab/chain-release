import logging
from pathlib import Path

import aiofiles
from grpc import aio

from . import metric_pb2, metric_pb2_grpc

DATA_DIR = Path("/data/experiments")
logger = logging.getLogger(__name__)


class MetricService(metric_pb2_grpc.MetricServiceServicer):
    async def SendMetrics(self, request_iterator, context):
        buffer = []
        flush_threshold = 100

        async for metric_req in request_iterator:
            buffer.append(metric_req)

            if len(buffer) >= flush_threshold:
                await self.flush_to_file(buffer)
                buffer.clear()

        if buffer:
            await self.flush_to_file(buffer)

        return metric_pb2.MetricResponse(status="ok")

    async def flush_to_file(self, buffer):
        for m in buffer:
            dir_path = DATA_DIR / m.experiment_id / m.run_uuid
            dir_path.mkdir(parents=True, exist_ok=True)

            metric_path = dir_path / f"{m.key}.bin"
            meta_path = dir_path / f"{m.key}.meta"

            async with aiofiles.open(metric_path, "ab") as f:
                await f.write(m.value)

            if not meta_path.exists():
                async with aiofiles.open(meta_path, "w") as f:
                    await f.write(str(m.dim))


async def chaser_grpc_server(host: str = "0.0.0.0", port: int = 14000):
    server = aio.server()
    metric_pb2_grpc.add_MetricServiceServicer_to_server(MetricService(), server)
    server.add_insecure_port(f"{host}:{port}")
    await server.start()
    logger.info(f"Async gRPC server started on port {port}")
    await server.wait_for_termination()


if __name__ == "__main__":
    pass
