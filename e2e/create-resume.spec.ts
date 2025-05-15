import { test, expect } from '@playwright/test';

/**
 * MyResumo Create Resume Tests
 *
 * These tests verify the functionality of the resume creation page.
 */

test.describe('Create Resume Page Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the create resume page before each test
    await page.goto('/create');

    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');
  });

  test('should have the correct title and form elements', async ({ page }) => {
    // Verify the page title
    await expect(page).toHaveTitle(/Create Resume - MyResumo/);

    // Check for the main heading
    const heading = page.getByRole('heading', { name: 'Create an Optimized Resume' });
    await expect(heading).toBeVisible();

    // Check for the file upload area
    const fileUploadArea = page.getByText('Drag and drop your resume here');
    await expect(fileUploadArea).toBeVisible();

    // Check for the job description textarea
    const jobDescriptionTextarea = page.getByLabel('Job Description *');
    await expect(jobDescriptionTextarea).toBeVisible();

    // Check for the job title input
    const jobTitleInput = page.getByLabel('Job Title');
    await expect(jobTitleInput).toBeVisible();
  });

  test('should have a multi-step process', async ({ page }) => {
    // Check for step labels directly
    await expect(page.getByText('Upload', { exact: true })).toBeVisible();
    await expect(page.getByText('Analyze', { exact: true })).toBeVisible();
    await expect(page.getByText('Review', { exact: true })).toBeVisible();
    await expect(page.getByText('Results', { exact: true })).toBeVisible();

    // Verify we have step numbers (1, 2, 3, 4)
    await expect(page.getByText('1', { exact: true })).toBeVisible();
    await expect(page.getByText('2', { exact: true })).toBeVisible();
    await expect(page.getByText('3', { exact: true })).toBeVisible();
    await expect(page.getByText('4', { exact: true })).toBeVisible();
  });

  test('should have disabled analyze button without inputs', async ({ page }) => {
    // Check that the Analyze Resume button is disabled initially
    const analyzeButton = page.getByRole('button', { name: 'Analyze Resume' });
    await expect(analyzeButton).toBeDisabled();

    // Fill in the job description but still no file
    const jobDescriptionTextarea = page.getByLabel('Job Description *');
    await jobDescriptionTextarea.fill('This is a test job description');

    // Button should still be disabled without a file upload
    await expect(analyzeButton).toBeDisabled();
  });

  test('should allow entering job description and title', async ({ page }) => {
    // Enter job description
    const jobDescriptionTextarea = page.getByLabel('Job Description *');
    await jobDescriptionTextarea.fill('This is a test job description for a software engineer position requiring skills in JavaScript, React, and Node.js.');

    // Enter job title
    const jobTitleInput = page.getByLabel('Job Title');
    await jobTitleInput.fill('Software Engineer');

    // Verify the inputs were accepted
    await expect(jobDescriptionTextarea).toHaveValue('This is a test job description for a software engineer position requiring skills in JavaScript, React, and Node.js.');
    await expect(jobTitleInput).toHaveValue('Software Engineer');
  });
});
