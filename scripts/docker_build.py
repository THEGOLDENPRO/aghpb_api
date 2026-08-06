# import sys
# sys.path.insert(0, '.')

import app
from subprocess import check_call

tags = [
    f"devgoldy/aghpb_api:{app.__version__}",
    "devgoldy/aghpb_api:latest"
]

for image_tag in tags:
    check_call(
        args = [
            "docker",
            "buildx",
            "build",
            "-t",
            image_tag,
            "."
        ]
    )