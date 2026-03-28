import json
import os
from typing import Union
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BEARER_TOKEN_BEDROCK, AWS_DEFAULT_REGION, BEDROCK_MODEL_ID


def get_bedrock_client():
    if AWS_BEARER_TOKEN_BEDROCK:
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = AWS_BEARER_TOKEN_BEDROCK
        return boto3.client(
            "bedrock-runtime",
            region_name=AWS_DEFAULT_REGION,
        )
    else:
        return boto3.client(
            "bedrock-runtime",
            region_name=AWS_DEFAULT_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )


async def invoke_bedrock(prompt: str, system: str = "", max_tokens: int = 4096) -> str:
    client = get_bedrock_client()

    messages = [{"role": "user", "content": [{"text": prompt}]}]

    kwargs = {
        "modelId": BEDROCK_MODEL_ID,
        "messages": messages,
        "inferenceConfig": {"maxTokens": max_tokens},
    }

    if system:
        kwargs["system"] = [{"text": system}]

    response = client.converse(**kwargs)

    return response["output"]["message"]["content"][0]["text"]


async def invoke_bedrock_json(prompt: str, system: str = "", max_tokens: int = 4096) -> Union[dict, list]:
    """Invoke Bedrock and parse the response as JSON."""
    import re

    raw = await invoke_bedrock(prompt, system, max_tokens)
    raw = raw.strip()

    code_block = re.search(r"```(?:json)?\s*\n?(.*?)```", raw, re.DOTALL)
    if code_block:
        raw = code_block.group(1).strip()
    else:
        first_brace = raw.find("{")
        first_bracket = raw.find("[")
        if first_brace == -1 and first_bracket == -1:
            raise ValueError(f"No JSON found in response: {raw[:200]}")
        if first_bracket == -1 or (first_brace != -1 and first_brace < first_bracket):
            start = first_brace
        else:
            start = first_bracket

        raw = raw[start:]

        if raw[0] == "{":
            depth, end = 0, 0
            for i, c in enumerate(raw):
                if c == "{": depth += 1
                elif c == "}": depth -= 1
                if depth == 0:
                    end = i + 1
                    break
            raw = raw[:end]
        elif raw[0] == "[":
            depth, end = 0, 0
            for i, c in enumerate(raw):
                if c == "[": depth += 1
                elif c == "]": depth -= 1
                if depth == 0:
                    end = i + 1
                    break
            raw = raw[:end]

    return json.loads(raw)
