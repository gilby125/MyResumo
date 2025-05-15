import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import { uploadResume } from './utils/test-helpers';

/**
 * Resume Optimization End-to-End Tests
 *
 * These tests verify the complete resume optimization workflow.
 * They test the upload, analysis, optimization, and download of resumes.
 *
 * NOTE: These tests use the /api/resume endpoint, not /api/resumes.
 */

test.describe('Resume Optimization End-to-End Tests', () => {
  // Sample resume file path - this should be updated to point to a real test resume
  const SAMPLE_RESUME_PATH = path.join(__dirname, '../test-data/sample-resume.pdf');

  // Sample job description for testing
  const SAMPLE_JOB_DESCRIPTION = `
    Senior Software Engineer

    Requirements:
    - 5+ years of experience in software development
    - Strong knowledge of JavaScript, TypeScript, and React
    - Experience with Node.js and Express
    - Familiarity with MongoDB or other NoSQL databases
    - Experience with CI/CD pipelines
    - Strong problem-solving skills
    - Excellent communication skills

    Responsibilities:
    - Design and implement new features for our web application
    - Collaborate with cross-functional teams to define and implement new features
    - Write clean, maintainable, and efficient code
    - Participate in code reviews and provide constructive feedback
    - Troubleshoot and fix bugs in existing code
    - Mentor junior developers
  `;

  // Sample job title for testing
  const SAMPLE_JOB_TITLE = 'Senior Software Engineer';

  // Before each test, navigate to the create resume page
  test.beforeEach(async ({ page, context }) => {
    // Intercept any requests to /api/resumes and redirect them to /api/resume
    await context.route('/api/resumes*', async (route) => {
      const url = new URL(route.request().url());
      const newUrl = url.toString().replace('/api/resumes', '/api/resume');
      console.log(`Redirecting ${url} to ${newUrl}`);
      await route.continue({ url: newUrl });
    });

    // Navigate to the create resume page
    await page.goto('/create');

    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');

    // Verify we're on the create resume page
    await expect(page).toHaveTitle(/Create Resume - MyResumo/);
  });

  // Skip this test if the sample resume file doesn't exist
  test('should upload a resume and proceed to analysis', async ({ page }) => {
    // Skip the test if the sample resume file doesn't exist
    test.skip(!fs.existsSync(SAMPLE_RESUME_PATH), `Sample resume file not found at ${SAMPLE_RESUME_PATH}`);

    // Use the helper function to upload the resume
    const uploadSuccess = await uploadResume(page, SAMPLE_RESUME_PATH);
    expect(uploadSuccess).toBeTruthy();

    // Enter the job description
    const jobDescriptionTextarea = page.getByLabel('Job Description *');
    await jobDescriptionTextarea.fill(SAMPLE_JOB_DESCRIPTION);

    // Enter the job title
    const jobTitleInput = page.getByLabel('Job Title');
    await jobTitleInput.fill(SAMPLE_JOB_TITLE);

    // Click the Analyze Resume button
    const analyzeButton = page.getByRole('button', { name: 'Analyze Resume' });
    await expect(analyzeButton).toBeEnabled();
    await analyzeButton.click();

    // Wait for the analysis to complete and proceed to the next step
    await page.waitForSelector('text=Resume Analysis Complete', { timeout: 30000 });

    // Verify we're on the analysis step
    const analysisStep = page.locator('.step-item.active:has-text("Analyze")');
    await expect(analysisStep).toBeVisible();

    // Verify the analysis results are displayed
    await expect(page.locator('.analysis-results')).toBeVisible();

    console.log('Resume uploaded and analyzed successfully');
  });

  test('should optimize a resume with a job description', async ({ page }) => {
    // Mock the resume upload and analysis steps
    await page.evaluate(() => {
      // This is a mock implementation to simulate a successful upload and analysis
      // In a real test, this would be done through the UI
      window.localStorage.setItem('resumeData', JSON.stringify({
        id: 'test-resume-id',
        title: 'Test Resume',
        original_content: 'Test content',
        ats_score: 65,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }));
    });

    // Navigate directly to the optimization page
    await page.goto('/resume/test-resume-id/optimize');

    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');

    // Enter the job description
    const jobDescriptionTextarea = page.getByLabel('Job Description');
    await jobDescriptionTextarea.fill(SAMPLE_JOB_DESCRIPTION);

    // Set the temperature slider (if available)
    const temperatureSlider = page.locator('input[type="range"]');
    if (await temperatureSlider.count() > 0) {
      await temperatureSlider.fill('0.7'); // Set to a moderate creativity level
    }

    // Click the Optimize Resume button
    const optimizeButton = page.getByRole('button', { name: 'Optimize Resume' });
    await optimizeButton.click();

    // Wait for the optimization to complete
    await page.waitForSelector('text=Optimization Complete!', { timeout: 30000 });

    // Verify the optimization results are displayed
    await expect(page.locator('.optimization-results')).toBeVisible();

    // Verify the optimized score is higher than the original score
    const originalScoreText = await page.locator('.original-score').textContent();
    const optimizedScoreText = await page.locator('.optimized-score').textContent();

    // Make sure we have score text
    expect(originalScoreText).not.toBeNull();
    expect(optimizedScoreText).not.toBeNull();

    // Extract the scores as numbers
    const originalScoreMatch = originalScoreText?.match(/\d+/);
    const optimizedScoreMatch = optimizedScoreText?.match(/\d+/);

    // Make sure we have matches
    expect(originalScoreMatch).not.toBeNull();
    expect(optimizedScoreMatch).not.toBeNull();

    const originalScore = parseInt(originalScoreMatch?.[0] || '0', 10);
    const optimizedScore = parseInt(optimizedScoreMatch?.[0] || '0', 10);

    // Verify the optimized score is higher
    expect(optimizedScore).toBeGreaterThan(originalScore);

    console.log(`Resume optimized successfully. Original score: ${originalScore}, Optimized score: ${optimizedScore}`);
  });

  test('should download the optimized resume in PDF format', async ({ page }) => {
    // Mock the resume optimization steps
    await page.evaluate(() => {
      // This is a mock implementation to simulate a successful optimization
      // In a real test, this would be done through the UI
      window.localStorage.setItem('resumeData', JSON.stringify({
        id: 'test-resume-id',
        title: 'Test Resume',
        original_content: 'Test content',
        optimized_data: {
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
              hard_skills: ['JavaScript', 'TypeScript', 'React', 'Node.js', 'MongoDB'],
              soft_skills: ['Communication', 'Problem Solving', 'Teamwork']
            }
          }
        },
        ats_score: 65,
        optimized_ats_score: 85,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }));
    });

    // Navigate directly to the optimization results page
    await page.goto('/resume/test-resume-id/optimize');

    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');

    // Mock the optimization completion
    await page.evaluate(() => {
      // This is a mock implementation to simulate a completed optimization
      const resultsElement = document.querySelector('.optimization-results');
      if (resultsElement) {
        (resultsElement as HTMLElement).style.display = 'block';
      }
    });

    // Setup download listener
    const downloadPromise = page.waitForEvent('download');

    // Click the download button to show options
    await page.getByRole('button', { name: 'Download Optimized Resume' }).click();

    // Click the PDF option
    await page.getByRole('menuitem', { name: 'PDF Format' }).click();

    // Wait for download to start
    const download = await downloadPromise;

    // Verify download has started
    expect(download.suggestedFilename()).toContain('.pdf');

    console.log(`Resume downloaded successfully as ${download.suggestedFilename()}`);
  });

  test('should download the optimized resume in LaTeX format', async ({ page }) => {
    // Mock the resume optimization steps
    await page.evaluate(() => {
      // This is a mock implementation to simulate a successful optimization
      // In a real test, this would be done through the UI
      window.localStorage.setItem('resumeData', JSON.stringify({
        id: 'test-resume-id',
        title: 'Test Resume',
        original_content: 'Test content',
        optimized_data: {
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
              hard_skills: ['JavaScript', 'TypeScript', 'React', 'Node.js', 'MongoDB'],
              soft_skills: ['Communication', 'Problem Solving', 'Teamwork']
            }
          }
        },
        ats_score: 65,
        optimized_ats_score: 85,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }));
    });

    // Navigate directly to the optimization results page
    await page.goto('/resume/test-resume-id/optimize');

    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');

    // Mock the optimization completion
    await page.evaluate(() => {
      // This is a mock implementation to simulate a completed optimization
      const resultsElement = document.querySelector('.optimization-results');
      if (resultsElement) {
        (resultsElement as HTMLElement).style.display = 'block';
      }
    });

    // Setup download listener
    const downloadPromise = page.waitForEvent('download');

    // Click the download button to show options
    await page.getByRole('button', { name: 'Download Optimized Resume' }).click();

    // Click the LaTeX option
    await page.getByRole('menuitem', { name: 'LaTeX Format (Editable)' }).click();

    // Wait for download to start
    const download = await downloadPromise;

    // Verify download has started
    expect(download.suggestedFilename()).toContain('.tex');

    console.log(`Resume downloaded successfully as ${download.suggestedFilename()}`);
  });

  test('should display optimization summary with improvements', async ({ page }) => {
    // Mock the resume optimization steps
    await page.evaluate(() => {
      // This is a mock implementation to simulate a successful optimization
      // In a real test, this would be done through the UI
      window.localStorage.setItem('resumeData', JSON.stringify({
        id: 'test-resume-id',
        title: 'Test Resume',
        original_content: 'Test content',
        optimized_data: {
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
              hard_skills: ['JavaScript', 'TypeScript', 'React', 'Node.js', 'MongoDB'],
              soft_skills: ['Communication', 'Problem Solving', 'Teamwork']
            }
          }
        },
        ats_score: 65,
        optimized_ats_score: 85,
        score_improvement: 20,
        matching_skills: ['JavaScript', 'React', 'Node.js', 'MongoDB'],
        missing_skills: ['TypeScript', 'Express'],
        recommendation: 'Consider adding more details about your TypeScript and Express experience.',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }));
    });

    // Navigate directly to the optimization results page
    await page.goto('/resume/test-resume-id/optimize');

    // Wait for the page to load completely
    await page.waitForLoadState('networkidle');

    // Mock the optimization completion
    await page.evaluate(() => {
      // This is a mock implementation to simulate a completed optimization
      const resultsElement = document.querySelector('.optimization-results');
      if (resultsElement) {
        (resultsElement as HTMLElement).style.display = 'block';
      }
    });

    // Verify the optimization summary is displayed
    await expect(page.locator('.optimization-summary')).toBeVisible();

    // Verify the score improvement is displayed
    const scoreImprovement = page.locator('.score-improvement');
    await expect(scoreImprovement).toBeVisible();
    expect(await scoreImprovement.textContent()).toContain('20');

    // Verify the matching skills are displayed
    const matchingSkills = page.locator('.matching-skills');
    await expect(matchingSkills).toBeVisible();
    expect(await matchingSkills.textContent()).toContain('JavaScript');
    expect(await matchingSkills.textContent()).toContain('React');
    expect(await matchingSkills.textContent()).toContain('Node.js');
    expect(await matchingSkills.textContent()).toContain('MongoDB');

    // Verify the missing skills are displayed
    const missingSkills = page.locator('.missing-skills');
    await expect(missingSkills).toBeVisible();
    expect(await missingSkills.textContent()).toContain('TypeScript');
    expect(await missingSkills.textContent()).toContain('Express');

    // Verify the recommendation is displayed
    const recommendation = page.locator('.recommendation');
    await expect(recommendation).toBeVisible();
    expect(await recommendation.textContent()).toContain('Consider adding more details about your TypeScript and Express experience');

    console.log('Optimization summary displayed successfully');
  });
});