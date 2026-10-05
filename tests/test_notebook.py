from pathlib import Path
import ast
import nbformat


def test_colab_notebook_schema_and_code_syntax():
    for path in Path("notebooks").glob("marketforecast*colab.ipynb"):
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        for cell in notebook.cells:
            if cell.cell_type == "code":
                ast.parse(cell.source)
                assert cell.outputs == []
                assert cell.execution_count is None

