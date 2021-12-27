import os
import glob
import datetime

from ru_address.source.xml import Definition
from ru_address.source.xml import Data
from ru_address._version import __version__
from ru_address._version import __repo_url__


class Converter:
    SQL_SYNTAX_PGSQL = 'pgsql'
    SQL_SYNTAX_MYSQL = 'mysql'

    SOURCE_XML = 'xml'
    SOURCE_DBF = 'dbf'

    TABLE_LIST_FIAS = [
        'ACTSTAT',
        'CENTERST',
        'CURENTST',
        'ESTSTAT',
        'FLATTYPE',
        'NDOCTYPE',
        'OPERSTAT',
        'ROOMTYPE',
        'SOCRBASE',
        'STRSTAT',
        'NORMDOC',
        'STEAD',
        'ROOM',
        'HOUSE',
        'ADDR_OBJ'
    ]

    TABLE_LIST_GAR = [
        'NORMATIVE_DOCS_KINDS',
        'NORMATIVE_DOCS_TYPES',
        'ROOM_TYPES',
        'PARAM_TYPES',
        'OPERATION_TYPES',
        'OBJECT_LEVELS',
        'HOUSE_TYPES',
        'APARTMENT_TYPES',
        'ADDR_OBJ_TYPES',
        'NORMATIVE_DOCS',
        'CHANGE_HISTORY',
        'ADM_HIERARCHY',
        'APARTMENTS',
        'CARPLACES',
        'ADDR_OBJ_DIVISION',
        'HOUSES',
        'MUN_HIERARCHY',
        'ADDR_OBJ',
        'PARAM',
        'REESTR_OBJECTS',
        'ROOMS',
        'STEADS'
    ]

    def __init__(self, source, source_path, beta):
        self.source = source
        self.source_path = source_path
        self.beta = beta

    def get_source_filepath(self, table, extension):
        """ Ищем файл таблицы в папке с исходниками, 
        Названия файлов в непонятном формате, например AS_ACTSTAT_2_250_08_04_01_01.xsd
        """
        file = 'AS_{}_[0-9]*.{}'.format(table, extension)
        file_path = os.path.join(self.source_path, file)
        found_files = glob.glob(file_path)
        if len(found_files) == 1:
            return found_files[0]
        elif len(found_files) > 1:
            raise FileNotFoundError('More than one file found: {}'.format(file_path))
        else:
            raise FileNotFoundError('Not found source file: {}'.format(file_path))

    def get_data_filepaths(self, table, extension):
        """ Ищем файлы с данными в папке с исходниками,
        Названия файлов в формате вида: 04/AS_ADDR_OBJ_DIVISION_20211203_3ba54d31-44ed-4410-8b4d-c40f42ec05e9.XML
        """
        file = '**/AS_{}_[0-9]*.{}'.format(table, extension)
        file_path = os.path.join(self.source_path, file)
        found_files = glob.glob(file_path, recursive=True)
        return found_files

    def convert_table(self, file, schema, table, sql_syntax, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и XML файлы. """
        if self.source == self.SOURCE_XML:
            self._convert_table_xml(file, schema, table, sql_syntax, skip_definition, skip_data, batch_size)
        elif self.source == self.SOURCE_DBF:
            self._convert_table_dbf(file, schema, table, sql_syntax, skip_definition, skip_data, batch_size)

    def _convert_table_xml(self, file, schema, table, sql_syntax, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и XML файлы. """
        dump_file = file

        source_filepath = self.get_source_filepath(table, 'xsd')
        definition = Definition(schema, table, source_filepath, sql_syntax)
        if skip_definition is False:
            definition.convert_and_dump(dump_file)

        if skip_data is False:
            try:
                paths = self.get_data_filepaths(table, 'XML')
                for source_filepath in paths:
                    data = Data(sql_syntax=sql_syntax, db_schema=schema, table_name=table, source_file=source_filepath)
                    if self.beta:
                        data.convert_and_dump_v2(dump_file, definition, batch_size)
                    else:
                        data.convert_and_dump(dump_file, definition, batch_size)
            except FileNotFoundError as err:
                print(err)

    def _convert_table_dbf(self, schema, table, sql_syntax, skip_definition, skip_data, batch_size):
        """ Конвертирует схему и данные таблицы, используя соответствующие XSD и DBF файлы. """
        print('TODO!')

    @staticmethod
    def prepare_table_input(table_list_string, xsd_schema):
        """ Подготавливает переданный через аргумент список таблиц """

        if xsd_schema == "gar":
            table_list = Converter.TABLE_LIST_GAR
        elif xsd_schema == "fias":
            table_list = Converter.TABLE_LIST_FIAS
        else:
            print("Неизвестная схема '{}'. Возможные варианты: gar | fias".format(xsd_schema))
            return []

        if table_list_string is not None:
            process_tables = table_list_string.split(',')
            for table in process_tables:
                if table not in table_list:
                    raise ValueError('Unknown table "{}"'.format(table))
            if process_tables is not None:
                return process_tables

        return table_list

    @staticmethod
    def get_dump_copyright():
        """ Сообщение в заголовок сгенерированного файла """
        header = ("-- --------------------------------------------------------\n"
                  "-- ver. {}\n"
                  "-- get latest version @ {}\n"
                  "-- file generated {}\n"
                  "-- --------------------------------------------------------\n\n")
        now = datetime.datetime.now()
        return header.format(__version__, __repo_url__, str(now))

    @staticmethod
    def get_dump_header(sql_syntax, encoding, schema):
        """ Подготовка к импорту """
        if sql_syntax == Converter.SQL_SYNTAX_MYSQL:
            header = ("/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;\n"
                      "/*!40101 SET NAMES {} */;\n"
                      "/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;\n"
                      "/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;\n")
            return header.format(encoding)
        elif sql_syntax == Converter.SQL_SYNTAX_PGSQL:
            header = "\nCREATE SCHEMA IF NOT EXISTS \"{}\";\n"
            return header.format(schema)

    @staticmethod
    def get_dump_footer(sql_syntax):
        """ Завершение импорта """
        if sql_syntax == Converter.SQL_SYNTAX_MYSQL:
            footer = ("\n/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;\n"
                      "/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;\n"
                      "/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;")
            return footer
        elif sql_syntax == Converter.SQL_SYNTAX_PGSQL:
            return ""

    @staticmethod
    def get_table_separator(table):
        return "\n\n-- Table {}\n".format(table)


class Output:
    SINGLE_FILE = 0
    FILE_PER_TABLE = 1

    def __init__(self, output_path, mode):
        self.output_path = output_path
        self.mode = mode

    @staticmethod
    def get_table_filename(index, table):
        return '{:03d}_{}.{}'.format(index, table, 'sql')

    def open_dump_file(self, filename):
        filepath = os.path.join(self.output_path, filename)
        return open(filepath, 'w', encoding='utf-8')
