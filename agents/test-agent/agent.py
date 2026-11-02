import os

from agents import Agent, Runner

from instructions import TEST_AGENT_INSTRUCTIONS


def create_test_agent():

    return Agent(
        name="InfraGuardian Test Agent",

        instructions=TEST_AGENT_INSTRUCTIONS,

        model=os.environ.get(
            "MODEL_DEPLOYMENT_NAME",
            "gpt-4.1-mini"
        ),

        tools=[]
    )


async def run_test(
    application_url: str,
    instructions: str
):

    agent = create_test_agent()

    prompt = f"""
Testing target:

{application_url}

Testing objective:

{instructions}

Begin by understanding the application and
the requested testing objective.

Execute the appropriate tests and provide
a final test report.
"""

    result = await Runner.run(
        agent,
        prompt
    )

    return result.final_output