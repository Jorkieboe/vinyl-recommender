from backend.llm_advisor import LLMAdvisor

class Agentloop:
    def __init__(self, config):
        self.messageHistory = []
        self._initialize_agent()
        self.max_steps = 5
        self.llm = LLMAdvisor()

    def _initialize_agent(self):
        base_prompt = """
        You are a research agent in a controlled laboratory environment.
        Your goal is to complete the user's task using the provided tools.
        Be concise and analytical.

        COMPLETION PROTOCOL:
        - When the task is complete, you MUST call the 'finish' tool.
        - NEVER simply write the final answer as text. If you do not call 'finish', the loop will continue.
        """

        self.messageHistory.append({"role": "system", "content": base_prompt})

    async def run(self, user_input):

        self.messageHistory.append({"role": "user", "content": user_input})
        first_response = await self.llm(self.messageHistory)
        self.messageHistory.append({"role": "assistant", "content": first_response})

        step = 0
        while step < self.max_steps:
            step += 1
            response = await self.llm(self.messageHistory)
            self.messageHistory.append({"role": "assistant", "content": first_response})
