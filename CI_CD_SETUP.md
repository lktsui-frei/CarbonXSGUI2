# GitLab CI/CD Setup for CarbonXS GUI

## Overview

This project is configured to automatically run tests using GitLab CI/CD whenever changes are pushed to the repository. The configuration is defined in `.gitlab-ci.yml`.

## How It Works

### Triggering the Pipeline

The CI/CD pipeline automatically runs on:
- **Every push** to any branch
- **Every merge request**

### Pipeline Stages

The pipeline consists of a single stage:

1. **Test Stage**: Runs all Python tests using pytest

### Test Execution

The pipeline:
- Uses Python 3.11 Docker image
- Installs dependencies from `requirements.txt`
- Runs all tests in the `tests/` directory
- Automatically skips deprecated tests (marked with `@pytest.mark.skip`)
- Automatically skips tests requiring Fortran reference data if unavailable

### Verification: Tests Can Run Without Fortran Code

✅ **Confirmed**: All Python tests can run independently without requiring Fortran code compilation or execution.

The tests that reference Fortran:
- **`test_fit_verification.py`**: Marked as `@pytest.mark.skip` (deprecated), automatically skipped
- **`test_port_verification.py`**: Uses `@pytest.mark.skipif` to skip if reference data unavailable
- **`test_regression.py`**: Reads Fortran output files but doesn't execute Fortran code

None of these tests execute Fortran binaries - they only read reference data files from the `carbonxs/` directory for comparison.

## Viewing Pipeline Results

After pushing changes to GitLab:

1. Navigate to your project on GitLab
2. Go to **CI/CD > Pipelines**
3. Click on the pipeline for your commit
4. View detailed test results and logs

## Pipeline Configuration Details

### Python Version
- Python 3.11 (can be changed by modifying the `image` directive in `.gitlab-ci.yml`)

### Dependencies
- All dependencies are installed from `requirements.txt`
- Pip packages are cached between pipeline runs for faster execution

### Test Output
- Verbose test output (`-v`) for detailed results
- Short traceback format (`--tb=short`) for easier debugging
- Test results are saved as JUnit XML artifacts (available for 1 week)

## Future Enhancements

The following features are commented out in `.gitlab-ci.yml` and can be enabled later:

### Code Coverage
Uncomment the `coverage` job to:
- Generate test coverage reports
- Display coverage percentage in merge requests
- Track coverage trends over time

### Code Quality Checks
Can be added in future iterations:
- **Linting**: Add `flake8` or `pylint` to check code quality
- **Formatting**: Add `black` to verify code formatting
- **Type Checking**: Add `mypy` for static type checking

## Customization

### Changing Python Version

Edit the `image` line in `.gitlab-ci.yml`:
```yaml
image: python:3.10  # or python:3.9, python:3.12, etc.
```

### Running Specific Tests Only

Modify the pytest command in the `test` job:
```yaml
- pytest tests/test_core.py tests/test_fit.py -v  # Run specific test files
```

### Excluding Specific Tests

Use pytest's `-k` option:
```yaml
- pytest tests/ -v -k "not slow"  # Skip tests marked as slow
```

## Troubleshooting

### Pipeline Fails on Dependency Installation

- Check that all dependencies in `requirements.txt` are available for your Python version
- Some packages may require system libraries - add them to `before_script`:
  ```yaml
  before_script:
    - apt-get update && apt-get install -y libsome-dependency
    - pip install -r requirements.txt
  ```

### Tests Pass Locally but Fail in CI

- Ensure your tests don't depend on local files or environment-specific settings
- Check that all test data files are committed to the repository
- Verify that tests don't rely on absolute paths

### Pipeline Takes Too Long

- Enable caching (already configured for pip packages)
- Run only critical tests in the main pipeline
- Move slower integration tests to a scheduled pipeline

## Related Files

- **`.gitlab-ci.yml`**: Main CI/CD configuration file
- **`requirements.txt`**: Python dependencies
- **`tests/`**: All test files
- **`pytest.ini`** (optional): Can be created for pytest configuration

## Additional Resources

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [pytest Documentation](https://docs.pytest.org/)
- [Python Docker Images](https://hub.docker.com/_/python)
