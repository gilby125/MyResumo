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
    const heading = page.getByRole('heading', { name: /Create a New Resume/i });
    await expect(heading).toBeVisible();
    
    // Check for the file upload area
    const fileUploadArea = page.locator('.dropzone');
    await expect(fileUploadArea).toBeVisible();
    
    // Check for the job description textarea
    const jobDescriptionTextarea = page.getByPlaceholder(/Paste the job description here/i);
    await expect(jobDescriptionTextarea).toBeVisible();
    
    // Check for the job title input
    const jobTitleInput = page.getByPlaceholder(/e.g. Software Engineer/i);
    await expect(jobTitleInput).toBeVisible();
  });

  test('should have a multi-step process', async ({ page }) => {
    // Check for step indicators
    const stepIndicators = page.locator('.step-indicator');
    await expect(stepIndicators).toHaveCount(3); // Assuming 3 steps in the process
    
    // Check that the first step is active
    const activeStep = page.locator('.step-indicator.active');
    await expect(activeStep).toHaveCount(1);
    await expect(activeStep).toContainText('Upload Resume');
  });

  test('should show validation when trying to proceed without inputs', async ({ page }) => {
    // Try to proceed without uploading a file
    const nextButton = page.getByRole('button', { name: /Next/i });
    await nextButton.click();
    
    // Check for validation message
    const validationMessage = page.getByText(/Please upload a resume file/i);
    await expect(validationMessage).toBeVisible();
  });

  test('should allow entering job description', async ({ page }) => {
    // Enter job description
    const jobDescriptionTextarea = page.getByPlaceholder(/Paste the job description here/i);
    await jobDescriptionTextarea.fill('This is a test job description for a software engineer position requiring skills in JavaScript, React, and Node.js.');
    
    // Enter job title
    const jobTitleInput = page.getByPlaceholder(/e.g. Software Engineer/i);
    await jobTitleInput.fill('Software Engineer');
    
    // Verify the inputs were accepted
    await expect(jobDescriptionTextarea).toHaveValue('This is a test job description for a software engineer position requiring skills in JavaScript, React, and Node.js.');
    await expect(jobTitleInput).toHaveValue('Software Engineer');
  });
});
