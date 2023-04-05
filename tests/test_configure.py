import os
from launchable_cli_args import CLIArgs


def test_configure_and_parse() -> None:
    test_conf_file_path = os.path.join('tests', 'unittest1.conf')
    args = CLIArgs.auto_configure("tests")

    args.write_as_yaml(test_conf_file_path)

    args = CLIArgs.from_yaml(path=test_conf_file_path)
    os.remove(test_conf_file_path)

    assert args.source_object["__fullpath__"].endswith(test_conf_file_path)
    assert args.error_counter.error_count == 1, "LAUNCHABLE_TOKEN warnings should be detected"
    args.error_counter.print_errors()


def test_command() -> None:
    args = CLIArgs.auto_configure("tests")
    args.build_id = "XXX"  # manually configured build id

    # at present, test only subset mode command.

    # record-only mode (default) / skip subset service, record test command only
    args.subset.mode = "record-only"
    assert args.subset.to_command() == ()

    # subset mode
    args.subset.mode = "subset"
    assert args.subset.to_command() == ("launchable", "subset", "--build",
                                        "XXX", "--confidence", 99, "pytest")

    # subset-and-rest mode
    args.subset.mode = "subset-and-rest"
    assert args.subset.to_command() == ("launchable", "subset", "--build", "XXX",
                                        "--confidence", 99, "--rest", args.subset.REST_FILE_NAME, "pytest")
