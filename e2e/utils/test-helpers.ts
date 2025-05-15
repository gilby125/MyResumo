import { Page, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Test Utilities
 * 
 * This file contains helper functions for common test operations.
 */

/**
 * Navigate to a page and wait for it to load
 * @param page Playwright page object
 * @param url URL to navigate to
 * @param title Expected page title (regex pattern)
 */
export async function navigateToPage(page: Page, url: string, title: RegExp): Promise<void> {
  // Navigate to the page
  await page.goto(url);
  
  // Wait for the page to load completely
  await page.waitForLoadState('networkidle');
  
  // Verify the page title
  await expect(page).toHaveTitle(title);
}

/**
 * Upload a resume file
 * @param page Playwright page object
 * @param filePath Path to the resume file
 * @returns True if the upload was successful, false otherwise
 */
export async function uploadResume(page: Page, filePath: string): Promise<boolean> {
  // Check if the file exists
  if (!fs.existsSync(filePath)) {
    console.error(`File not found: ${filePath}`);
    return false;
  }
  
  // Get the file input element
  const fileInput = page.locator('input[type="file"]');
  
  // Upload the file
  await fileInput.setInputFiles(filePath);
  
  try {
    // Wait for the file to be processed
    await page.waitForSelector('text=File uploaded successfully', { timeout: 10000 });
    return true;
  } catch (error) {
    console.error('Error uploading resume:', error);
    return false;
  }
}

/**
 * Generate a random job description for testing
 * @param jobTitle Job title to include in the description
 * @param skills Array of skills to include in the description
 * @returns A job description string
 */
export function generateJobDescription(jobTitle: string, skills: string[]): string {
  const skillsList = skills.map(skill => `- ${skill}`).join('\n');
  
  return `
    ${jobTitle}
    
    Requirements:
    - 5+ years of experience in software development
    ${skillsList}
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
}

/**
 * Wait for an optimization or scoring process to complete
 * @param page Playwright page object
 * @param timeout Timeout in milliseconds
 * @returns True if the process completed successfully, false otherwise
 */
export async function waitForProcessCompletion(page: Page, timeout: number = 30000): Promise<boolean> {
  try {
    // Wait for either the optimization complete or scoring complete message
    await Promise.race([
      page.waitForSelector('text=Optimization Complete!', { timeout }),
      page.waitForSelector('text=Scoring Complete!', { timeout })
    ]);
    return true;
  } catch (error) {
    console.error('Error waiting for process completion:', error);
    return false;
  }
}

/**
 * Extract score from a score element
 * @param page Playwright page object
 * @param selector Selector for the score element
 * @returns The score as a number, or null if not found
 */
export async function extractScore(page: Page, selector: string): Promise<number | null> {
  try {
    const scoreText = await page.locator(selector).textContent();
    const scoreMatch = scoreText.match(/\d+/);
    if (scoreMatch) {
      return parseInt(scoreMatch[0], 10);
    }
    return null;
  } catch (error) {
    console.error('Error extracting score:', error);
    return null;
  }
}

/**
 * Mock resume data in local storage
 * @param page Playwright page object
 * @param resumeData Resume data to mock
 */
export async function mockResumeData(page: Page, resumeData: any): Promise<void> {
  await page.evaluate((data) => {
    window.localStorage.setItem('resumeData', JSON.stringify(data));
  }, resumeData);
}

/**
 * Generate a sample resume data object for testing
 * @param id Resume ID
 * @param name User name
 * @param skills Array of skills
 * @returns A resume data object
 */
export function generateSampleResumeData(id: string, name: string, skills: string[]): any {
  return {
    id,
    title: `${name}'s Resume`,
    original_content: 'Sample resume content',
    optimized_data: {
      user_information: {
        name,
        email: `${name.toLowerCase().replace(' ', '.')}@example.com`,
        github: `github.com/${name.toLowerCase().replace(' ', '')}`,
        linkedin: `linkedin.com/in/${name.toLowerCase().replace(' ', '')}`,
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
          hard_skills: skills,
          soft_skills: ['Communication', 'Problem Solving', 'Teamwork']
        }
      }
    },
    ats_score: 65,
    optimized_ats_score: 85,
    score_improvement: 20,
    matching_skills: skills.slice(0, Math.ceil(skills.length / 2)),
    missing_skills: ['TypeScript', 'Express'],
    recommendation: 'Consider adding more details about your TypeScript and Express experience.',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };
}

/**
 * Clean up test artifacts
 * @param filePaths Array of file paths to delete
 */
export function cleanupTestArtifacts(filePaths: string[]): void {
  for (const filePath of filePaths) {
    if (fs.existsSync(filePath)) {
      try {
        fs.unlinkSync(filePath);
        console.log(`Deleted test artifact: ${filePath}`);
      } catch (error) {
        console.error(`Error deleting test artifact ${filePath}:`, error);
      }
    }
  }
}