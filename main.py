import argparse
import importlib
import os.path
import shutil
import subprocess

import yaml

import jinja2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo_full_name", dest="repo_full_name", help="user/repo_name"
    )
    parser.add_argument("--output", dest="output", default="webified")
    parser.add_argument("--templates-dir", dest="templates_dir", default="templates")
    parser.add_argument("--src-dir", dest="src_dir", default="src")
    parser.add_argument("--globals-file", dest="globals_file", default="globals")
    args = parser.parse_args()

    if os.path.exists(args.output):
        shutil.rmtree(args.output)

    Parser(
        output=args.output,
        src_dir=args.src_dir,
        templates_dir=args.templates_dir,
        globals_file=args.globals_file,
    ).parse()


class Parser:
    def __init__(self, output, src_dir, templates_dir, globals_file):
        self.output = output
        self.src_dir = src_dir
        self.templates_dir = templates_dir
        self.environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader([self.src_dir, self.templates_dir])
        )
        self.globals_cls = importlib.import_module(globals_file).Globals

    def get_globals(self, index_path, context):
        return self.globals_cls(src_dir=self.src_dir, index_path=index_path, environment=self.environment, context=context).get()

    def parse(self):

        self.copy_content()
        pages = self.find_pages()
        for index_path in pages:
            self.parse_page(index_path)

    def copy_content(self):
        self.copy_folder("assets")
        self.copy_file("favicon.ico")

    def parse_page(self, index_path):
        
        if os.name == "nt":  # Windows
            rel_index_path = os.path.relpath(index_path, self.src_dir).replace("\\", "/")
        else:
            rel_index_path = os.path.relpath(index_path, self.src_dir)
        output_file = os.path.join(
            self.output,
            rel_index_path,
        )
        result = self.environment.get_template(rel_index_path).render(
            self.get_context(index_path)
        )
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as output:
            output.write(result)
        print(f"Rendered {index_path} -> {output_file}")

    def get_context(self, index_path) -> dict:
        context_path = os.path.join(os.path.dirname(index_path), "context.yml")
        if os.path.exists(context_path):
            with open(context_path) as f:
                context = yaml.safe_load(f) or {}
        else:
            context = {}
        context.update(self.get_globals(index_path, context))
        return context

    def find_pages(self):
        result = []

        for base, _, files in os.walk(self.src_dir):
            for file in files:
                if file == "index.html":
                    abs_file = os.path.join(base, file)
                    result.append(abs_file)
        
        return result

    def copy_folder(self, path, dest_relative_path=""):
        if not dest_relative_path:
            dest_relative_path = os.path.basename(path)
        dest_path = os.path.join(self.output, dest_relative_path)
        shutil.copytree(path, dest_path)
        print(f"Copied {path} -> {dest_path}")

    def copy_file(self, path, dest_relative_path=""):
        dest_path = os.path.join(self.output, dest_relative_path)
        shutil.copy(path, dest_path)
        print(f"Copied {path} -> {dest_path}")


if __name__ == "__main__":
    main()
