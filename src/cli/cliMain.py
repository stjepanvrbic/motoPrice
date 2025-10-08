"""CLI entry point for motoPrice."""

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="moto-eval")
def main():
    """Motorcycle listing evaluator.

    Analyze motorcycle listings to find great deals based on price, mileage,
    condition, and other factors.
    """
    pass


if __name__ == "__main__":
    main()
