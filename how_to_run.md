
# WARNING: This project is written and tested in **Debian GNU/Linux bookworm/sid x86_64**, AVOID USING WINDOWS, MACOS and WSL to run this project.

# Python Version: 3.10, Please don't use any older version

zh update: tested and passed on windows10, python 3.9 also

```
> python3 --version
Python 3.10.1
```

## How to Run in CommandLine

1. Put test files into `test_files`
2. Launch tracker first, see [How to Run Tracker](#how-to-run-tracker).
3. Use path `test` as the working directory
4. add project root directory into `PYTHONPATH`
5. Run `python3 the_test.py` to start one test
6. Your command line should look like this:
   
    `yuk1@~/Desktop/cs305_p2p/ ➜ cd test && PYTHONPATH=../ python3 ComplexTest.py`

7. Only this method is tested in command line.

## How to Run in PyCharm

1. Simply click the green Run button, the working directory is set to be where the script is by default.

## How to Run Tracker

1. Run `python3 Tracker.py` in project root directory.
