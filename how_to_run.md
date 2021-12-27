
# WARNING: This project is written and tested in **Debian GNU/Linux bookworm/sid x86_64**, AVOID USING WINDOWS, MACOS and WSL to run this project.

# Python Version: 3.10, Please don't any older version

```
> python3 --version
Python 3.10.1
```

## How to Run in CommandLine

1. Put test files into "./tests/test_files"
2. Use the project root path as the working directory
3. Use `PYTHONPATH=$(pwd) python3 tests/ComplexTest.py` to start one test
4. Your command line should look like this:

    `yuk1@~/Desktop/cs305_p2p ➜ PYTHONPATH=$(pwd) python3 tests/ComplexTest.py`

5. Only this method is tested in command line.

## How to Run in PyCharm

1. Click the green Run button when opening the ComplexTest file.
2. Edit the Run Configuration, change the working directory to the root of this project.