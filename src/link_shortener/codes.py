"""Random short-code generator."""

import secrets

from link_shortener.domain import CODE_ALPHABET, CODE_LENGTH


class RandomCodeGenerator:
    def generate(self) -> str:
        return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
