from link_shortener.codes import RandomCodeGenerator
from link_shortener.domain import CODE_ALPHABET, CODE_LENGTH, is_valid_code


def test_generated_code_has_length_six_and_is_valid() -> None:
    code = RandomCodeGenerator().generate()
    assert len(code) == CODE_LENGTH == 6
    assert is_valid_code(code)


def test_generated_codes_use_only_the_alphabet() -> None:
    gen = RandomCodeGenerator()
    assert all(set(gen.generate()) <= set(CODE_ALPHABET) for _ in range(200))


def test_many_draws_are_not_all_equal() -> None:
    gen = RandomCodeGenerator()
    assert len({gen.generate() for _ in range(50)}) > 1
