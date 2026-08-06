from enum import StrEnum

__all__ = ()

class Colours(StrEnum):
    """Enum class containing codes for most console colours. (Added in v2.0)"""
    GREEN = "\u001b[32m"
    BLUE = "\u001b[36m"
    CLAY = "\u001b[38;5;51m"
    PURPLE = "\u001b[38;5;200m"
    RED = "\u001b[31m"
    BOLD_RED = "\u001b[31;1m"
    PINK_GREY = "\u001b[38;5;139m"
    GREY = "\u001b[1;37;30m"
    YELLOW = "\u001b[33;20m"
    ORANGE = "\u001b[38;5;214m"
    WHITE = "\u001b[1;37;40m"

    RESET = "\u001b[0m"
    RESET_COLOUR = "\u001b[0m"

    def apply(self, string: str) -> str:
        """Returns that string but with this colour applied to it."""

        return self.value + string + self.RESET_COLOUR