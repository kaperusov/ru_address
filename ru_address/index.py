import lxml.etree as et
import os.path
from ru_address import package_directory


class Index:
    def __init__(self, target, schema):
        self.schema = schema
        self.stylesheet_file = os.path.join(package_directory, 'resources', target, 'index.xsl')
        self.index_file = os.path.join(package_directory, 'resources', target, 'index.xml')
        self.index_tree = et.parse(self.index_file)

    def build(self, table_name):
        stylesheet = et.parse(self.stylesheet_file)
        transform = et.XSLT(stylesheet)

        plain_schema_name = transform.strparam(self.schema)
        plain_table_name = transform.strparam(table_name)
        result = transform(self.index_tree, schema=plain_schema_name, table_name=plain_table_name)
        return str(result)
