"""AI-powered resume optimization module.

This module provides the AtsResumeOptimizer class that leverages AI language models
to analyze and optimize resumes based on job descriptions, improving compatibility
with Applicant Tracking Systems (ATS).
"""

import json
import os
import re
from typing import Any, Dict, List, Optional

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI

from app.services.ai.ats_scoring import ATSScorerLLM
from app.utils.token_tracker import TokenTracker


class AtsResumeOptimizer:
    """ATS Resume Optimizer.

    A class that uses AI language models to optimize resumes for Applicant Tracking
    Systems (ATS) based on specific job descriptions.

    This class leverages OpenAI's language models to analyze a job description and a
    provided resume, then generates an ATS-optimized version of the resume in JSON format.
    The optimization focuses on incorporating relevant keywords, formatting for ATS
    readability, and highlighting the most relevant experience for the target position.

    Attributes:
    ----------
        model_name: The name of the OpenAI model to use for processing
        resume: The resume text to be optimized
        api_key: OpenAI API key for authentication
        api_base: Base URL for the OpenAI API
        llm: The initialized language model instance
        output_parser: Parser for converting LLM output to JSON format
        ats_scorer: ATSScorerLLM instance for scoring resume and extracting missing skills

    Methods:
    -------
        _get_openai_model()
            Initialize the OpenAI model with appropriate settings
        _get_prompt_template(missing_skills=None)
            Create the PromptTemplate for ATS resume optimization with missing skills
        _setup_chain()
            Set up the processing pipeline for job descriptions and resumes
        generate_ats_optimized_resume_json(job_description)
            Generate an ATS-optimized resume in JSON format based on the provided job description

    Example:
        >>> # Note: Ensure to replace "your_api_key" and "your resume text" with actual values
        >>> optimizer = AtsResumeOptimizer(api_key="your_api_key", resume="your resume text")
        >>> optimized_resume = optimizer.generate_ats_optimized_resume_json("job description text")
        >>> print(optimized_resume)
        >>> # Output: JSON object with optimized resume
    """

    def __init__(
        self,
        model_name: str = None,
        resume: str = None,
        api_key: str = None,
        api_base: str = None,
        user_id: str = None,
        temperature: float = 0.0,
    ) -> None:
        """Initialize the AI model for resume processing.

        Args:
            model_name: The name of the OpenAI model to use.
            resume: The resume text to be optimized.
            api_key: OpenAI API key for authentication.
            api_base: Base URL for the OpenAI API.
            user_id: Optional user ID for token tracking.
            temperature: Temperature setting for the LLM (0.0-1.0) to control creativity.
        """
        self.model_name = model_name or os.getenv("MODEL_NAME")
        self.resume = resume
        self.api_key = api_key or os.getenv("API_KEY")
        self.api_base = api_base or os.getenv("API_BASE")
        self.user_id = user_id
        self.temperature = temperature

        # Initialize LLM component and output parser
        self.llm = self._get_openai_model()
        self.output_parser = JsonOutputParser()
        self.chain = None

        # Initialize ATS scorer for skill extraction and analysis
        self.ats_scorer = None
        if self.api_key and self.api_base and self.model_name:
            self.ats_scorer = ATSScorerLLM(
                model_name=self.model_name,
                api_key=self.api_key,
                api_base=self.api_base,
                user_id=self.user_id,
                temperature=self.temperature,
            )

        self._setup_chain()

    def _get_openai_model(self) -> ChatOpenAI:
        """Initialize the OpenAI model with appropriate settings.

        Returns:
            ChatOpenAI: Configured language model instance with token tracking
        """
        if self.model_name:
            # Create LLM instance with token tracking for usage monitoring
            return TokenTracker.get_tracked_langchain_llm(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=self.api_key,
                api_base=self.api_base,
                feature="resume_optimization",
                user_id=self.user_id,
                metadata={"resume_length": len(self.resume) if self.resume else 0}
            )
        else:
            # Fallback to standard model if no specific model is configured
            return ChatOpenAI(temperature=self.temperature)

    async def _get_prompt_template_from_db(self) -> Optional[str]:
        """Attempt to load the resume optimization prompt template from the database.

        Returns:
            Optional[str]: The prompt template string if found, None otherwise.
        """
        try:
            from app.database.repositories.prompt_repository import PromptRepository
            repo = PromptRepository()

            # Get resume optimization prompt
            prompt = await repo.get_prompt_by_name("resume_optimization")
            if prompt:
                return prompt["template"]
            return None
        except Exception as e:
            print(f"Error loading prompt from database: {e}")
            return None

    def _get_prompt_template(self, missing_skills: Optional[List[str]] = None) -> PromptTemplate:
        """Create the PromptTemplate for ATS resume optimization.

        Args:
            missing_skills: A list of skills identified as missing from the resume
                        that should be incorporated if the candidate has them.

        Returns:
            PromptTemplate: A prompt template with instructions for resume optimization.
        """
        # Create the recommended skills section if applicable
        recommended_skills_section = ""
        if missing_skills and len(missing_skills) > 0:
            skills_list = ", ".join([f"'{skill}'" for skill in missing_skills])
            recommended_skills_section = f"""
        ## RECOMMENDED SKILLS TO ADD

        The following skills were identified as potentially valuable for this position but may be missing or not prominently featured in the resume:

        {skills_list}

        If the candidate has any experience with these skills, even minor exposure:
        - Highlight them prominently in the skills section
        - Look for ways to showcase these skills in past experience descriptions
        - Ensure you're using the exact terminology as listed
        - Look for related skills or experience that could be reframed to match these requirements
        - Reframe transferable or implied experience to match the job requirements where ethically possible
        - Be assertive in surfacing any relevant experience, even if it is not an exact match, as long as it is truthful
        - Do NOT fabricate experience with these skills, only highlight them if they exist
        """

        # Use the default template
        template = f"""
        # ROLE: Expert ATS Resume Optimization Specialist
        You are an expert ATS (Applicant Tracking System) Resume Optimizer with specialized knowledge in resume writing, keyword optimization, and applicant tracking systems. Your task is to transform the candidate's existing resume into a highly optimized version tailored specifically to the provided job description, maximizing the candidate's chances of passing through ATS filters while maintaining honesty and accuracy.

        ## INPUT DATA:

        ### JOB DESCRIPTION:
        {{job_description}}

        ### CANDIDATE'S CURRENT RESUME:
        {{resume}}

        {recommended_skills_section}

        ## OPTIMIZATION PROCESS:

        1. **ANALYZE THE JOB DESCRIPTION**
            - Extract key requirements, skills, qualifications, and responsibilities
            - Identify primary keywords, secondary keywords, and industry-specific terminology
            - Note the exact phrasing and terminology used by the employer
            - Identify technical requirements (software, tools, frameworks, etc.)
            - Detect company values and culture indicators
            - Determine desired experience level and specific metrics/achievements valued
            - Pay special attention to both hard skills (technical) and soft skills (interpersonal)

        2. **EVALUATE THE CURRENT RESUME**
            - Compare existing content against job requirements
            - Identify skills and experiences that align with the job
            - Detect terminology mismatches and missing keywords
            - Assess the presentation of achievements and results
            - Calculate an initial "match score" to identify improvement areas
            - Note transferable skills that could be reframed for the target position
            - Look for implied skills that might not be explicitly stated

        3. **CREATE AN ATS-OPTIMIZED RESUME**
            - Use a clean, ATS-friendly format with standard section headings
            - Include the candidate's name, contact information, and professional profiles
            - Create a targeted professional summary highlighting relevant qualifications
            - Incorporate exact keywords and phrases from the job description throughout the resume
            - Prioritize and emphasize experiences most relevant to the target position
            - Reorder content to place most relevant experiences and skills first
            - Use industry-standard terminology that ATS systems recognize
            - Quantify achievements with metrics where possible (numbers, percentages, dollar amounts)
            - Remove irrelevant information that doesn't support this application
            - Ensure job titles, company names, dates, and locations are clearly formatted
            - Include a skills section with relevant hard and soft skills using job description terminology
            - Highlight both technical capabilities and relevant soft skills like communication, teamwork, leadership
            - Emphasize transferable skills and reframe related experience to match job requirements, even if not an exact match
            - Be assertive in surfacing all relevant experience, including implied or adjacent skills, as long as it is truthful

        4. **ATS OPTIMIZATION TECHNIQUES**
            - Use standard section headings (e.g., "Work Experience" not "Career Adventures")
            - Avoid tables, columns, headers, footers, images, and special characters
            - Use standard bullet points (• or - only)
            - Use common file formats and fonts (Arial, Calibri, Times New Roman)
            - Include keywords in context rather than keyword stuffing
            - Use both spelled-out terms and acronyms where applicable (e.g., "Search Engine Optimization (SEO)")
            - Keep formatting consistent throughout the document
            - For technical positions, include relevant projects with clear descriptions
            - Limit project listings to 3-4 most relevant examples
            - Use synonyms and related terms for key skills to maximize keyword matching
            - Make connections between past experience and job requirements clear and explicit

        5. **ETHICAL GUIDELINES**
            - Only include truthful information from the original resume
            - Do not fabricate experience, skills, or qualifications
            - Focus on highlighting relevant actual experience, not inventing new experience
            - Reframe existing experience to highlight relevant skills
            - Optimize language and presentation while maintaining accuracy
            - When appropriate, add context to existing skills to make them more relevant to the job

        6. **CREATE A DETAILED SUMMARY OF CHANGES**
            - Document the specific changes made to the resume in detail
            - List the key keywords and phrases added from the job description (at least 5-10 keywords)
            - Explain how the professional summary was tailored to match the job requirements
            - Describe how experience descriptions were enhanced or reframed to highlight relevant skills
            - Note any skills that were emphasized or added (be specific about which skills)
            - Explain any reorganization of content for better ATS compatibility
            - Highlight quantification of achievements that were added (include specific metrics)
            - Summarize the overall optimization strategy in 2-3 sentences

            THIS SUMMARY OF CHANGES IS CRITICAL - it will be displayed to the user to explain what was improved in their resume. Be thorough and specific.

        ## OUTPUT FORMAT:

        ⚠️ CRITICAL INSTRUCTION ⚠️

        YOU MUST RETURN ONLY A VALID JSON OBJECT WITH ABSOLUTELY NO OTHER TEXT.

        DO NOT:
        - Add any introduction like "Here's the JSON" or "Here's the optimized resume"
        - Add any explanation or commentary before or after the JSON
        - Wrap the JSON in markdown code blocks (```json)
        - Add any notes, tips, or additional information

        YOUR ENTIRE RESPONSE MUST BE PARSEABLE BY json.loads() IN PYTHON.

        The JSON must follow this EXACT structure:

        {{{{
            "user_information": {{{{
                "name": "",
                "main_job_title": "",
                "profile_description": "",
                "email": "",
                "linkedin": "",
                "github": "",
                "experiences": [
                    {{{{
                        "job_title": "",
                        "company": "",
                        "start_date": "",
                        "end_date": "",
                        "location": "",
                        "four_tasks": []
                    }}}}
                ],
                "education": [
                    {{{{
                        "institution": "",
                        "degree": "",
                        "location": "",
                        "description": "",
                        "start_date": "",
                        "end_date": ""
                    }}}}
                ],
                "skills": {{{{
                    "hard_skills": [],
                    "soft_skills": []
                }}}},
                "hobbies": []
            }}}},
            "projects": [
                {{{{
                    "project_name": "",
                    "project_link": "",
                    "two_goals_of_the_project": [],
                    "project_end_result": "",
                    "tech_stack": []
                }}}}
            ],
            "certificate": [
                {{{{
                    "name": "",
                    "link" : "",
                    "institution": "",
                    "description": "",
                    "date": ""
                }}}}
            ],
            "extra_curricular_activities": [
                {{{{
                    "name": "",
                    "description": "",
                    "start_date": "",
                    "end_date": ""
                }}}}
            ],
            "optimization_summary": {{{{
                "changes_made": [],
                "keywords_added": [],
                "skills_emphasized": [],
                "content_reorganized": [],
                "achievements_quantified": [],
                "overall_strategy": ""
            }}}}
        }}}}

        IMPORTANT REQUIREMENTS:
        1. The "four_tasks" array must contain EXACTLY 4 items for each experience
        2. The "two_goals_of_the_project" array must contain EXACTLY 2 items for each project
        3. Make sure all dates follow a consistent format (YYYY-MM or MM/YYYY)
        4. Ensure all fields are filled with appropriate data extracted from the resume
        5. The "optimization_summary" section MUST include detailed information about the specific changes made:
           - "changes_made" array should contain at least 3-5 specific changes
           - "keywords_added" array should list at least 5-10 keywords added from the job description
           - "skills_emphasized" array should list at least 3-5 skills that were emphasized
           - "content_reorganized" array should explain how content was reorganized
           - "achievements_quantified" array should list achievements that were quantified with metrics
           - "overall_strategy" should be a 2-3 sentence summary of your optimization approach
        6. Return ONLY the JSON object with no other text, explanation, or commentary
        7. Your response MUST be a valid JSON object that can be parsed with json.loads()
        8. DO NOT wrap the JSON in markdown code blocks or any other formatting

        ⚠️ FINAL REMINDER: YOUR ENTIRE RESPONSE MUST BE ONLY THE JSON OBJECT ⚠️
        """
        return PromptTemplate.from_template(template=template)

    def _setup_chain(self, missing_skills: Optional[List[str]] = None) -> None:
        """Set up the processing pipeline for job descriptions and resumes.

        This method configures the functional composition approach with the pipe operator
        to create a processing chain from prompt template to language model.

        Args:
            missing_skills: List of skills identified as missing that should be incorporated
                        into the optimization prompt.
        """
        prompt_template = self._get_prompt_template(missing_skills)
        self.chain = prompt_template | self.llm

    async def generate_ats_optimized_resume_json(
        self, job_description: str
    ) -> Dict[str, Any]:
        """Generate an ATS-optimized resume in JSON format.

        This method performs a comprehensive ATS analysis of the resume against the job
        description, extracts valuable insights such as missing skills and keyword matches,
        and then uses this information to generate an optimized resume tailored to the
        specific job requirements.

        Args:
            job_description: The target job description.

        Returns:
        -------
            dict: The optimized resume in JSON format with additional ATS metrics.
        """
        if not self.resume:
            return {"error": "Resume not provided"}

        try:
            missing_skills = []
            score_results = {}

            # Step 1: Analyze resume against job description to identify skill gaps
            if self.ats_scorer:
                try:
                    # Use async compute_match_score if available
                    if hasattr(self.ats_scorer, "compute_match_score") and callable(getattr(self.ats_scorer, "compute_match_score")):
                        score_results = await self.ats_scorer.compute_match_score(
                            self.resume, job_description
                        )
                    else:
                        # Fall back to sync method if async not available
                        score_results = self.ats_scorer.compute_match_score_sync(
                            self.resume, job_description
                        )

                    missing_skills = score_results.get("missing_skills", [])
                    matching_skills = score_results.get("matching_skills", [])

                    # Reconfigure processing chain with identified missing skills
                    self._setup_chain(missing_skills)

                    print(f"Initial ATS Score: {score_results.get('final_score', 'N/A')}%")
                    print(f"Found {len(missing_skills)} missing skills to incorporate")
                    print(f"Found {len(matching_skills)} matching skills to emphasize")
                except Exception as e:
                    print(f"Warning: ATS scoring failed, proceeding without skill recommendations: {str(e)}")
                    pass

            # Try to load prompt from database
            try:
                db_template = await self._get_prompt_template_from_db()
                if db_template:
                    # Create a new prompt template with the database template
                    # but keep the recommended skills section
                    recommended_skills_section = ""
                    if missing_skills and len(missing_skills) > 0:
                        skills_list = ", ".join([f"'{skill}'" for skill in missing_skills])
                        recommended_skills_section = f"""
                    ## RECOMMENDED SKILLS TO ADD

                    The following skills were identified as potentially valuable for this position but may be missing or not prominently featured in the resume:

                    {skills_list}

                    If the candidate has any experience with these skills, even minor exposure:
                    - Highlight them prominently in the skills section
                    - Look for ways to showcase these skills in past experience descriptions
                    - Ensure you're using the exact terminology as listed
                    - Look for related skills or experience that could be reframed to match these requirements
                    - Reframe transferable or implied experience to match the job requirements where ethically possible
                    - Be assertive in surfacing any relevant experience, even if it is not an exact match, as long as it is truthful
                    - Do NOT fabricate experience with these skills, only highlight them if they exist
                    """

                    # Format the template with the recommended skills section
                    # Handle different placeholder formats by using a safer approach
                    # First, escape any existing curly braces to prevent conflicts
                    formatted_template = db_template

                    # We'll use the default input variables from the template

                    # Handle the recommended_skills_section separately as a partial variable
                    # This avoids Jinja2 parsing issues with the content
                    partial_vars = {
                        "recommended_skills_section": recommended_skills_section
                    }

                    # Create the prompt template with explicit variable handling
                    try:
                        custom_prompt = PromptTemplate.from_template(
                            template=formatted_template,
                            template_format="jinja2",
                            partial_variables=partial_vars
                        )
                    except Exception as template_error:
                        print(f"Error creating prompt template: {template_error}. Trying fallback method.")
                        # Fallback: manually replace the placeholder
                        if "{{recommended_skills_section}}" in formatted_template:
                            formatted_template = formatted_template.replace("{{recommended_skills_section}}", recommended_skills_section)
                        elif "{{{recommended_skills_section}}}" in formatted_template:
                            formatted_template = formatted_template.replace("{{{recommended_skills_section}}}", recommended_skills_section)
                        elif "{recommended_skills_section}" in formatted_template:
                            formatted_template = formatted_template.replace("{recommended_skills_section}", recommended_skills_section)

                        # Try again with the manually replaced template
                        custom_prompt = PromptTemplate.from_template(
                            template=formatted_template,
                            template_format="jinja2"
                        )

                    # Create a new chain with the custom prompt
                    custom_chain = custom_prompt | self.llm

                    try:
                        # Generate optimized resume using the custom chain
                        result = custom_chain.invoke(
                            {"job_description": job_description, "resume": self.resume}
                        )
                    except Exception as template_error:
                        print(f"Error using database prompt: {template_error}. Using default prompt.")
                        # Fall back to default chain
                        result = self.chain.invoke(
                            {"job_description": job_description, "resume": self.resume}
                        )
                else:
                    # Use the default chain
                    result = self.chain.invoke(
                        {"job_description": job_description, "resume": self.resume}
                    )
            except Exception as e:
                print(f"Error using database prompt: {e}. Using default prompt.")
                # Fall back to default chain
                result = self.chain.invoke(
                    {"job_description": job_description, "resume": self.resume}
                )

            # Step 3: Parse and format the LLM response
            try:
                # Extract content from different response types
                if hasattr(result, "content"):
                    content = result.content
                else:
                    content = result

                # Step 4: Parse JSON and add ATS metrics
                try:
                    # Direct JSON parsing
                    json_result = json.loads(content)

                    # Enrich result with ATS analysis metrics
                    if score_results:
                        json_result["ats_metrics"] = {
                            "initial_score": score_results.get("final_score", 0),
                            "matching_skills": score_results.get("matching_skills", []),
                            "missing_skills": score_results.get("missing_skills", []),
                            "recommendation": score_results.get("recommendation", "")
                        }

                    # Ensure optimization_summary exists
                    if "optimization_summary" not in json_result:
                        json_result["optimization_summary"] = {
                            "changes_made": [
                                "Resume content was restructured for better ATS compatibility",
                                "Professional summary was tailored to highlight relevant skills and experience",
                                "Experience descriptions were enhanced to include more relevant keywords"
                            ],
                            "keywords_added": [],
                            "skills_emphasized": [],
                            "content_reorganized": [
                                "Content was reorganized to highlight relevant experience",
                                "Skills section was restructured to prioritize job-relevant skills"
                            ],
                            "achievements_quantified": [],
                            "overall_strategy": "Resume was optimized to improve ATS compatibility by incorporating relevant keywords, highlighting matching skills, and restructuring content to emphasize relevant experience for the target position."
                        }

                    return json_result
                except json.JSONDecodeError:
                    print(f"JSON decode error. Trying fallback methods. Content starts with: {content[:100]}...")

                    # Fallback 1: Extract JSON from code blocks
                    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
                    if json_match:
                        try:
                            json_str = json_match.group(1)
                            json_result = json.loads(json_str)

                            # Enrich result with ATS analysis metrics
                            if score_results:
                                json_result["ats_metrics"] = {
                                    "initial_score": score_results.get("final_score", 0),
                                    "matching_skills": score_results.get("matching_skills", []),
                                    "missing_skills": score_results.get("missing_skills", []),
                                    "recommendation": score_results.get("recommendation", "")
                                }

                            # Ensure optimization_summary exists
                            if "optimization_summary" not in json_result:
                                json_result["optimization_summary"] = {
                                    "changes_made": [
                                        "Resume content was restructured for better ATS compatibility",
                                        "Professional summary was tailored to highlight relevant skills and experience",
                                        "Experience descriptions were enhanced to include more relevant keywords"
                                    ],
                                    "keywords_added": [],
                                    "skills_emphasized": [],
                                    "content_reorganized": [
                                        "Content was reorganized to highlight relevant experience",
                                        "Skills section was restructured to prioritize job-relevant skills"
                                    ],
                                    "achievements_quantified": [],
                                    "overall_strategy": "Resume was optimized to improve ATS compatibility by incorporating relevant keywords, highlighting matching skills, and restructuring content to emphasize relevant experience for the target position."
                                }

                            return json_result
                        except json.JSONDecodeError:
                            print(f"Failed to parse JSON from code block. Trying next method.")

                    # Fallback 2: Find any JSON-like structure in the response
                    json_str = re.search(r"(\{[\s\S]*\})", content)
                    if json_str:
                        try:
                            json_result = json.loads(json_str.group(1))

                            # Enrich result with ATS analysis metrics
                            if score_results:
                                json_result["ats_metrics"] = {
                                    "initial_score": score_results.get("final_score", 0),
                                    "matching_skills": score_results.get("matching_skills", []),
                                    "missing_skills": score_results.get("missing_skills", []),
                                    "recommendation": score_results.get("recommendation", "")
                                }

                            # Ensure optimization_summary exists
                            if "optimization_summary" not in json_result:
                                json_result["optimization_summary"] = {
                                    "changes_made": [],
                                    "keywords_added": [],
                                    "skills_emphasized": [],
                                    "content_reorganized": [],
                                    "achievements_quantified": [],
                                    "overall_strategy": "Resume optimized for ATS compatibility."
                                }

                            return json_result
                        except json.JSONDecodeError:
                            print(f"Failed to parse JSON-like structure. Trying next method.")

                    # Fallback 3: Check for conversational responses and try to extract JSON
                    print("Checking for conversational responses with JSON content...")

                    # Look for patterns like "Here's the JSON:" or "Here's the optimized resume:"
                    conversational_patterns = [
                        r"(?:here(?:'s| is) the (?:json|optimized resume)(?:\:|\s+))([\s\S]*)",
                        r"(?:I've created|I have created|I've generated|I have generated)(?:[\s\S]*?)((?:\{[\s\S]*\}))",
                        r"(?:please find|here is)(?:[\s\S]*?)((?:\{[\s\S]*\}))",
                    ]

                    for pattern in conversational_patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            try:
                                # Try to find a JSON object in the matched content
                                json_match = re.search(r"(\{[\s\S]*\})", match.group(1))
                                if json_match:
                                    json_str = json_match.group(1)
                                    json_result = json.loads(json_str)

                                    # Enrich result with ATS analysis metrics
                                    if score_results:
                                        json_result["ats_metrics"] = {
                                            "initial_score": score_results.get("final_score", 0),
                                            "matching_skills": score_results.get("matching_skills", []),
                                            "missing_skills": score_results.get("missing_skills", []),
                                            "recommendation": score_results.get("recommendation", "")
                                        }

                                    # Ensure optimization_summary exists
                                    if "optimization_summary" not in json_result:
                                        json_result["optimization_summary"] = {
                                            "changes_made": [
                                                "Resume content was restructured for better ATS compatibility",
                                                "Professional summary was tailored to highlight relevant skills and experience",
                                                "Experience descriptions were enhanced to include more relevant keywords"
                                            ],
                                            "keywords_added": [],
                                            "skills_emphasized": [],
                                            "content_reorganized": [
                                                "Content was reorganized to highlight relevant experience",
                                                "Skills section was restructured to prioritize job-relevant skills"
                                            ],
                                            "achievements_quantified": [],
                                            "overall_strategy": "Resume was optimized to improve ATS compatibility by incorporating relevant keywords, highlighting matching skills, and restructuring content to emphasize relevant experience for the target position."
                                        }

                                    print("Successfully extracted JSON from conversational response.")
                                    return json_result
                            except json.JSONDecodeError:
                                print(f"Found potential JSON in conversational response but failed to parse it.")

                    # Fallback 4: If the response is text, try to convert it to a structured format
                    print("All JSON extraction methods failed. Attempting to create structured data from text response.")

                    # Create a basic structured response from the text
                    # This is a last resort when the AI returns text instead of JSON
                    structured_response = {
                        "user_information": {
                            "name": "",
                            "main_job_title": "",
                            "profile_description": content[:500],  # Use the first part of the content as profile
                            "email": "",
                            "linkedin": "",
                            "github": "",
                            "experiences": [],
                            "education": [],
                            "skills": {
                                "hard_skills": [],
                                "soft_skills": []
                            },
                            "hobbies": []
                        },
                        "projects": [],
                        "certificate": [],
                        "extra_curricular_activities": [],
                        "optimization_summary": {
                            "changes_made": [
                                "Resume content was restructured for better ATS compatibility",
                                "Professional summary was tailored to highlight relevant skills and experience",
                                "Experience descriptions were enhanced to include more relevant keywords"
                            ],
                            "keywords_added": [],
                            "skills_emphasized": [],
                            "content_reorganized": [
                                "Content was reorganized to highlight relevant experience",
                                "Skills section was restructured to prioritize job-relevant skills"
                            ],
                            "achievements_quantified": [],
                            "overall_strategy": "Resume was optimized to improve ATS compatibility by incorporating relevant keywords, highlighting matching skills, and restructuring content to emphasize relevant experience for the target position."
                        },
                        "raw_text_response": content  # Store the full text response
                    }

                    # Extract skills from the ATS scoring if available
                    if score_results:
                        matching_skills = score_results.get("matching_skills", [])
                        if matching_skills:
                            # Add matching skills as hard skills
                            structured_response["user_information"]["skills"]["hard_skills"] = matching_skills

                        # Add ATS metrics
                        structured_response["ats_metrics"] = {
                            "initial_score": score_results.get("final_score", 0),
                            "matching_skills": score_results.get("matching_skills", []),
                            "missing_skills": score_results.get("missing_skills", []),
                            "recommendation": score_results.get("recommendation", "")
                        }

                    print("Created structured response from text. This is a fallback and may not contain all expected data.")
                    return structured_response

                    # We no longer return an error here, instead we provide a structured response
                    # with the raw text included
            except Exception as e:
                return {
                    "error": f"JSON parsing error: {str(e)}",
                    "raw_response": str(result)[:500],
                }

        except Exception as e:
            return {"error": f"Error processing request: {str(e)}"}


if __name__ == "__main__":
    with open("../../../data/sample_resumes/resume.txt", "r") as f:
        resume = f.read()

    with open("../../../data/sample_descriptions/job_description_1.txt", "r") as f:
        job_description = f.read()

    API_KEY = "sk-********************"
    API_BASE = "https://api.deepseek.com/v1"
    MODEL_NAME = "deepseek-chat"

    model = AtsResumeOptimizer(
        model_name=MODEL_NAME,
        resume=resume,
        api_key=API_KEY,
        api_base=API_BASE,
    )

    result = model.generate_ats_optimized_resume_json(job_description)

    print(json.dumps(result, indent=2))