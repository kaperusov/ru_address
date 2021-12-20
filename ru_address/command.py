import click
import time

from . import __version__
from ru_address.converter import Converter
from ru_address.converter import Output
from ru_address.common import Common


@click.command()
@click.option('--join', type=str, 
              help='Опция позволяет объединить весь дамп в один файл (по умолчанию отдельный файл для каждой таблицы).\n\n ')
@click.option('--source', type=click.Choice([Converter.SOURCE_XML, Converter.SOURCE_DBF]), 
              help='Формат источника данных.\n\nВозможные варианты: xml | dbf.\n\nПо умолчанию "xml". "dbf" пока не реализован.\n\n ',
              default=Converter.SOURCE_XML)
@click.option('--sql-syntax', type=click.Choice([Converter.SQL_SYNTAX_PGSQL, Converter.SQL_SYNTAX_MYSQL]),
              help='SQL формат выходных файлов (по умолчанию "pgsql").\n\n ',
              default=Converter.SQL_SYNTAX_PGSQL)
@click.option('--db-schema', type=str, 
              help='Имя схемы в БД (только PostgreSQL), по умолчанию: "gar").\n\n ', 
              default='gar')
@click.option('--xsd-schema', type=str, 
              help='Тип XSD схемы. Возможные варианты: gar | fias. (По умолчанию: "gar").\n\n ', 
              default='gar')
@click.option('--table-list', type=str, 
              help='Список таблиц для обработки, указывается строкой с разделением запятой.\n\n ')
@click.option('--no-data', is_flag=True, 
              help='Не генерировать в результирующем файле инструкуции для вставки данных в таблицы.\n\n ')
@click.option('--no-definition', is_flag=True, 
              help='Пропустить создание схемы.\n\n ')
@click.option('--encoding', type=str, default='utf8mb4', 
              help='Кодировка таблицы, по умолчанию "utf8mb4" (только для MySQL).\n\n ')
@click.option('--beta', is_flag=True, help='Отладочный флаг. Для проверки работы методов.\n\n ')
@click.argument('source_path', type=click.types.Path(exists=True, file_okay=False, readable=True))
@click.argument('output_path', type=click.types.Path(exists=True, file_okay=False, readable=True, writable=True))
@click.version_option(version=__version__)
def cli(join, source, sql_syntax, xsd_schema, db_schema, table_list, no_data, no_definition, encoding, beta, source_path, output_path):
    """ Подготавливает БД ФИАС для использования с SQL.
    XSD файлы и XML выгрузку можно получить на сайте ФНС https://fias.nalog.ru/Updates.aspx

    Для автоматицации выгрузки, можно воспользоваться shell-скриптом: download_schemas.sh
    """
    start_time = time.time()

    if xsd_schema == "gar":
        process_tables = Converter.TABLE_LIST_GAR
    elif xsd_schema == "fias":
        process_tables = Converter.TABLE_LIST_FIAS
    else:
        print("Неизвестная схема '{}'. Возможные варианты: gar | fias".format(xsd_schema))
        exit

    if table_list is not None:
        process_tables = Converter.prepare_table_input(table_list)

    mode = Output.FILE_PER_TABLE
    if join is not None:
        mode = Output.SINGLE_FILE

    output = Output(output_path, mode)
    converter = Converter(source, source_path, beta)

    if mode == Output.SINGLE_FILE:
        file = output.open_dump_file(join)
        file.write(Converter.get_dump_copyright())
        file.write(Converter.get_dump_header(encoding=encoding, sql_syntax=sql_syntax, schema=db_schema))

        for table in process_tables:
            Common.cli_output('Processing table `{}`'.format(table))
            file.write(Converter.get_table_separator(table))
            converter.convert_table(file=file, sql_syntax=sql_syntax, schema=db_schema, table=table,
                                    skip_definition=no_definition, skip_data=no_data,
                                    batch_size=500)

        file.write(Converter.get_dump_footer(sql_syntax=sql_syntax))
        file.close()

    elif mode == Output.FILE_PER_TABLE:
        for table in process_tables:
            file = output.open_dump_file(output.get_table_filename(table))
            file.write(Converter.get_dump_copyright())
            file.write(Converter.get_dump_header(encoding=encoding, sql_syntax=sql_syntax))

            Common.cli_output('Processing table `{}`'.format(table))
            converter.convert_table(file=file, sql_syntax=sql_syntax, schema=db_schema, table=table,
                                    skip_definition=no_definition, skip_data=no_data,
                                    batch_size=500)

            file.write(Converter.get_dump_footer(sql_syntax=sql_syntax))
            file.close()

    Common.show_memory_usage()
    time_measure = time.time() - start_time
    print("{} s".format(round(time_measure, 2)))
