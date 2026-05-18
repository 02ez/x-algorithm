"""Entry point for ``python -m x_publish_lint``."""

from x_publish_lint.cli import app


def main() -> None:
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":
    main()
