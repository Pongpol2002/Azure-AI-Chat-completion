import os
import asyncio
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import ListSortOrder
from dotenv import load_dotenv

load_dotenv()

class AzureConfig:
    """Configuration class to manage multiple Azure OpenAI endpoints and models"""
    
    def __init__(self, config_name: str):
        self.config_name = config_name
        self.project_endpoint = os.getenv(f"PROJECT_ENDPOINT_{config_name}")
        self.chat_model = os.getenv(f"CHAT_MODEL_{config_name}")
        self.agent_model = os.getenv(f"AGENT_ID_{config_name}")
        self.connection_name = os.getenv(f"CONNECTION_NAME_{config_name}")
        self.api_version = os.getenv(f"API_VERSION_{config_name}", "2024-12-01-preview")
        
        # Validate required settings
        if not self.project_endpoint:
            raise ValueError(f"PROJECT_ENDPOINT_{config_name} not found in environment variables")
        if not self.chat_model:
            raise ValueError(f"CHAT_MODEL_{config_name} not found in environment variables")
    
    def __str__(self):
        return f"Config: {self.config_name}, Endpoint: {self.project_endpoint}, Model: {self.chat_model}"

async def test_chat_completion(config: AzureConfig, project_client):
    """Test chat completion with the given configuration"""
    print(f"\n=== Testing Chat Completion with {config.config_name} ===")
    print(f"Using model: {config.chat_model}")
    print(f"Using endpoint: {config.project_endpoint}")
    
    try:
        async with await project_client.get_openai_client(api_version=config.api_version) as client:
            response = await client.chat.completions.create(
                model=config.chat_model,
                messages=[
                    {
                        "role": "user",
                        "content": input("Ask me anything..."),
                    },
                ],
            )
            print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Error with {config.config_name}: {e}")

async def upload_dataset(config: AzureConfig, dataset_name: str, dataset_version: str, file_path: str, project_client):
    """Upload dataset with the given configuration"""
    print(f"\n=== Uploading Dataset with {config.config_name} ===")
    
    if not config.connection_name:
        print(f"No connection name configured for {config.config_name}, skipping dataset upload")
        return
    
    try:
        dataset = await project_client.datasets.upload_file(
            name=dataset_name,
            version=dataset_version,
            file_path=file_path,
            connection_name=config.connection_name,
        )
        print(f"Dataset uploaded successfully: {dataset}")
    except Exception as e:
        print(f"Error uploading dataset with {config.config_name}: {e}")

async def upload_file_to_index(config: AzureConfig, file_path: str):
    return

async def agent_chat_completion(config: AzureConfig, project):
    print(f"\n=== Testing Chat Completion with {config.config_name} ===")
    print(f"Using model: {config.chat_model}")
    print(f"Using endpoint: {config.project_endpoint}")

    # Add await for async get_agent call
    agent = await project.agents.get_agent(config.agent_model)

    # Add await for async thread creation
    thread = await project.agents.threads.create()
    print(f"Created thread, ID: {thread.id}")

    # Add await for async message creation
    message = await project.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=input("Ask me something...")
    )

    # Add await for async run creation and processing
    run = await project.agents.runs.create_and_process(
        thread_id=thread.id,
        agent_id=agent.id
    )

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")
    else:
        # Get all messages as a list (use sparingly)
            messages = [message async for message in project.agents.messages.list(
                thread_id=thread.id, 
                order=ListSortOrder.ASCENDING
            )]

            # Then iterate normally
            for message in messages:
                if message.text_messages:
                    print(f"{message.role}: {message.text_messages[-1].text.value}")

    await project.close()

async def get_conversation_history(project_client, thread_id):
    """Get all messages from a conversation thread"""
    messages = []
    async for message in project_client.agents.messages.list(
        thread_id=thread_id,
        order=ListSortOrder.ASCENDING
    ):
        if message.text_messages:
            messages.append({
                'role': message.role,
                'content': message.text_messages[-1].text.value,
                'timestamp': message.created_at
            })
    return messages

async def main():
    # ==============================================
    # CONFIGURATION SELECTION - CHANGE THIS PART
    # ==============================================
    
    # Select which configuration to use
    SELECTED_CONFIG = "TEST"  
    
    # Avaiable config (Project_endpoint for DEV still missing -> authorization)
    CONFIGS_TO_TEST = ["TEST", "DEV"]  
    
    # Dataset settings
    DATASET_NAME = "Test_dataset_1"
    DATASET_VERSION = "1.0.0"
    FILE_PATH = "Northwind_Health_Plus_Benefits_Details.pdf"
    
    # ==============================================
    
    print("Available configurations:")

    configs = {}
    for config_name in CONFIGS_TO_TEST:
        try:
            config = AzureConfig(config_name)
            configs[config_name] = config
            print(f"✓ {config}")
        except ValueError as e:
            print(f"✗ {config_name}: {e}")
    
    # Test the selected configuration
    if SELECTED_CONFIG in configs:
        selected_config = configs[SELECTED_CONFIG]

        project_client = AIProjectClient(
            credential=DefaultAzureCredential(),
            endpoint=selected_config.project_endpoint,
        )
        
        # # Test chat completion
        # await test_chat_completion(selected_config, project_client)
        
        # # Test agent chat completion
        # await agent_chat_completion(selected_config, project_client)

        # # Upload file to a dataset
        # await upload_dataset(selected_config, DATASET_NAME, DATASET_VERSION, FILE_PATH, project_client)

        print(await get_conversation_history(project_client, thread_id="thread_AqpDn0CQu9gw49CJRgRkZlmI"))
    else:
        print(f"Selected configuration '{SELECTED_CONFIG}' is not available")
    
    # Optionally test all configurations
    # print(f"\n=== Testing All Configurations ===")
    # for config_name, config in configs.items():
    #     await test_chat_completion(config)

if __name__ == "__main__":
    asyncio.run(main())