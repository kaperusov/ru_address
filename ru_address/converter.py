import os
import glob
import datetime

from ru_address.source.xml import Definition
from ru_address.source.xml import Data
from ru_address._version import __version__


class Converter:
    TARGET_POSTGRES = 'pgsql'
    TARGET_MYSQL = 'mysql'

    SOURCE_XML = 'xml'
    SOURCE_DBF = 'dbf'

    TABLE_LIST = [
        'ACTSTAT',
        'ADDR_OBJ',
        'CENTERST',
        'CURENTST',
        'ESTSTAT',
        'FLATTYPE',
        'HOUSE',
        'NDOCTYPE',
        'NORMDOC',
        'OPERSTAT',
        'ROOMTYPE',
        'ROOM',
        'SOCRBASE',
        'STEAD',
        'STRSTAT'
    ]

    def __init__(self, source, source_path, beta):
        self.source = source
        self.source_path = source_path
        self.beta = beta

    def get_source_filepath(self, table, extension):
        """ Ищем файл таблицы в папке с исходниками, 
        Названия файлов в непонятном формате, например AS_ACTSTAT_2_250_08_04_01_01.xsd
        """
        file = 'AS_{}_*.{}'.format(table, extension)
        file_path = os.path.join(self.source_path, file)
        found_files = glob.glob(file_path)
        if len(found_files) == 1:
            return found_files[0]
        elif len(found_files) > 1:
            raise FileNotFoundError('More than one file found: {}'.format(file_path))
        else:
            raise FileNotFoundError('Not found source file: {}'.format(file_path))

    def convert_table(self, file, schema, table, target, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и XML файлы. """
        if self.source == self.SOURCE_XML:
            self._convert_table_xml(file, schema, table, target, skip_definition, skip_data, batch_size)
        elif self.source == self.SOURCE_DBF:
            self._convert_table_dbf(file, schema, table, target, skip_definition, skip_data, batch_size)

    def _convert_table_xml(self, file, schema, table, target, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и XML файлы. """
        dump_file = file

        source_filepath = self.get_source_filepath(table, 'xsd')
        definition = Definition(schema, table, source_filepath, target)
        if skip_definition is False:
            definition.convert_and_dump(dump_file)

        if skip_data is False:
            source_filepath = self.get_source_filepath(table, 'xml')
            data = Data(table, source_filepath)
            if self.beta:
                data.convert_and_dump_v2(dump_file, definition, batch_size)
            else:
                data.convert_and_dump(dump_file, definition, batch_size)

    def _convert_table_dbf(self, schema, table, target, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и DBF файлы. """
        print('TODO!')

    @staticmethod
    def prepare_table_input(table_list_string):
        """ Подготавливает переданный через аргумент список таблиц """
        table_list = table_list_string.split(',')
        for table in table_list:
            if table not in Converter.TABLE_LIST:
                raise ValueError('Unknown table "{}"'.format(table))
        return table_list

    @staticmethod
    def get_dump_copyright():
        """ Сообщение в заголовок сгенерированного файла """
        header = ("-- --------------------------------------------------------\n"
                  "-- ver. {}\n"
                  "-- get latest version @ https://github.com/shadz3rg/ru_address\n"
                  "-- file generated {}\n"
                  "-- --------------------------------------------------------\n\n")
        now = datetime.datetime.now()
        return header.format(__version__, str(now))

    @staticmethod
    def get_dump_header(target, encoding):
        """ Подготовка к импорту """
        if target == Converter.TARGET_MYSQL:
            header = ("/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;\n"
                      "/*!40101 SET NAMES {} */;\n"
                      "/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;\n"
                      "/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;\n")
            return header.format(encoding)
        elif target == Converter.TARGET_POSTGRES:
            return ""

    @staticmethod
    def get_dump_footer(target):
        """ Завершение импорта """
        if target == Converter.TARGET_MYSQL:
            footer = ("\n/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;\n"
                      "/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;\n"
                      "/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;")
            return footer
        elif target == Converter.TARGET_POSTGRES:
            return ""

    @staticmethod
    def get_table_separator(table):
        return "\n\n-- Table `{}`\n".format(table)


class Output:
    SINGLE_FILE = 0
    FILE_PER_TABLE = 1

    def __init__(self, output_path, mode):
        self.output_path = output_path
        self.mode = mode

    def get_table_filename(self, table):
        return '{}.{}'.format(table, 'sql')

    def open_dump_file(self, filename):
        filepath = os.path.join(self.output_path, filename)
        return open(filepath, 'w', encoding='utf-8')
