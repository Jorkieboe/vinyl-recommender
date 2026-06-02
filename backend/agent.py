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
        self.max_steps = 50
        self.llm = LLMAdvisor()

    def _initialize_agent(self):
        base_prompt = """
        You are a vinyl recommender agent. You work autonomous and does not expect new users reply
        Your goal is to find a music album that fits the user's taste.

        Use the `get_artist_knowledge` tool first whenever a user mentions an artist they already know, like, or dislike, or when you are deciding whether to explore an artist. This helps avoid redundant exploration of artists they already have fully synced or evaluated.

        You need to pick between exploration and exploitation:
        - Exploration: Make a pivot and switch to another liked genre or try to explore other paths that do not seem to fit at first.
        - Exploitation: Go deeper and explore more of the same artist or try related artists.

        You can use different tools to explore artists and albums, inspect system knowledge of an artist, and calculate sonic similarity between artists and the user's taste.
        Be concise and analytical.

        To reach the goal the following criteria must be met:
        - Never recommend below 60% similarity.
        - If the similarity is on the lower side like 70%, try to look for a better option before committing to this one.
        - If you see not much improvement after exploring more options, pick the highest rated.

        If none of the criteria have been met but the last step is reached, recommend the best one yet.
        If the goal is satisfied return finish.
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
            logger.result(content)

            if "finish" in content.lower() or step == self.max_steps:
                logger.result("Agent optimization complete. Finalizing recommendation...")

                # 1. Ask the LLM for the structured final choice based on the history
                final_decision = await self.llm.final_decision(self.messageHistory)

                # 2. Extract the ID from the structured result
                if isinstance(final_decision, dict) and final_decision.get('album_id'):
                    target_album_id = int(final_decision['album_id'])

                    # 3. Run the final semantic/scraping logic (Awaited)
                    score, insight = await self.bridge._run_album_semantical_analysis_logic(None, target_album_id)

                    return {"status": "success", "message": insight}

                # Fallback if no structured ID was found
                return {"message": content}

        return {"message": "Agent reached maximum execution steps."}