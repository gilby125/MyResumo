import { test, expect } from '@playwright/test';

/**
 * MyResumo Dashboard Tests
 *
 * These tests verify the functionality of the MyResumo dashboard page.
 */

test.describe('Dashboard Page Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the dashboard page before each test
    await page.goto('/dashboard');

    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
  });

  test('should have the correct title', async ({ page }) => {
    // Verify the page title
    await expect(page).toHaveTitle(/Dashboard - MyResumo/);
  });

  test('should display dashboard header elements', async ({ page }) => {
    // Check for the main heading
    const heading = page.getByRole('heading', { name: 'Dashboard' });
    await expect(heading).toBeVisible();

    // Check for the subheading
    const subheading = page.getByText('Manage your resumes and track your optimization progress');
    await expect(subheading).toBeVisible();
  });

  test('should have a "Create New Resume" button', async ({ page }) => {
    // Look for the Create New Resume button
    const createButton = page.getByRole('link', { name: /Create New Resume/i });
    await expect(createButton).toBeVisible();

    // Verify the button links to the create page
    expect(await createButton.getAttribute('href')).toBe('/create');
  });

  test('should have search functionality', async ({ page }) => {
    // Check for the search input
    const searchInput = page.getByPlaceholder('Search resumes...');
    await expect(searchInput).toBeVisible();

    // Test entering a search term
    await searchInput.fill('test resume');
    await searchInput.press('Enter');

    // Note: We're not checking results as this is just testing the UI elements
  });

  test('should have view mode toggle buttons', async ({ page }) => {
    // Check for the list view button
    const listViewButton = page.getByRole('button', { name: 'List View' });
    await expect(listViewButton).toBeVisible();

    // Check for the grid view button
    const gridViewButton = page.getByRole('button', { name: 'Grid View' });
    await expect(gridViewButton).toBeVisible();

    // Test switching to grid view
    await gridViewButton.click();

    // Test switching back to list view
    await listViewButton.click();
  });
});
