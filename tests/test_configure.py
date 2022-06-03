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

    # at the present, test only subset mode command.

    # default is subset mode
    assert args.subset.to_command() == ("launchable", "subset", "--build",
                                        "XXX", "--target", "30%", "pytest")

    # subset_and_rest mode
    args.subset.mode = "subset_and_rest"
    assert args.subset.to_command() == ("launchable", "subset", "--build", "XXX",
                                        "--target", "30%", "--rest", args.subset.REST_FILE_NAME, "pytest")

    # record_only mode / skip subset service, record test command only
    args.subset.mode = "record_only"
    assert args.subset.to_command() == ()
