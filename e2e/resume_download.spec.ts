import { test, expect } from '@playwright/test';

/**
 * MyResumo Resume Download Tests
 *
 * These tests verify the functionality of the resume download options.
 *
 * NOTE: These tests use the /api/resume endpoint, not /api/resumes.
 */

test.describe('Resume Download Options Tests', () => {
  // Mock resume data for testing
  const mockResumeId = 'test-resume-id';
  const mockOptimizedData = {
    user_information: {
      name: 'John Doe',
      email: 'john.doe@example.com',
      github: 'github.com/johndoe',
      linkedin: 'linkedin.com/in/johndoe',
      profile_description: 'Experienced software engineer',
      experiences: [
        {
          job_title: 'Senior Software Engineer',
          company: 'Tech Company',
          start_date: '2020-01',
          end_date: 'Present',
          location: 'New York, NY',
          four_tasks: [
            'Developed scalable backend services',
            'Implemented CI/CD pipelines',
            'Optimized database queries',
            'Mentored junior developers'
          ]
        }
      ],
      skills: {
        hard_skills: ['Python', 'JavaScript', 'SQL'],
        soft_skills: ['Communication', 'Leadership']
      }
    }
  };

  test.beforeEach(async ({ page, context }) => {
    // Mock API responses
    await context.route('/api/resume/' + mockResumeId, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: mockResumeId,
          title: 'Test Resume',
          original_content: 'Test content',
          optimized_data: mockOptimizedData,
          ats_score: 85,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
      });
    });

    // Mock optimization results
    await context.route('/api/resume/' + mockResumeId + '/optimize', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          resume_id: mockResumeId,
          original_ats_score: 65,
          optimized_ats_score: 85,
          score_improvement: 20,
          matching_skills: ['Python', 'JavaScript'],
          missing_skills: ['React', 'Node.js'],
          recommendation: 'Consider adding more details about your React experience.',
          optimized_data: mockOptimizedData
        })
      });
    });

    // Mock PDF download
    await context.route('/api/resume/' + mockResumeId + '/download*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        body: Buffer.from('Mock PDF content')
      });
    });

    // Mock LaTeX download
    await context.route('/api/resume/' + mockResumeId + '/download-latex*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/x-latex',
        body: Buffer.from('\\documentclass{article}\\begin{document}Mock LaTeX content\\end{document}')
      });
    });

    // Navigate to the resume optimization page
    await page.goto('/resume/' + mockResumeId + '/optimize');
    await page.waitForLoadState('networkidle');
  });

  test('should display download options dropdown', async ({ page }) => {
    // Fill in job description and optimize
    await page.getByLabel('Job Description').fill('Test job description requiring Python and JavaScript skills');
    await page.getByRole('button', { name: 'Optimize Resume' }).click();

    // Wait for optimization to complete
    await page.waitForSelector('text=Optimization Complete!', { timeout: 10000 });

    // Verify download dropdown button is visible
    const downloadButton = page.getByRole('button', { name: 'Download Optimized Resume' });
    await expect(downloadButton).toBeVisible();

    // Click the download button to show options
    await downloadButton.click();

    // Verify dropdown options are visible
    await expect(page.getByRole('menuitem', { name: 'PDF Format' })).toBeVisible();
    await expect(page.getByRole('menuitem', { name: 'LaTeX Format (Editable)' })).toBeVisible();
  });

  test('should download PDF when PDF option is selected', async ({ page, context }) => {
    // Setup download listener
    const downloadPromise = page.waitForEvent('download');

    // Fill in job description and optimize
    await page.getByLabel('Job Description').fill('Test job description requiring Python and JavaScript skills');
    await page.getByRole('button', { name: 'Optimize Resume' }).click();

    // Wait for optimization to complete
    await page.waitForSelector('text=Optimization Complete!', { timeout: 10000 });

    // Click the download button to show options
    await page.getByRole('button', { name: 'Download Optimized Resume' }).click();

    // Click the PDF option
    await page.getByRole('menuitem', { name: 'PDF Format' }).click();

    // Wait for download to start
    const download = await downloadPromise;

    // Verify download has started
    expect(download.suggestedFilename()).toContain('.pdf');
  });

  test('should download LaTeX when LaTeX option is selected', async ({ page, context }) => {
    // Setup download listener
    const downloadPromise = page.waitForEvent('download');

    // Fill in job description and optimize
    await page.getByLabel('Job Description').fill('Test job description requiring Python and JavaScript skills');
    await page.getByRole('button', { name: 'Optimize Resume' }).click();

    // Wait for optimization to complete
    await page.waitForSelector('text=Optimization Complete!', { timeout: 10000 });

    // Click the download button to show options
    await page.getByRole('button', { name: 'Download Optimized Resume' }).click();

    // Click the LaTeX option
    await page.getByRole('menuitem', { name: 'LaTeX Format (Editable)' }).click();

    // Wait for download to start
    const download = await downloadPromise;

    // Verify download has started
    expect(download.suggestedFilename()).toContain('.tex');
  });
});
