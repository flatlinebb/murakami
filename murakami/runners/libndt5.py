import logging
import shutil
import subprocess
import uuid

import jsonlines

from murakami.errors import RunnerError
from murakami.runner import MurakamiRunner

logger = logging.getLogger(__name__)


class LibndtClient(MurakamiRunner):
    """Run LibNDT tests."""
    def __init__(self, config=None, data_cb=None):
        super().__init__(
            title="ndt5",
            description="The Network Diagnostic Tool v5 test.",
            config=config,
            data_cb=data_cb,
        )

    @staticmethod
    def _start_test():
        logger.info("Starting NDT5 test...")
        if shutil.which("libndt-client") is not None:
            output = subprocess.run(
                [
                    "libndt-client",
                    "--download",
                    "--upload",
                    "--lookup-policy=closest",
                    "--json",
                    "--websocket",
                    "--tls",
                    "--batch",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            reader = jsonlines.Reader(output.stdout.splitlines())
        else:
            raise RunnerError(
                "libndt",
                "Executable libndt-client does not exist, please install libndt.",
            )
        return [
            *reader.iter(allow_none=True, skip_empty=True, skip_invalid=True)
        ]
