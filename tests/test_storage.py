import pytest

from pixelcloud.storage import parse_s3_uri


def test_parse_s3_uri() -> None:
    assert parse_s3_uri("s3://example-bucket/input/cases.jsonl") == (
        "example-bucket",
        "input/cases.jsonl",
    )


@pytest.mark.parametrize("uri", ["https://bucket/key", "s3://bucket", "s3:///key"])
def test_reject_invalid_s3_uri(uri: str) -> None:
    with pytest.raises(ValueError):
        parse_s3_uri(uri)

