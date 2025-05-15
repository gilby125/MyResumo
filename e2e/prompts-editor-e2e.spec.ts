import { test, expect } from '@playwright/test';

/**
 * Prompts Editor End-to-End Tests
 *
 * These tests verify the functionality of the prompts editor page.
 * They test the viewing, editing, and saving of prompt templates.
 *
 * NOTE: These tests use the /api/prompts-direct endpoint, not /api/prompts.
 */

test.describe('Prompts Editor End-to-End Tests', () => {
  // Sample prompt data for testing
  const SAMPLE_PROMPT = {
    name: 'Test Prompt',
    template: 'This is a test prompt template with a {{variable}}.',
    description: 'A test prompt for end-to-end testing'
  };

  // Before each test, navigate to the prompts editor page
  test.beforeEach(async ({ page, context }) => {
    // Intercept any requests to /api/prompts and redirect them to /api/prompts-direct
    await context.route('/api/prompts*', async (route) => {
      const url = new URL(route.request().url());
      const newUrl = url.toString().replace('/api/prompts', '/api/prompts-direct');
      console.log(`Redirecting ${url} to ${newUrl}`);
      await route.continue({ url: newUrl });
    });

    // Navigate to the prompts editor page
    await page.goto('/prompts');

    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');
  });

  test('should display the prompts editor page', async ({ page }) => {
    // Verify the page title
    await expect(page).toHaveTitle(/Prompts Editor - MyResumo/);

    // Verify the page heading
    const heading = page.getByRole('heading', { name: 'Prompts Editor' });
    await expect(heading).toBeVisible();

    // Verify the prompt list is displayed
    const promptList = page.locator('.prompt-list');
    await expect(promptList).toBeVisible();

    // Verify the prompt editor form is displayed
    const promptEditor = page.locator('.prompt-editor');
    await expect(promptEditor).toBeVisible();

    console.log('Prompts editor page displayed successfully');
  });

  test('should list available prompts', async ({ page }) => {
    // Verify the prompt list contains items
    const promptItems = page.locator('.prompt-item');

    // Wait for the prompt items to be loaded
    await expect(promptItems.first()).toBeVisible({ timeout: 10000 });

    // Get the count of prompt items
    const count = await promptItems.count();

    // Verify there are prompt items
    expect(count).toBeGreaterThan(0);

    console.log(`Found ${count} prompts in the list`);

    // Verify the first prompt item has a name
    const firstPromptName = await promptItems.first().locator('.prompt-name').textContent();
    expect(firstPromptName.trim()).not.toBe('');

    console.log(`First prompt name: ${firstPromptName}`);
  });

  test('should select a prompt for editing', async ({ page }) => {
    // Wait for the prompt items to be loaded
    const promptItems = page.locator('.prompt-item');
    await expect(promptItems.first()).toBeVisible({ timeout: 10000 });

    // Click on the first prompt item
    await promptItems.first().click();

    // Verify the prompt editor is populated with the selected prompt
    const promptNameInput = page.locator('input[name="promptName"]');
    await expect(promptNameInput).toBeVisible();
    expect(await promptNameInput.inputValue()).not.toBe('');

    const promptTemplateTextarea = page.locator('textarea[name="promptTemplate"]');
    await expect(promptTemplateTextarea).toBeVisible();
    expect(await promptTemplateTextarea.inputValue()).not.toBe('');

    console.log('Prompt selected for editing successfully');
  });

  test('should edit a prompt template', async ({ page }) => {
    // Wait for the prompt items to be loaded
    const promptItems = page.locator('.prompt-item');
    await expect(promptItems.first()).toBeVisible({ timeout: 10000 });

    // Click on the first prompt item
    await promptItems.first().click();

    // Get the original prompt name and template
    const promptNameInput = page.locator('input[name="promptName"]');
    const originalName = await promptNameInput.inputValue();

    const promptTemplateTextarea = page.locator('textarea[name="promptTemplate"]');
    const originalTemplate = await promptTemplateTextarea.inputValue();

    // Edit the prompt name and template
    await promptNameInput.fill(`${originalName} (Edited)`);
    await promptTemplateTextarea.fill(`${originalTemplate} This is an edit.`);

    // Click the Save button
    const saveButton = page.getByRole('button', { name: 'Save' });
    await saveButton.click();

    // Wait for the save operation to complete
    await page.waitForSelector('text=Prompt saved successfully', { timeout: 10000 });

    // Verify the prompt was saved
    const successMessage = page.locator('.success-message');
    await expect(successMessage).toBeVisible();

    console.log('Prompt edited and saved successfully');

    // Reload the page to verify the changes persist
    await page.reload();

    // Wait for the prompt items to be loaded
    await expect(promptItems.first()).toBeVisible({ timeout: 10000 });

    // Find the edited prompt
    const editedPromptItem = page.locator(`.prompt-item:has-text("${originalName} (Edited)")`);

    // Click on the edited prompt
    await editedPromptItem.click();

    // Verify the edited prompt name and template
    await expect(promptNameInput).toHaveValue(`${originalName} (Edited)`);
    await expect(promptTemplateTextarea).toHaveValue(`${originalTemplate} This is an edit.`);

    console.log('Edited prompt persisted after page reload');
  });

  test('should create a new prompt', async ({ page }) => {
    // Click the New Prompt button
    const newPromptButton = page.getByRole('button', { name: 'New Prompt' });
    await newPromptButton.click();

    // Verify the prompt editor is cleared
    const promptNameInput = page.locator('input[name="promptName"]');
    await expect(promptNameInput).toBeVisible();
    await expect(promptNameInput).toHaveValue('');

    const promptTemplateTextarea = page.locator('textarea[name="promptTemplate"]');
    await expect(promptTemplateTextarea).toBeVisible();
    await expect(promptTemplateTextarea).toHaveValue('');

    // Fill in the new prompt details
    await promptNameInput.fill(SAMPLE_PROMPT.name);
    await promptTemplateTextarea.fill(SAMPLE_PROMPT.template);

    // Fill in the description if there's a description field
    const promptDescriptionTextarea = page.locator('textarea[name="promptDescription"]');
    if (await promptDescriptionTextarea.count() > 0) {
      await promptDescriptionTextarea.fill(SAMPLE_PROMPT.description);
    }

    // Click the Save button
    const saveButton = page.getByRole('button', { name: 'Save' });
    await saveButton.click();

    // Wait for the save operation to complete
    await page.waitForSelector('text=Prompt saved successfully', { timeout: 10000 });

    // Verify the prompt was saved
    const successMessage = page.locator('.success-message');
    await expect(successMessage).toBeVisible();

    console.log('New prompt created and saved successfully');

    // Reload the page to verify the changes persist
    await page.reload();

    // Wait for the prompt items to be loaded
    const promptItems = page.locator('.prompt-item');
    await expect(promptItems.first()).toBeVisible({ timeout: 10000 });

    // Find the new prompt
    const newPromptItem = page.locator(`.prompt-item:has-text("${SAMPLE_PROMPT.name}")`);
    await expect(newPromptItem).toBeVisible();

    // Click on the new prompt
    await newPromptItem.click();

    // Verify the new prompt details
    await expect(promptNameInput).toHaveValue(SAMPLE_PROMPT.name);
    await expect(promptTemplateTextarea).toHaveValue(SAMPLE_PROMPT.template);

    console.log('New prompt persisted after page reload');
  });

  test('should validate prompt template syntax', async ({ page }) => {
    // Click the New Prompt button
    const newPromptButton = page.getByRole('button', { name: 'New Prompt' });
    await newPromptButton.click();

    // Fill in the prompt name
    const promptNameInput = page.locator('input[name="promptName"]');
    await promptNameInput.fill('Invalid Template Prompt');

    // Fill in an invalid template with mismatched braces
    const promptTemplateTextarea = page.locator('textarea[name="promptTemplate"]');
    await promptTemplateTextarea.fill('This is an invalid template with {{mismatched} braces.');

    // Click the Save button
    const saveButton = page.getByRole('button', { name: 'Save' });
    await saveButton.click();

    // Verify an error message is displayed
    const errorMessage = page.locator('.error-message');
    await expect(errorMessage).toBeVisible();
    expect(await errorMessage.textContent()).toContain('Invalid template syntax');

    console.log('Template syntax validation working correctly');

    // Fix the template
    await promptTemplateTextarea.fill('This is a valid template with {{matched}} braces.');

    // Click the Save button again
    await saveButton.click();

    // Wait for the save operation to complete
    await page.waitForSelector('text=Prompt saved successfully', { timeout: 10000 });

    // Verify the prompt was saved
    const successMessage = page.locator('.success-message');
    await expect(successMessage).toBeVisible();

    console.log('Fixed template saved successfully');
  });

  test('should delete a prompt', async ({ page }) => {
    // Create a new prompt for deletion
    // Click the New Prompt button
    const newPromptButton = page.getByRole('button', { name: 'New Prompt' });
    await newPromptButton.click();

    // Fill in the prompt details
    const promptNameInput = page.locator('input[name="promptName"]');
    await promptNameInput.fill('Prompt To Delete');

    const promptTemplateTextarea = page.locator('textarea[name="promptTemplate"]');
    await promptTemplateTextarea.fill('This prompt will be deleted.');

    // Click the Save button
    const saveButton = page.getByRole('button', { name: 'Save' });
    await saveButton.click();

    // Wait for the save operation to complete
    await page.waitForSelector('text=Prompt saved successfully', { timeout: 10000 });

    // Reload the page
    await page.reload();

    // Wait for the prompt items to be loaded
    const promptItems = page.locator('.prompt-item');
    await expect(promptItems.first()).toBeVisible({ timeout: 10000 });

    // Find the prompt to delete
    const promptToDelete = page.locator('.prompt-item:has-text("Prompt To Delete")');
    await expect(promptToDelete).toBeVisible();

    // Click on the prompt to delete
    await promptToDelete.click();

    // Click the Delete button
    const deleteButton = page.getByRole('button', { name: 'Delete' });
    await deleteButton.click();

    // Confirm the deletion in the confirmation dialog
    const confirmButton = page.getByRole('button', { name: 'Confirm' });
    await confirmButton.click();

    // Wait for the delete operation to complete
    await page.waitForSelector('text=Prompt deleted successfully', { timeout: 10000 });

    // Verify the prompt was deleted
    const successMessage = page.locator('.success-message');
    await expect(successMessage).toBeVisible();

    console.log('Prompt deleted successfully');

    // Reload the page to verify the deletion persists
    await page.reload();

    // Wait for the prompt items to be loaded
    await expect(promptItems.first()).toBeVisible({ timeout: 10000 });

    // Verify the deleted prompt is no longer in the list
    const deletedPrompt = page.locator('.prompt-item:has-text("Prompt To Delete")');
    await expect(deletedPrompt).toHaveCount(0);

    console.log('Prompt deletion persisted after page reload');
  });
});