import argparse
import inspect
import os

import configargparse
import logging

import sys
from appdirs import AppDirs

from pynYNAB.Client import clientfromargs
from pynYNAB.scripts.csvimport import do_csvimport
from pynYNAB.scripts.ofximport import do_ofximport

configfile = 'ynab.conf'
if not os.path.exists(configfile):
    myAppdir = AppDirs('pynYNAB').user_config_dir
    configfile = os.path.join(myAppdir, configfile)

LOG = logging.getLogger(__name__)


class MainCommands(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='nYnab-CLI using the python API',
            usage='''nynab <command> [<args>]

            ''')
        argcommands = parser.add_argument('command', help='Subcommand to run',choices=['csvimport','ofximport'])
        parser.usage += 'commands : '+','.join(argcommands.choices)
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def csvimport(self):
        print('pynYNAB CSV import')
        """Manually import a CSV into a nYNAB budget"""
        parser = configargparse.getArgumentParser('pynYNAB')
        parser.description = inspect.getdoc(self.csvimport)
        parser.add_argument('csvfile', metavar='CSVpath', type=str,
                            help='The CSV file to import')
        parser.add_argument('schema', metavar='schemaName', type=str,
                            help='The CSV schema to use (see csv_schemas directory)')
        parser.add_argument('accountname', metavar='AccountName', type=str, nargs='?',
                            help='The nYNAB account name  to use')
        parser.add_argument('-import-duplicates', action='store_true',
                            help='Forces the import even if a duplicate (same date, account, amount, memo, payee) is found')

        args = parser.parse_args()
        verify_common_args(args)

        if not os.path.exists(args.csvfile):
            LOG.error('input CSV file does not exist')
            exit(-1)

        client = clientfromargs(args)
        delta = do_csvimport(args,client)
        client.push(expected_delta=delta)


    def ofximport(self):
        print('pynYNAB OFX import')
        """Manually import an OFX into a nYNAB budget"""

        parser = configargparse.getArgumentParser('pynYNAB')
        parser.description = inspect.getdoc(self.ofximport)
        parser.add_argument('ofxfile', metavar='OFXPath', type=str,
                            help='The OFX file to import')

        args = parser.parse_args()
        verify_common_args(args)
        client = clientfromargs(args)
        delta = do_ofximport(args,client)
        client.push(expected_delta=delta)


def verify_common_args(args):
    if args.email is None:
        LOG.error('No email user ID provided, please specify it at the command line or in %s' % (configfile,))
        exit(-1)
    if args.password is None:
        LOG.error('No password provided, please specify it at the command line or in %s' % (configfile,))
        exit(-1)
    if args.budgetname is None:
        LOG.error('No budget name provided, please specify it at the command line or in %s' % (configfile,))
        exit(-1)


parser = configargparse.getArgumentParser('pynYNAB', default_config_files=[configfile],
                                          add_env_var_help=True,
                                          add_config_file_help=True,
                                          auto_env_var_prefix='NYNAB_')

parser.add_argument('--email', metavar='Email', type=str, required=False,
                    help='The Email User ID for nYNAB')
parser.add_argument('--password', metavar='Password', type=str, required=False,
                    help='The Password for nYNAB')
parser.add_argument('--budgetname', metavar='BudgetName', type=str, required=False,
                    help='The nYNAB budget to use')

def main():
    MainCommands()