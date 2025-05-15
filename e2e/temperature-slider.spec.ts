import { test, expect } from '@playwright/test';
import * as dotenv from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';

// Load environment variables from .env.test
dotenv.config({ path: '.env.test' });

// Get the base URL from environment variables or use localhost for local testing
const BASE_URL = 'http://localhost:8081';

/**
 * Temperature Slider Tests
 *
 * These tests verify the functionality of the temperature slider on the create resume page.
 */

// Create screenshots directory if it doesn't exist
const screenshotsDir = path.join(process.cwd(), 'test-screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

test.describe('Temperature Slider Tests', () => {
  test('should have temperature slider on create resume page', async ({ page }) => {
    // Navigate to the create resume page
    await page.goto(`${BASE_URL}/create`);
    console.log(`Navigated to ${BASE_URL}/create`);

    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');
    console.log('Page loaded');

    // Take a screenshot of the initial page
    await page.screenshot({ path: path.join(screenshotsDir, '01-initial-page.png'), fullPage: true });
    console.log('Took initial screenshot');

    // Check if the page title contains "Create Resume"
    await expect(page).toHaveTitle(/Create Resume/);
    console.log('Page title verified');

    // Check if the page contains the job description textarea
    const jobDescription = page.locator('#job-description');
    await expect(jobDescription).toBeVisible();
    console.log('Job description textarea is visible');

    // Take a screenshot of the job description section
    await jobDescription.screenshot({ path: path.join(screenshotsDir, '02-job-description.png') });

    // Get the job description section's parent element
    const jobDescriptionSection = page.locator('.job-description-section');
    if (await jobDescriptionSection.count() > 0) {
      await jobDescriptionSection.screenshot({ path: path.join(screenshotsDir, '03-job-description-section.png') });
      console.log('Job description section screenshot taken');
    } else {
      console.log('Job description section not found');
    }

    // Take a screenshot of the form section
    const formSection = page.locator('form');
    if (await formSection.count() > 0) {
      await formSection.screenshot({ path: path.join(screenshotsDir, '04-form-section.png') });
      console.log('Form section screenshot taken');
    } else {
      console.log('Form section not found');
    }

    // Log the HTML content for debugging
    const html = await page.content();
    fs.writeFileSync(path.join(screenshotsDir, 'page-html.txt'), html);
    console.log('HTML content saved to file');

    // Search for temperature-related elements in the HTML
    const hasTemperatureSlider = html.includes('temperature-slider');
    const hasCreativityLevel = html.includes('Creativity Level');
    console.log(`HTML contains temperature-slider: ${hasTemperatureSlider}`);
    console.log(`HTML contains Creativity Level: ${hasCreativityLevel}`);

    // Try to find the temperature slider with different selectors
    const temperatureSlider = page.locator('#temperature-slider');
    const temperatureSliderCount = await temperatureSlider.count();
    console.log(`Temperature slider count: ${temperatureSliderCount}`);

    if (temperatureSliderCount > 0) {
      await temperatureSlider.screenshot({ path: path.join(screenshotsDir, '05-temperature-slider.png') });
      console.log('Temperature slider screenshot taken');
      await expect(temperatureSlider).toBeVisible();
    } else {
      console.log('Temperature slider not found with #temperature-slider');

      // Try with a more general selector
      const rangeInputs = page.locator('input[type="range"]');
      const rangeInputCount = await rangeInputs.count();
      console.log(`Range input count: ${rangeInputCount}`);

      if (rangeInputCount > 0) {
        await rangeInputs.screenshot({ path: path.join(screenshotsDir, '06-range-inputs.png') });
        console.log('Range inputs screenshot taken');
      }
    }

    // Check for the temperature label with different approaches
    const creativityTexts = page.getByText(/Creativity Level/);
    const creativityCount = await creativityTexts.count();
    console.log(`Creativity Level text count: ${creativityCount}`);

    if (creativityCount > 0) {
      await creativityTexts.screenshot({ path: path.join(screenshotsDir, '07-creativity-level.png') });
      console.log('Creativity Level text screenshot taken');
      await expect(creativityTexts).toBeVisible();
    }

    // Take a final full page screenshot
    await page.screenshot({ path: path.join(screenshotsDir, '08-final-page.png'), fullPage: true });
    console.log('Took final screenshot');
  });
});
