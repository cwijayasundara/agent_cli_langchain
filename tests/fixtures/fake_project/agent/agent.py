class _FakeAgent:
    def invoke(self, payload):
        msg = payload["messages"][-1]["content"]
        return {"messages": [{"role": "assistant", "content": f"echo: {msg}"}]}


agent = _FakeAgent()
