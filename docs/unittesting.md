# Unit Testing Guide
Unit testing allows automated testing of code units to validating that each unit of the software performs as designed. If you don't know why this is important read some of the links below.

## Useful links
- [Getting Started With Testing in Python](https://realpython.com/python-testing/)
- [Basic patterns and examples](https://docs.pytest.org/en/latest/example/simple.html)
- [An Introduction to Mocking in Python](https://www.toptal.com/python/an-introduction-to-mocking-in-python)
- [Unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

## Project Implementation
Within this project all unit tests are help within the tests folder. Each module will have it's own test script with the file name relating to its as shown in the example file tree below.
```
├── tests
│   ├── context.py
│   ├── test_module_1.py
│   └── test_submodule_module_2.py
└── modules
    ├── module_1.py
    ├── submodule_1
        └── module_2.py
```

A unit test template is shown below n.b. test names should be as verbose as possible. 

```python
from unittest import TestCase
from context import modules

from modules import module_1.py

class test_module_1(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def test_1(self):
        self.assertTrue(True)
```

The file `context.py` provides root directory context and must be included at the top of each test file.
