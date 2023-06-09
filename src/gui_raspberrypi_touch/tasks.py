from invoke import task


@task
def check(c):
    """Runs all the linters."""
    c.run("python -m black -l 100 main.py")
    c.run("python -m pylint main.py")
    c.run("python -m mypy .")
    c.run("python -m pydocstyle main.py")
