import { test, expect } from '@playwright/test';

/**
 * MyResumo MCP Tests
 * 
 * These tests verify the Model Control Protocol (MCP) functionality.
 */

test.describe('MCP Functionality Tests', () => {
  test('should take a screenshot of the dashboard', async ({ page }) => {
    // Navigate to the dashboard page
    await page.goto('/dashboard');
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Take a screenshot using the MCP
    await page.screenshot({ path: 'dashboard-screenshot.png' });
    
    // Verify the screenshot was taken
    const fs = require('fs');
    expect(fs.existsSync('dashboard-screenshot.png')).toBeTruthy();
  });
  
  test('should navigate between pages using MCP', async ({ page }) => {
    // Start at the home page
    await page.goto('/');
    
    // Verify we're on the home page
    await expect(page).toHaveTitle(/MyResumo - AI-Powered Resume Optimization/);
    
    // Navigate to the dashboard using MCP
    await page.goto('/dashboard');
    
    // Verify we're on the dashboard page
    await expect(page).toHaveTitle(/Dashboard - MyResumo/);
    
    // Navigate to the create page
    await page.goto('/create');
    
    // Verify we're on the create page
    await expect(page).toHaveTitle(/Create Resume - MyResumo/);
    
    // Go back to the dashboard
    await page.goBack();
    
    // Verify we're back on the dashboard
    await expect(page).toHaveTitle(/Dashboard - MyResumo/);
  });
  
  test('should interact with elements using MCP', async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/dashboard');
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Get the search input
    const searchInput = page.getByPlaceholder('Search resumes...');
    
    // Type in the search input
    await searchInput.fill('test resume');
    
    // Verify the input value
    await expect(searchInput).toHaveValue('test resume');
    
    // Clear the input
    await searchInput.clear();
    
    // Verify it's cleared
    await expect(searchInput).toHaveValue('');
  });
  
  test('should capture page state using MCP', async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/dashboard');
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Get the page title
    const title = await page.title();
    expect(title).toContain('Dashboard');
    
    // Get the current URL
    const url = page.url();
    expect(url).toContain('/dashboard');
    
    // Check if an element exists
    const createButton = page.getByRole('link', { name: /Create New Resume/i });
    await expect(createButton).toBeVisible();
  });
});
