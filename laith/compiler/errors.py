from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class SourceLocation:
    line: int
    col: int
    source: Optional[str] = None

    def format(self, context_lines: int = 2) -> str:
        if not self.source:
            return f"  at line {self.line}, column {self.col}"
        lines = self.source.split("\n")
        start = max(0, self.line - 1 - context_lines)
        end = min(len(lines), self.line + context_lines)
        out = []
        for i in range(start, end):
            marker = ">" if i == self.line - 1 else " "
            out.append(f"  {marker} {i+1:4d} | {lines[i]}")
            if i == self.line - 1:
                out.append(f"       {' ' * self.col}^")
        return "\n".join(out)


class CompileError(Exception):
    def __init__(
        self,
        message: str,
        location: Optional[SourceLocation] = None,
        hint: Optional[str] = None,
    ):
        self.message = message
        self.location = location
        self.hint = hint
        super().__init__(str(self))

    def __str__(self) -> str:
        parts = [f"[bold red]Error:[/bold red] {self.message}"]
        if self.location:
            parts.append(self.location.format())
        if self.hint:
            parts.append(f"[yellow]Hint:[/yellow] {self.hint}")
        return "\n".join(parts)

    def __repr__(self) -> str:
        return f"CompileError({self.message!r}, location={self.location!r}, hint={self.hint!r})"


class TypeError(CompileError):
    def __init__(
        self,
        message: str,
        expected: str,
        got: str,
        location: Optional[SourceLocation] = None,
    ):
        hint = f"Expected type [bold]{expected}[/bold] but got [bold]{got}[/bold]"
        super().__init__(message, location=location, hint=hint)


class UndefinedSymbolError(CompileError):
    def __init__(self, name: str, location: Optional[SourceLocation] = None):
        hint = f"Did you forget to define [bold]{name}[/bold] or import it?"
        super().__init__(
            f"Undefined symbol [bold]{name}[/bold]",
            location=location,
            hint=hint,
        )


class UnsupportedFeatureError(CompileError):
    def __init__(self, feature: str, location: Optional[SourceLocation] = None):
        hint = f"This feature is not yet implemented in Laith"
        super().__init__(
            f"Unsupported feature: [bold]{feature}[/bold]",
            location=location,
            hint=hint,
        )
