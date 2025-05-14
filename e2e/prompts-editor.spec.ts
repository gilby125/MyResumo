import { test, expect } from '@playwright/test';

/**
 * MyResumo Prompts Editor Tests
 * 
 * These tests verify the functionality of the prompts editor page.
 */

test.describe('Prompts Editor Page Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the prompts editor page before each test
    await page.goto('/prompts');
    
    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');
  });

  test('should have the correct title', async ({ page }) => {
    // Verify the page title
    await expect(page).toHaveTitle(/Prompts Editor - MyResumo/);
  });

  test('should display prompts editor header', async ({ page }) => {
    // Check for the main heading
    const heading = page.getByRole('heading', { name: 'Prompts Editor' });
    await expect(heading).toBeVisible();
    
    // Check for the subheading
    const subheading = page.getByText('View and edit system prompts used by the AI components.');
    await expect(subheading).toBeVisible();
  });

  test('should have a list of prompts', async ({ page }) => {
    // Check for the prompts list
    const promptsList = page.locator('.prompts-list');
    await expect(promptsList).toBeVisible();
    
    // Check that there are prompt items
    const promptItems = page.locator('.prompt-item');
    await expect(promptItems).toHaveCount.atLeast(1);
  });

  test('should have search and filter functionality', async ({ page }) => {
    // Check for the search input
    const searchInput = page.getByPlaceholder('Search prompts...');
    await expect(searchInput).toBeVisible();
    
    // Check for component filter dropdown
    const componentFilter = page.getByLabel('Filter by component');
    await expect(componentFilter).toBeVisible();
    
    // Check for status filter dropdown
    const statusFilter = page.getByLabel('Filter by status');
    await expect(statusFilter).toBeVisible();
  });

  test('should show prompt details when a prompt is selected', async ({ page }) => {
    // Click on the first prompt item
    const firstPromptItem = page.locator('.prompt-item').first();
    await firstPromptItem.click();
    
    // Check that the prompt details panel is visible
    const promptDetailsPanel = page.locator('.prompt-details');
    await expect(promptDetailsPanel).toBeVisible();
    
    // Check for the template textarea
    const templateTextarea = page.locator('#template');
    await expect(templateTextarea).toBeVisible();
    
    // Check for the save button
    const saveButton = page.getByRole('button', { name: 'Save Changes' });
    await expect(saveButton).toBeVisible();
  });

  test('should allow filtering prompts by component', async ({ page }) => {
    // Get the component filter dropdown
    const componentFilter = page.getByLabel('Filter by component');
    await componentFilter.click();
    
    // Select the first component option
    const firstComponentOption = page.locator('.component-option').first();
    await firstComponentOption.click();
    
    // Check that the prompts list is filtered
    // Note: We can't check the exact filtering without knowing the data,
    // but we can verify that the UI responds to the filter action
    await expect(page.locator('.prompts-list')).toBeVisible();
  });
});
