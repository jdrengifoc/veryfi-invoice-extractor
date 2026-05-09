# scripts/sandbox.py

from veryfi import Client
import os
from dotenv import load_dotenv
from veryfi_invoice_extractor.paths import ROOT
from veryfi_invoice_extractor.client import build_client

# Load secrets.
load_dotenv()


def load_secret(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}. ")

    return value


if __name__ == "__main__":
    client = build_client()
    print(client)

    # response = client.process_document(
    #     file_path="data/documents/synth-switch_v5-4.pdf",
    #     categories=["invoice"],
    # )

    # print(response)
