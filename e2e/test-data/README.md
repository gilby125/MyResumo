# Test Data Directory

This directory contains test data files used in end-to-end tests.

## Files

- `sample-resume.pdf`: A sample resume PDF file for testing the resume upload and optimization functionality.

## Usage

These files are referenced in the end-to-end tests. For example, in the resume optimization tests:

```typescript
const SAMPLE_RESUME_PATH = path.join(__dirname, '../test-data/sample-resume.pdf');
```

## Adding Test Data

When adding new test data files:

1. Keep the files small to avoid bloating the repository
2. Document the purpose of each file in this README
3. Make sure the files are appropriate for testing (no sensitive or personal information)
4. Consider using mock data generators when possible instead of static files

## Note

You need to add a real PDF file named `sample-resume.pdf` to this directory for the resume upload tests to work. This file is not included in the repository to avoid copyright issues and to keep the repository size small.