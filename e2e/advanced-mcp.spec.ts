import { test, expect } from '@playwright/test';

/**
 * Advanced MCP Tests
 * 
 * These tests demonstrate more advanced Model Control Protocol (MCP) functionality.
 */

test.describe('Advanced MCP Tests', () => {
  test('should resize browser window and verify responsive design', async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/dashboard');
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Get the current viewport size
    const originalViewport = page.viewportSize();
    
    // Resize to mobile size
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that mobile layout is applied
    // In mobile view, we expect certain elements to be stacked or hidden
    const dashboardHeader = page.locator('.max-w-7xl');
    await expect(dashboardHeader).toBeVisible();
    
    // Resize to tablet size
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // Check tablet layout
    await expect(dashboardHeader).toBeVisible();
    
    // Restore original size
    if (originalViewport) {
      await page.setViewportSize(originalViewport);
    }
  });
  
  test('should take element-specific screenshots', async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/dashboard');
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Take a screenshot of just the header
    const header = page.locator('h1').first();
    await header.screenshot({ path: 'header-screenshot.png' });
    
    // Verify the screenshot was taken
    const fs = require('fs');
    expect(fs.existsSync('header-screenshot.png')).toBeTruthy();
  });
  
  test('should handle dialogs with MCP', async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/dashboard');
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Set up dialog handler
    page.on('dialog', async dialog => {
      // Verify dialog content
      expect(dialog.type()).toBe('alert');
      expect(dialog.message()).toContain('This is a test alert');
      
      // Accept the dialog
      await dialog.accept();
    });
    
    // Execute JavaScript to show an alert
    await page.evaluate(() => {
      alert('This is a test alert');
    });
  });
  
  test('should monitor network requests with MCP', async ({ page }) => {
    // Create a request listener
    const requests = [];
    page.on('request', request => {
      requests.push(request.url());
    });
    
    // Navigate to the dashboard
    await page.goto('/dashboard');
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Verify that we captured some network requests
    expect(requests.length).toBeGreaterThan(0);
    
    // Check for specific API requests
    const apiRequests = requests.filter(url => url.includes('/api/'));
    console.log('API requests:', apiRequests);
  });
  
  test('should use keyboard navigation with MCP', async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/dashboard');
    
    // Wait for the page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Focus on the search input
    const searchInput = page.getByPlaceholder('Search resumes...');
    await searchInput.focus();
    
    // Type using keyboard
    await page.keyboard.type('test resume');
    
    // Verify the input value
    await expect(searchInput).toHaveValue('test resume');
    
    // Press Tab to move to the next element
    await page.keyboard.press('Tab');
    
    // Press Escape to clear any dropdowns
    await page.keyboard.press('Escape');
  });
});
