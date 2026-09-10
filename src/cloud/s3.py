"""S3 client helper.

This module does not upload the full AMEX dataset.
Callers must pass an explicit local path.
"""

from src.config import (
    AWS_REGION,
    require_aws,
)


def get_s3_client():
    require_aws()

    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is not installed. Run: pip install boto3"
        ) from exc

    return boto3.client(
        "s3",
        region_name=AWS_REGION,
    )
