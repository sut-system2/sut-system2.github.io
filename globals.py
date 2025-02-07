import os
from functools import cached_property
from pathlib import Path
from urllib.parse import urlparse

import jinja2
import yaml
import markdown


class Globals:
    def __init__(self, src_dir, index_path, environment, context):
        self.src_dir = src_dir
        self.index_path = index_path
        self.environment: jinja2.Environment = environment
        self.context = context

    def static(self, path):
        path = os.path.join("assets", path)
        return "/" + path.removeprefix("/")

    def load_header_context(self):
        directory = Path(self.index_path).resolve().parent
        while not os.path.isfile(directory / "header_context.yml"):
            if directory == directory.parent:
                raise Exception(
                    f"failed to find header_context.yml for {self.index_path}"
                )
            directory = directory.parent
        with open(directory / "header_context.yml") as f:
            return yaml.safe_load(f)

    @cached_property
    def index_url(self):
        current_path = os.path.relpath(os.path.dirname(self.index_path), self.src_dir)
        if current_path == ".":
            return "/"
        return os.path.normpath(current_path)

    @cached_property
    def base_url(self):
        parts = self.index_url.split(os.sep)
        if parts and parts[0] == "archive":
            return "/" + "/".join(parts[:2]) + "/"
        else:
            return "/"

    def get_nav_link(self, item):
        link = item["link"]
        return self.base_url + link.removeprefix("/")

    def static_or_abs_link(self, item):
        parsed = urlparse(item)
        if not parsed.netloc:
            return self.static(parsed.path)
        return item

    def sum_attr(self, list_, attr):
        return sum(int(x[attr]) for x in list_)

    def markdown(self, content):
        parsed = self.environment.from_string(content).render(self.context)
        return markdown.markdown(parsed, extensions=["nl2br", "mdx_math"])

    def local_file_with_icon(self, path, extension=None):
        url = self.static(path)
        file_name = os.path.basename(path)
        extension = extension or file_name.rsplit(".")[-1]
        if extension == "pdf":
            icon_class = "fa fa-file-pdf-o"
        elif extension == "zip":
            icon_class = "fa fa-file-zip-o"
        else:
            raise ValueError(f"Can't map file name '{file_name}' with extension {extension} to any icon")
        return f'<i class="{icon_class}"></i> [{file_name}]({url})'

    def get(self):
        return {
            "static": self.static,
            "header_context": self.load_header_context(),
            "get_nav_link": self.get_nav_link,
            "sum_attr": self.sum_attr,
            "markdown": self.markdown,
            "static_or_abs_link": self.static_or_abs_link,
            "current_url": self.index_url,
            "local_file_with_icon": self.local_file_with_icon,
        }
