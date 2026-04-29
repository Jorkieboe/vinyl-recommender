import json
from backend.llm_advisor import LLMAdvisor
from backend.tools import ToolRegistry, MusicAgentTools
from backend.utils.logger import logger

class Agentloop:
    def __init__(self, bridge):
        self.bridge = bridge
        self.registry = ToolRegistry()

        self.music_tools = MusicAgentTools(bridge)
        self.registry.register_instance_tools(self.music_tools)

        self.messageHistory = []
        self._initialize_agent()
        self.max_steps = 10
        self.llm = LLMAdvisor()

    def _initialize_agent(self):
        base_prompt = """
        You are a vinyl recommender agent.
        Your goal is to find an music album that fit the user taste.
        Your can use different tools to explora artist and albums and calculate sonic simularity between artists and the users taste.
        Be concise and analytical.

        if the goal is satisfied return finish

        """

        self.messageHistory.append({"role": "system", "content": base_prompt})

    async def run(self, user_input):
        """Processes user input through the agent loop with tool execution"""
        self.messageHistory.append({"role": "user", "content": user_input})

        step = 0
        tools_schema = self.registry.get_all_schemas()

        while step < self.max_steps:
            step += 1
            logger.ai(f"Agent Step {step}/{self.max_steps}...")

            response_message = await self.llm.agent_call(self.messageHistory, tools_schema=tools_schema)

            logger.ai(response_message)
            if not response_message:
                return {"message": "The AI failed to generate a response."}

            # Add the assistant's message to history (required for OpenAI-style tool flows)
            self.messageHistory.append(response_message)

            # Check for Tool Calls 
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)

                    logger.ai(f"Executing Tool: {func_name}({func_args})")

                    if func_name in self.registry.tools:
                        result = await self.registry.tools[func_name].execute(**func_args)

                        # Add tool result to history
                        self.messageHistory.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": str(result)
                        })
                    else:
                        logger.error(f"Tool {func_name} not found in registry.")

                # Continue loop to let model see tool results
                continue

            # If there are no tool calls, it's a final response
            content = response_message.content or ""

            if "finish" in content.lower() or step == self.max_steps:
                # Clean up the "finish" keyword for UI presentation if desired
                display_msg = content.replace("finish", "").replace("FINISH", "").strip()
                return {"message": display_msg or "Task completed."}

            return {"message": content}

        return {"message": "Agent reached maximum execution steps."}