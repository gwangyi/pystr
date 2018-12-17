from paver.easy import *
from paver.setuputils import setup
import paver.doctools

here = path(__file__).abspath().dirname()

options = environment.options

options(
    minilib=Bunch(
        extra_files=['doctools'],
        versioned_name=False,
        extra_packages=['six']
    ),
    sphinx=Bunch(
        builddir="build",
        sourcedir="source"
    ),
)

setup(
    name="pystr",
    packages=["pystr"],
    version="0.1.0",
    url="https://github.com/gwangyi/pystr",
    author="Sungkwang Lee",
    author_email="gwangyi.kr@gmail.com",
    description="Packet analysis tool w/ cffi",
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["build.py:ffi"],
    install_requires=["cffi>=1.0.0"]
)

@task
def lint():
    sh('mypy --strict -p pystr')
    sh('pylint pystr')

@task
def test():
    sh('PYTHONPATH={} pytest --cov=./pystr --cov-branch --cov-report=html --cov-report=term'
       .format(path(__file__).abspath().dirname()))

@task
@needs('paver.doctools.html')
def html():
    builtdocs = path("docs") / options.sphinx.builddir / "html"
    destdir = path("pystr") / "docs"
    destdir.rmtree_p()
    builtdocs.move(destdir)
