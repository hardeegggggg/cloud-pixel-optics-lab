#!/usr/bin/env python3
import os

import aws_cdk as cdk

from pixel_optics_stack import PixelOpticsBatchStack


app = cdk.App()
PixelOpticsBatchStack(
    app,
    "PixelOpticsBatchStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)
app.synth()

