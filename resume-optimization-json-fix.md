# Resume Optimization JSON Extraction Fix

## Problem Description

During resume optimization, the application was encountering a 500 Internal Server Error with the following error message:

```
2025-05-15 15:38:32,351 - app.api.routers.resume - ERROR - AI service returned an error: Could not extract valid JSON from response: Certainly! Please provide the specific job description and the current resume you'd like me to optim...
```

The issue was that the AI service (DeepSeek-V3-0324) was returning a conversational text response instead of a valid JSON object as required by the application. The JSON extraction logic in the `AtsResumeOptimizer.generate_ats_optimized_resume_json()` method was failing to parse this response.

## Root Cause

1. The AI model was responding in a conversational format instead of following the instructions to return a JSON object
2. The JSON extraction logic wasn't robust enough to handle non-JSON or conversational responses
3. The error handling in the resume optimization endpoint didn't provide clear feedback about JSON extraction issues

## Solution

The fix involved three main changes:

### 1. Enhanced JSON Extraction Logic

We improved the JSON extraction logic in `app/services/ai/model_ai.py` to better handle conversational responses. A new fallback method was added that specifically looks for patterns like "Here's the JSON:" or "I've created..." in the AI response and attempts to extract JSON from these conversational formats.

```python
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
                
                print("Successfully extracted JSON from conversational response.")
                return json_result
        except json.JSONDecodeError:
            print(f"Found potential JSON in conversational response but failed to parse it.")
```

### 2. Improved Prompt Template

We enhanced the prompt template to more explicitly instruct the model to return only JSON. The updated template includes warning symbols and clearer instructions to prevent the model from adding conversational text:

```
⚠️ CRITICAL INSTRUCTION ⚠️

YOU MUST RETURN ONLY A VALID JSON OBJECT WITH ABSOLUTELY NO OTHER TEXT.

DO NOT:
- Add any introduction like "Here's the JSON" or "Here's the optimized resume"
- Add any explanation or commentary before or after the JSON
- Wrap the JSON in markdown code blocks (```json)
- Add any notes, tips, or additional information

YOUR ENTIRE RESPONSE MUST BE PARSEABLE BY json.loads() IN PYTHON.

...

⚠️ FINAL REMINDER: YOUR ENTIRE RESPONSE MUST BE ONLY THE JSON OBJECT ⚠️
```

### 3. Better Error Handling

We improved the error handling in the resume optimization endpoint to provide clearer feedback when JSON extraction fails:

```python
elif "json" in str(e).lower() or "extract" in str(e).lower() or "parse" in str(e).lower():
    logger.error("JSON extraction error from AI response")
    
    # Try to extract the first part of the response for debugging
    error_msg = str(e)
    response_preview = ""
    if "Could not extract valid JSON from response:" in error_msg:
        response_preview = error_msg.split("Could not extract valid JSON from response:", 1)[1].strip()[:100]
        if response_preview:
            response_preview = f" Response starts with: '{response_preview}...'"
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"The AI service returned a response that could not be processed as JSON. Please try again with a lower temperature setting (0.0 recommended).{response_preview}",
    )
```

## Testing

The changes should be tested by:

1. Attempting to optimize a resume with different temperature settings (0.0, 0.5, 1.0)
2. Verifying that the application can handle both properly formatted JSON responses and conversational responses
3. Checking that appropriate error messages are displayed when JSON extraction fails

## Future Improvements

1. Consider implementing a retry mechanism that automatically retries with a lower temperature if JSON extraction fails
2. Add more robust validation of the extracted JSON to ensure it meets the expected schema
3. Implement a fallback mechanism that uses a different model or prompt if the primary model consistently fails to return valid JSON
