"""Test script for the prompts API.

This script tests the functionality of the prompts API, including:
- Initializing default prompts
- Retrieving prompts
- Updating prompts
"""

import asyncio
import json
import os
import sys

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.repositories.prompt_repository import PromptRepository


async def test_initialize_default_prompts():
    """Test initializing default prompts."""
    print("Testing initialize_default_prompts...")
    repo = PromptRepository()
    
    # Clear existing prompts for testing
    prompts = await repo.get_all_prompts(include_inactive=True)
    for prompt in prompts:
        await repo.delete_prompt(prompt["id"])
    
    # Initialize default prompts
    await repo.initialize_default_prompts()
    
    # Verify prompts were created
    prompts = await repo.get_all_prompts()
    print(f"Found {len(prompts)} prompts after initialization")
    
    # Print prompt names
    for prompt in prompts:
        print(f"- {prompt['name']}: {prompt['description'][:50]}...")
    
    return len(prompts) > 0


async def test_get_prompts_by_component():
    """Test getting prompts by component."""
    print("\nTesting get_prompts_by_component...")
    repo = PromptRepository()
    
    # Get prompts by component
    ats_prompts = await repo.get_prompts_by_component("ats_scoring")
    print(f"Found {len(ats_prompts)} ATS scoring prompts")
    
    optimization_prompts = await repo.get_prompts_by_component("resume_optimization")
    print(f"Found {len(optimization_prompts)} resume optimization prompts")
    
    return len(ats_prompts) > 0 and len(optimization_prompts) > 0


async def test_update_prompt():
    """Test updating a prompt."""
    print("\nTesting update_prompt...")
    repo = PromptRepository()
    
    # Get a prompt to update
    prompts = await repo.get_all_prompts()
    if not prompts:
        print("No prompts found to update")
        return False
    
    prompt = prompts[0]
    prompt_id = prompt["id"]
    original_description = prompt["description"]
    
    # Update the prompt
    new_description = f"{original_description} (Updated)"
    from app.database.models.prompt import PromptUpdate
    update_data = PromptUpdate(description=new_description)
    
    success = await repo.update_prompt(prompt_id, update_data)
    print(f"Update result: {success}")
    
    # Verify the update
    updated_prompt = await repo.get_prompt_by_id(prompt_id)
    print(f"Original description: {original_description}")
    print(f"Updated description: {updated_prompt['description']}")
    
    # Restore the original description
    restore_data = PromptUpdate(description=original_description)
    await repo.update_prompt(prompt_id, restore_data)
    
    return updated_prompt["description"] == new_description


async def main():
    """Run all tests."""
    print("=== Testing Prompts API ===")
    
    # Run tests
    init_result = await test_initialize_default_prompts()
    component_result = await test_get_prompts_by_component()
    update_result = await test_update_prompt()
    
    # Print results
    print("\n=== Test Results ===")
    print(f"Initialize default prompts: {'PASS' if init_result else 'FAIL'}")
    print(f"Get prompts by component: {'PASS' if component_result else 'FAIL'}")
    print(f"Update prompt: {'PASS' if update_result else 'FAIL'}")
    
    all_passed = init_result and component_result and update_result
    print(f"\nOverall result: {'PASS' if all_passed else 'FAIL'}")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
