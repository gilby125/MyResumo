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

    // Check for the CTA button - use exact: true to avoid ambiguity with "Get Started for Free"
    const ctaButton = page.getByRole('link', { name: 'Get Started', exact: true });
    await expect(ctaButton).toBeVisible();

    // Verify the button links to the create page
    expect(await ctaButton.getAttribute('href')).toBe('/create');
  });

  test('should have feature sections', async ({ page }) => {
    // Check for the Features heading
    const featuresHeading = page.getByRole('heading', { name: 'Features' });
    await expect(featuresHeading).toBeVisible();

    // Check for feature items (using the term elements)
    const featureItems = page.locator('dt');

    // Verify we have at least 3 features
    const count = await featureItems.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });

  test('should have testimonials section', async ({ page }) => {
    // Check for testimonials section heading
    const testimonialsHeading = page.getByRole('heading', { name: /Trusted by job seekers/i });
    await expect(testimonialsHeading).toBeVisible();

    // Check for testimonial quotes (paragraphs with quotes)
    const testimonialQuotes = page.locator('p:has-text("\\"")');

    // Verify we have at least one testimonial
    const count = await testimonialQuotes.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('should have CTA section at bottom', async ({ page }) => {
    // Check for the CTA heading at the bottom
    const ctaHeading = page.getByRole('heading', { name: /Ready to optimize your resume/i });
    await expect(ctaHeading).toBeVisible();

    // Check for the Get Started for Free button
    const getStartedButton = page.getByRole('link', { name: 'Get Started for Free' });
    await expect(getStartedButton).toBeVisible();

    // Verify the button links to the create page
    expect(await getStartedButton.getAttribute('href')).toBe('/create');
  });

  test('should navigate to create page when clicking Get Started', async ({ page }) => {
    // Click the Get Started button - use exact: true to avoid ambiguity
    const ctaButton = page.getByRole('link', { name: 'Get Started', exact: true });
    await ctaButton.click();

    // Verify navigation to create page
    await expect(page).toHaveURL(/\/create$/);
  });
});
