import os
import sys
import argparse
from launchable_cli_args import CLIArgs


def main() -> int:
    parser = argparse.ArgumentParser(
        description='generate/verify launchable test runner configuration file')
    parser.add_argument('--file', dest="file",
                        default=".launchable.d/config.yml", help='configuration file name')
    parser.add_argument('--create', action="store_true",
                        help='create new configuration file by standard settings')
    parser.add_argument('--verify', action="store_true",
                        help='verify existing configuration file')

    args = parser.parse_args()
    path = args.file

    exit_code = 0
    if args.verify:
        if os.path.isfile(path):
            print("verifying configuration file %s..." %
                  (os.path.join(os.getcwd(), path)))
            conf = CLIArgs.from_yaml(path)
            if conf.error_counter.error_count == 0:
                print("No obvious errors were found. Please try actual test session!")
            else:
                conf.error_counter.print_errors()
                exit_code = 1
        else:
            print("%s does not exist." % path)
            exit_code = 1
    elif args.create:
        conf = CLIArgs.auto_configure(os.getcwd())
        conf.write_as_yaml(path)
        print("Launchable configuration file is written to %s" %
              (os.path.join(os.getcwd(), path)))
    else:
        print("one of --create or --verify must be specified")
        exit_code = 1
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
