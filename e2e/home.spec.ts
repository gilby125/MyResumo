import { test, expect } from '@playwright/test';

/**
 * MyResumo Home Page Tests
 * 
 * These tests verify the functionality of the MyResumo home/landing page.
 */

test.describe('Home Page Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the home page before each test
    await page.goto('/');
    
    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');
  });

  test('should have the correct title', async ({ page }) => {
    // Verify the page title
    await expect(page).toHaveTitle(/MyResumo - AI-Powered Resume Optimization/);
  });

  test('should display hero section with call to action', async ({ page }) => {
    // Check for the main heading
    const heading = page.getByRole('heading', { level: 1 });
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('AI-Powered');
    await expect(heading).toContainText('Resume Optimization');
    
    // Check for the CTA button
    const ctaButton = page.getByRole('link', { name: 'Get Started' });
    await expect(ctaButton).toBeVisible();
    
    // Verify the button links to the create page
    expect(await ctaButton.getAttribute('href')).toBe('/create');
  });

  test('should have feature sections', async ({ page }) => {
    // Check for feature sections
    const featureSections = page.locator('.feature-section');
    
    // Assuming there are at least 3 feature sections
    await expect(featureSections).toHaveCount.atLeast(3);
  });

  test('should have testimonials section', async ({ page }) => {
    // Check for testimonials section
    const testimonialsSection = page.getByText(/What our users say/i).first();
    await expect(testimonialsSection).toBeVisible();
    
    // Check for at least one testimonial
    const testimonials = page.locator('.testimonial');
    await expect(testimonials).toHaveCount.atLeast(1);
  });

  test('should have footer with navigation links', async ({ page }) => {
    // Check for footer
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
    
    // Check for navigation links in footer
    const footerLinks = footer.getByRole('link');
    await expect(footerLinks).toHaveCount.atLeast(3);
  });

  test('should navigate to create page when clicking Get Started', async ({ page }) => {
    // Click the Get Started button
    const ctaButton = page.getByRole('link', { name: 'Get Started' });
    await ctaButton.click();
    
    // Verify navigation to create page
    await expect(page).toHaveURL(/\/create$/);
    await expect(page).toHaveTitle(/Create Resume - MyResumo/);
  });
});
